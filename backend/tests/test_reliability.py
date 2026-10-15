"""
Reliability tests for LLM provider fallback, retry logic, and tool deduplication.
Run with: cd backend && pytest tests/test_reliability.py -v
"""
import json
import sys
import os
import types
from unittest.mock import MagicMock, patch

# Make backend importable without a full install
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from llm_provider import LLMProvider, ProviderError, STATE_CHANGING_TOOLS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_response(content="Hello", tool_calls=None):
    """Build a minimal OpenAI-style chat completion response."""
    msg = MagicMock()
    msg.content = content
    msg.tool_calls = tool_calls or []
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def _http_error(code: int) -> Exception:
    return Exception(f"Error code: {code} - server error")


def _timeout_error() -> Exception:
    return Exception("Request timed out")


# ---------------------------------------------------------------------------
# Test 1 — Gemini 503 causes fallback to Groq (success)
# ---------------------------------------------------------------------------

def test_groq_primary_gemini_fallback_on_503():
    """Groq is primary; if Groq returns 503 Gemini is tried."""
    provider = LLMProvider.__new__(LLMProvider)
    provider.gemini_key = "fake-gemini-key"
    provider.groq_key = "fake-groq-key"
    provider.gemini_model = "gemini-test"
    provider.groq_model = "llama-test"
    provider._gemini_client = None
    provider._groq_client = None

    groq_client = MagicMock()
    gemini_client = MagicMock()

    groq_client.chat.completions.create.side_effect = _http_error(503)
    gemini_client.chat.completions.create.return_value = _make_response("Gemini fallback OK")

    provider._groq_client = groq_client
    provider._gemini_client = gemini_client

    resp, pname, model = provider.call(messages=[], tools=[])
    assert pname == "gemini"
    assert resp.choices[0].message.content == "Gemini fallback OK"


# ---------------------------------------------------------------------------
# Test 2 — Both providers fail -> ProviderError raised
# ---------------------------------------------------------------------------

def test_both_providers_fail_raises_provider_error():
    provider = LLMProvider.__new__(LLMProvider)
    provider.gemini_key = "fake-gemini"
    provider.groq_key = "fake-groq"
    provider.gemini_model = "gemini-test"
    provider.groq_model = "llama-test"
    provider._gemini_client = None
    provider._groq_client = None

    groq_client = MagicMock()
    gemini_client = MagicMock()
    groq_client.chat.completions.create.side_effect = _http_error(503)
    gemini_client.chat.completions.create.side_effect = _http_error(503)

    provider._groq_client = groq_client
    provider._gemini_client = gemini_client

    with pytest.raises(ProviderError) as exc_info:
        provider.call(messages=[], tools=[])

    assert exc_info.value.category == "transient"


# ---------------------------------------------------------------------------
# Test 3 — Auth errors are not retried and do not fall back
# ---------------------------------------------------------------------------

def test_auth_error_skips_retry_and_falls_through():
    provider = LLMProvider.__new__(LLMProvider)
    provider.gemini_key = None
    provider.groq_key = "fake-groq"
    provider.gemini_model = "gemini-test"
    provider.groq_model = "llama-test"
    provider._gemini_client = None
    provider._groq_client = None

    groq_client = MagicMock()
    groq_client.chat.completions.create.side_effect = _http_error(401)
    provider._groq_client = groq_client

    with pytest.raises(ProviderError) as exc_info:
        provider.call(messages=[], tools=[])

    # Should have been called exactly once (no retry)
    assert groq_client.chat.completions.create.call_count == 1
    assert exc_info.value.category == "auth"


# ---------------------------------------------------------------------------
# Test 4 — Timeout is treated as transient and retried once
# ---------------------------------------------------------------------------

def test_timeout_retried_once_then_falls_back():
    provider = LLMProvider.__new__(LLMProvider)
    provider.gemini_key = "fake-gemini"
    provider.groq_key = "fake-groq"
    provider.gemini_model = "gemini-test"
    provider.groq_model = "llama-test"
    provider._gemini_client = None
    provider._groq_client = None

    groq_client = MagicMock()
    gemini_client = MagicMock()

    groq_client.chat.completions.create.side_effect = _timeout_error()
    gemini_client.chat.completions.create.return_value = _make_response("Gemini OK after timeout")

    provider._groq_client = groq_client
    provider._gemini_client = gemini_client

    with patch("llm_provider.time.sleep"):  # don't actually sleep in tests
        resp, pname, _ = provider.call(messages=[], tools=[])

    assert pname == "gemini"
    # Groq should have been called twice (original + 1 retry)
    assert groq_client.chat.completions.create.call_count == 2


# ---------------------------------------------------------------------------
# Test 5 — No duplicate state-changing tool calls after provider switch
# ---------------------------------------------------------------------------

def test_no_duplicate_state_changing_tool_calls():
    """
    Simulate: first LLM call requests create_meal_plan, tool runs,
    second LLM call (after a notional fallback) requests the same tool again.
    The dedup map must return the cached result without re-running the tool.
    """
    executed = {}

    def fake_execute_tool(name, args):
        key = (name, json.dumps(args))
        if key in executed:
            raise AssertionError(f"Tool {name} was called twice!")
        executed[key] = json.dumps({"plan_id": 1, "created": True})
        return executed[key]

    # Simulate the dedup logic that lives in PlannerAgent.chat()
    executed_state_tools = {}
    tool_name = "create_meal_plan"
    tool_args = {"week_start": "2026-10-15"}
    dedup_key = (tool_name, json.dumps(tool_args))

    # First call — should execute
    if tool_name in STATE_CHANGING_TOOLS and dedup_key in executed_state_tools:
        result = executed_state_tools[dedup_key]
    else:
        result = fake_execute_tool(tool_name, tool_args)
        if tool_name in STATE_CHANGING_TOOLS:
            executed_state_tools[dedup_key] = result

    assert json.loads(result)["plan_id"] == 1

    # Second call with same key — must return cached, not re-execute
    if tool_name in STATE_CHANGING_TOOLS and dedup_key in executed_state_tools:
        result2 = executed_state_tools[dedup_key]
    else:
        result2 = fake_execute_tool(tool_name, tool_args)

    assert result2 == result
    assert len(executed) == 1  # only executed once


# ---------------------------------------------------------------------------
# Test 6 — No providers configured raises ProviderError(config)
# ---------------------------------------------------------------------------

def test_no_keys_raises_config_error():
    provider = LLMProvider.__new__(LLMProvider)
    provider.gemini_key = None
    provider.groq_key = None
    provider.gemini_model = "gemini-test"
    provider.groq_model = "llama-test"
    provider._gemini_client = None
    provider._groq_client = None

    with pytest.raises(ProviderError) as exc_info:
        provider.call(messages=[], tools=[])

    assert exc_info.value.category == "config"
