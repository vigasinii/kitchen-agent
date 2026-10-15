"""
Reliability tests for LLM provider fallback, retry logic, and tool deduplication.
Run with: cd backend && pytest tests/test_reliability.py -v
"""
import json
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from llm_provider import LLMProvider, ProviderError, STATE_CHANGING_TOOLS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_response(content="Hello", tool_calls=None):
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


def _make_provider(primary="model-a", secondary="model-b"):
    provider = LLMProvider.__new__(LLMProvider)
    provider.groq_key = "fake-groq-key"
    provider.primary_model = primary
    provider.secondary_model = secondary
    provider._groq_client = None
    return provider


# ---------------------------------------------------------------------------
# Test 1 — Primary model 503 causes fallback to secondary
# ---------------------------------------------------------------------------

def test_primary_503_falls_back_to_secondary():
    provider = _make_provider()
    groq_client = MagicMock()

    calls = {"n": 0}
    def side_effect(**kwargs):
        calls["n"] += 1
        model = kwargs.get("model")
        if model == "model-a":
            raise _http_error(503)
        return _make_response("secondary OK")

    groq_client.chat.completions.create.side_effect = side_effect
    provider._groq_client = groq_client

    with patch("llm_provider.time.sleep"):
        resp, pname, model = provider.call(messages=[], tools=[])

    assert pname == "groq"
    assert model == "model-b"
    assert resp.choices[0].message.content == "secondary OK"


# ---------------------------------------------------------------------------
# Test 2 — Both models fail -> ProviderError raised
# ---------------------------------------------------------------------------

def test_both_models_fail_raises_provider_error():
    provider = _make_provider()
    groq_client = MagicMock()
    groq_client.chat.completions.create.side_effect = _http_error(503)
    provider._groq_client = groq_client

    with patch("llm_provider.time.sleep"):
        with pytest.raises(ProviderError) as exc_info:
            provider.call(messages=[], tools=[])

    assert exc_info.value.category == "transient"


# ---------------------------------------------------------------------------
# Test 3 — Auth error raises immediately, no retry
# ---------------------------------------------------------------------------

def test_auth_error_raises_immediately():
    provider = _make_provider()
    groq_client = MagicMock()
    groq_client.chat.completions.create.side_effect = _http_error(401)
    provider._groq_client = groq_client

    with pytest.raises(ProviderError) as exc_info:
        provider.call(messages=[], tools=[])

    assert groq_client.chat.completions.create.call_count == 1
    assert exc_info.value.category == "auth"


# ---------------------------------------------------------------------------
# Test 4 — Timeout retried once on primary, then secondary succeeds
# ---------------------------------------------------------------------------

def test_timeout_retried_once_then_secondary():
    provider = _make_provider()
    groq_client = MagicMock()

    primary_calls = {"n": 0}
    def side_effect(**kwargs):
        model = kwargs.get("model")
        if model == "model-a":
            primary_calls["n"] += 1
            raise _timeout_error()
        return _make_response("secondary OK after timeout")

    groq_client.chat.completions.create.side_effect = side_effect
    provider._groq_client = groq_client

    with patch("llm_provider.time.sleep"):
        resp, pname, model = provider.call(messages=[], tools=[])

    assert model == "model-b"
    assert primary_calls["n"] == 2  # tried twice (original + 1 retry)


# ---------------------------------------------------------------------------
# Test 5 — 404 skips to secondary without retry
# ---------------------------------------------------------------------------

def test_not_found_skips_to_secondary_without_retry():
    provider = _make_provider()
    groq_client = MagicMock()

    primary_calls = {"n": 0}
    def side_effect(**kwargs):
        model = kwargs.get("model")
        if model == "model-a":
            primary_calls["n"] += 1
            raise _http_error(404)
        return _make_response("secondary OK")

    groq_client.chat.completions.create.side_effect = side_effect
    provider._groq_client = groq_client

    resp, pname, model = provider.call(messages=[], tools=[])

    assert model == "model-b"
    assert primary_calls["n"] == 1  # no retry on 404


# ---------------------------------------------------------------------------
# Test 6 — No duplicate state-changing tool calls
# ---------------------------------------------------------------------------

def test_no_duplicate_state_changing_tool_calls():
    executed = {}

    def fake_execute_tool(name, args):
        key = (name, json.dumps(args))
        if key in executed:
            raise AssertionError(f"Tool {name} was called twice!")
        executed[key] = json.dumps({"plan_id": 1, "created": True})
        return executed[key]

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
    assert len(executed) == 1


# ---------------------------------------------------------------------------
# Test 7 — No key configured raises ProviderError(config)
# ---------------------------------------------------------------------------

def test_no_key_raises_config_error():
    provider = _make_provider()
    provider.groq_key = None
    provider._groq_client = None

    with pytest.raises(ProviderError) as exc_info:
        provider.call(messages=[], tools=[])

    assert exc_info.value.category == "config"
