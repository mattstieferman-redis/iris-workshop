"""Tests for LLM error classification (Claude API / Bedrock / LiteLLM)."""

from __future__ import annotations

import httpx
from anthropic import BadRequestError, RateLimitError

from backend.app.llm_errors import classify_llm_exception


def _response(status: int) -> httpx.Response:
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    return httpx.Response(status, request=request)


def _bad_request(*, body: object) -> BadRequestError:
    return BadRequestError("Bad Request", response=_response(400), body=body)


def test_budget_from_bad_request_body_dict() -> None:
    code, msg = classify_llm_exception(_bad_request(body={"error": {"type": "budget_exceeded", "message": "limit"}}))
    assert code == "budget_exceeded"
    assert "budget is exhausted" in msg.lower()
    assert "facilitator" in msg.lower()


def test_budget_from_bad_request_body_json_string() -> None:
    code, msg = classify_llm_exception(_bad_request(body='{"error": {"type": "budget_exceeded"}}'))
    assert code == "budget_exceeded"
    assert "budget is exhausted" in msg.lower()


def test_budget_fallback_substring() -> None:
    assert classify_llm_exception(RuntimeError('{"type": "budget_exceeded"}'))[0] == "budget_exceeded"
    assert classify_llm_exception(RuntimeError("Budget has been exceeded for this key"))[0] == "budget_exceeded"


def test_rate_limit_is_reported_as_such() -> None:
    exc = RateLimitError("slow down", response=_response(429), body={"error": {"type": "rate_limit_error"}})
    code, msg = classify_llm_exception(exc)
    assert code == "rate_limited"
    assert "rate limited" in msg.lower()


def test_non_budget_bad_request() -> None:
    code, msg = classify_llm_exception(_bad_request(body={"error": {"type": "invalid_request_error", "message": "nope"}}))
    assert code == "llm_error"
    assert msg


def test_generic_exception() -> None:
    code, msg = classify_llm_exception(RuntimeError("Something else broke"))
    assert code == "llm_error"
    assert "Something else broke" in msg
