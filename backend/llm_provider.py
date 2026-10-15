"""
Shared LLM provider: Gemini-primary, Groq-fallback.
Handles retry logic, error categorisation, structured latency logging,
and overall deadline enforcement. Never logs API keys or conversation text.
"""
import os
import random
import re
import time
from typing import Any, Dict, List, Optional, Tuple

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
_DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"
_DEFAULT_GROQ_MODEL = "compound-beta"

GEMINI_TIMEOUT = int(os.getenv("GEMINI_TIMEOUT", "10"))
GROQ_TIMEOUT = int(os.getenv("GROQ_TIMEOUT", "12"))
OVERALL_DEADLINE = int(os.getenv("OVERALL_DEADLINE", "26"))  # under Render's 30s free-tier limit

_TRANSIENT_CODES = {429, 502, 503, 504}
_AUTH_CODES = {401, 403}
_INVALID_CODES = {400, 422}

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
        # category: transient | auth | invalid | permanent | config
        self.category = category


def _error_category(e: Exception) -> str:
    s = str(e)
    name = type(e).__name__
    if any(str(c) in s for c in _AUTH_CODES):
        return "auth"
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
    print(f"[LLM] {' '.join(parts)}")


class LLMProvider:
    """Groq-primary, Gemini-fallback LLM provider."""

    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.gemini_model = os.getenv("GEMINI_MODEL", _DEFAULT_GEMINI_MODEL)
        self.groq_model = os.getenv("GROQ_LLM_MODEL", _DEFAULT_GROQ_MODEL)
        self._gemini_client = None
        self._groq_client = None

    def _gemini(self):
        if self._gemini_client is None and self.gemini_key:
            from openai import OpenAI
            self._gemini_client = OpenAI(
                api_key=self.gemini_key,
                base_url=GEMINI_BASE_URL,
                max_retries=0,
            )
        return self._gemini_client

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
        Call the LLM with automatic fallback.

        Returns (response, provider_name, model_name).
        Raises ProviderError with .category set when all providers fail.
        Never logs keys or message content.
        """
        if deadline is None:
            deadline = time.monotonic() + OVERALL_DEADLINE

        # Groq first (reliable, free, fast); Gemini as fallback
        providers = []
        if self.groq_key:
            providers.append(("groq", self.groq_model, GROQ_TIMEOUT, self._groq))
        if self.gemini_key:
            providers.append(("gemini", self.gemini_model, GEMINI_TIMEOUT, self._gemini))

        if not providers:
            raise ProviderError(
                "No API keys configured. Set GEMINI_API_KEY or GROQ_API_KEY.", "config"
            )

        last_error: Optional[Exception] = None
        last_category = "permanent"

        for pname, model, timeout, client_fn in providers:
            client = client_fn()
            if client is None:
                continue

            for attempt in range(1, 3):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise ProviderError("Overall response deadline exceeded.", "transient")

                actual_timeout = min(timeout, remaining)
                t0 = time.monotonic()

                try:
                    resp = client.chat.completions.create(
                        model=model,
                        messages=messages,
                        tools=tools if tools else None,
                        tool_choice="auto" if tools else None,
                        max_tokens=max_tokens,
                        timeout=actual_timeout,
                    )
                    elapsed = time.monotonic() - t0
                    tool_count = len(resp.choices[0].message.tool_calls or [])
                    _log_call(pname, model, attempt, elapsed, tool_calls=tool_count)
                    return resp, pname, model

                except Exception as e:
                    elapsed = time.monotonic() - t0
                    cat = _error_category(e)
                    last_error = e
                    last_category = cat
                    _log_call(pname, model, attempt, elapsed, status="error", error_category=cat)
                    print(f"[LLM] error detail: {type(e).__name__}: {str(e)[:200]}")

                    if cat in ("auth", "invalid"):
                        break  # no retry for this provider

                    if attempt == 1 and cat == "transient":
                        delay = _retry_delay(e)
                        if time.monotonic() + delay < deadline:
                            time.sleep(delay)
                            continue

                    break  # move to next provider

        raise ProviderError(str(last_error), last_category)
