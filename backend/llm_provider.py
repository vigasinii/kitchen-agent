"""
Shared LLM provider: Groq-primary with model fallback.
Handles retry logic, error categorisation, structured latency logging,
and overall deadline enforcement. Never logs API keys or conversation text.
"""
import os
import random
import re
import time
from typing import Any, Dict, List, Optional, Tuple

_DEFAULT_GROQ_MODEL_PRIMARY = "openai/gpt-oss-120b"
_DEFAULT_GROQ_MODEL_SECONDARY = "openai/gpt-oss-20b"

GROQ_TIMEOUT = int(os.getenv("GROQ_TIMEOUT", "20"))
OVERALL_DEADLINE = int(os.getenv("OVERALL_DEADLINE", "26"))  # under Render's 30s free-tier limit

_TRANSIENT_CODES = {429, 502, 503, 504}
_AUTH_CODES = {401, 403}
_INVALID_CODES = {400, 422}
_NOT_FOUND_CODES = {404}

# Tools that write to the database; must not be re-executed after success
STATE_CHANGING_TOOLS = frozenset({
    "create_meal_plan",
    "update_meal_plan",
    "update_cook_session",
    "complete_session",
    "flag_household_approval_needed",
    "report_missing_ingredient",
})


class ProviderError(RuntimeError):
    """Raised when all configured providers have failed."""

    def __init__(self, message: str, category: str):
        super().__init__(message)
        # category: transient | auth | invalid | not_found | permanent | config
        self.category = category


def _error_category(e: Exception) -> str:
    s = str(e)
    name = type(e).__name__
    if any(str(c) in s for c in _AUTH_CODES):
        return "auth"
    if any(str(c) in s for c in _NOT_FOUND_CODES):
        return "not_found"
    if any(str(c) in s for c in _INVALID_CODES):
        return "invalid"
    if any(str(c) in s for c in _TRANSIENT_CODES):
        return "transient"
    if "timeout" in s.lower() or "timed out" in s.lower() or "Timeout" in name:
        return "transient"
    return "permanent"


def _retry_delay(e: Exception) -> float:
    """Return a delay in seconds, honouring Retry-After when present."""
    m = re.search(r"retry.after[\"\\s:]+(\d+)", str(e), re.IGNORECASE)
    base = float(m.group(1)) if m else (0.4 + random.random() * 0.6)
    return min(base, 10.0)


def _log_call(
    provider: str,
    model: str,
    attempt: int,
    elapsed: float,
    tool_calls: Optional[int] = None,
    status: str = "success",
    error_category: Optional[str] = None,
    fallback_reason: Optional[str] = None,
) -> None:
    parts = [
        f"provider={provider}",
        f"model={model}",
        f"attempt={attempt}",
        f"duration={elapsed:.3f}s",
        f"status={status}",
    ]
    if tool_calls is not None:
        parts.append(f"tool_calls={tool_calls}")
    if error_category:
        parts.append(f"error_category={error_category}")
    if fallback_reason:
        parts.append(f"fallback_reason={fallback_reason}")
    print(f"[LLM] {' '.join(parts)}")


class LLMProvider:
    """Groq-primary LLM provider with model-level fallback."""

    def __init__(self):
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.primary_model = os.getenv("GROQ_LLM_MODEL", _DEFAULT_GROQ_MODEL_PRIMARY)
        self.secondary_model = os.getenv("GROQ_LLM_MODEL_SECONDARY", _DEFAULT_GROQ_MODEL_SECONDARY)
        self._groq_client = None

    def _groq(self):
        if self._groq_client is None and self.groq_key:
            from groq import Groq
            self._groq_client = Groq(api_key=self.groq_key, max_retries=0)
        return self._groq_client

    def call(
        self,
        messages: List[Dict],
        tools: List[Dict],
        max_tokens: int = 800,
        deadline: Optional[float] = None,
    ) -> Tuple[Any, str, str]:
        """
        Call the LLM with automatic model fallback.

        Returns (response, provider_name, model_name).
        Raises ProviderError with .category set when all models fail.
        Never logs keys or message content.
        """
        if deadline is None:
            deadline = time.monotonic() + OVERALL_DEADLINE

        if not self.groq_key:
            raise ProviderError(
                "No API key configured. Set GROQ_API_KEY.", "config"
            )

        client = self._groq()
        if client is None:
            raise ProviderError("Groq client could not be initialised.", "config")

        models = [self.primary_model, self.secondary_model]
        last_error: Optional[Exception] = None
        last_category = "permanent"

        for model in models:
            for attempt in range(1, 3):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise ProviderError("Overall response deadline exceeded.", "transient")

                actual_timeout = min(GROQ_TIMEOUT, remaining)
                t0 = time.monotonic()

                try:
                    create_kwargs: Dict = dict(
                        model=model,
                        messages=messages,
                        max_tokens=max_tokens,
                        timeout=actual_timeout,
                    )
                    if tools:
                        create_kwargs["tools"] = tools
                        create_kwargs["tool_choice"] = "auto"
                    resp = client.chat.completions.create(**create_kwargs)
                    elapsed = time.monotonic() - t0
                    tool_count = len(resp.choices[0].message.tool_calls or [])
                    _log_call("groq", model, attempt, elapsed, tool_calls=tool_count)
                    return resp, "groq", model

                except Exception as e:
                    elapsed = time.monotonic() - t0
                    cat = _error_category(e)
                    last_error = e
                    last_category = cat
                    _log_call("groq", model, attempt, elapsed, status="error", error_category=cat)
                    print(f"[LLM] error detail: {type(e).__name__}: {str(e)[:200]}")

                    # Auth errors: stop immediately, no retry, no fallback
                    if cat == "auth":
                        raise ProviderError(str(e), cat)

                    # Model not found / invalid: skip to next model without retry
                    if cat in ("not_found", "invalid"):
                        print(f"[LLM] model {model} unavailable ({cat}), trying next model")
                        break

                    # Transient: retry once, then try next model
                    if attempt == 1 and cat == "transient":
                        delay = _retry_delay(e)
                        if time.monotonic() + delay < deadline:
                            time.sleep(delay)
                            continue

                    break  # move to next model

        raise ProviderError(str(last_error), last_category)
