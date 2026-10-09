"""Classify LLM errors (Claude API / Bedrock / LiteLLM) for user-facing SSE messages."""

from __future__ import annotations

import json
from typing import Any

_BUDGET_MESSAGE = (
    "Session LLM budget is exhausted. Ask your facilitator to regenerate the LiteLLM key or raise the budget."
)
_RATE_LIMIT_MESSAGE = "The model is rate limited right now (too many tokens per minute). Wait a moment and try again."


def _truncate_detail(text: str, *, max_len: int = 280) -> str:
    normalized = text.strip()
    if len(normalized) <= max_len:
        return normalized or "An LLM request failed."
    return normalized[: max_len - 1] + "…"


def _coerce_body(raw: object) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def _error_type_from_body(body: dict[str, Any]) -> str | None:
    err = body.get("error")
    if isinstance(err, dict):
        t = err.get("type")
        if isinstance(t, str):
            return t
    return None


def classify_llm_exception(exc: BaseException) -> tuple[str, str]:
    """Return ``(error_code, user_message)`` for SSE ``error`` events.

    Codes: ``budget_exceeded`` (a LiteLLM-style spend limit), ``rate_limited`` (HTTP 429) and
    ``llm_error`` (anything else).
    """
    try:
        from anthropic import APIStatusError, RateLimitError
    except ImportError:  # pragma: no cover - anthropic is a hard dependency
        APIStatusError = RateLimitError = None  # type: ignore[misc, assignment]

    if APIStatusError is not None and isinstance(exc, APIStatusError):
        body = _coerce_body(getattr(exc, "body", None))
        if _error_type_from_body(body) == "budget_exceeded":
            return ("budget_exceeded", _BUDGET_MESSAGE)
    if RateLimitError is not None and isinstance(exc, RateLimitError):
        return ("rate_limited", _RATE_LIMIT_MESSAGE)

    text = str(exc)
    lower = text.lower()
    if "budget_exceeded" in lower or "budget has been exceeded" in lower:
        return ("budget_exceeded", _BUDGET_MESSAGE)

    return ("llm_error", _truncate_detail(text))
