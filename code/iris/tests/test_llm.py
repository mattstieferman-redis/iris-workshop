import pytest

from backend.app.llm import ANTHROPIC_MAX_TOKENS, build_chat_model, message_text
from backend.app.settings import DEFAULT_CLAUDE_MODEL, Settings


def _settings(**overrides) -> Settings:
    base = {"anthropic_api_key": "", "llm_model": "", "anthropic_base_url": None}
    return Settings(_env_file=None, **{**base, **overrides})


def test_claude_is_the_only_model_and_needs_its_key():
    s = _settings()
    assert not s.llm_configured
    assert s.llm_key_env_var == "ANTHROPIC_API_KEY"
    assert s.chat_model_name == DEFAULT_CLAUDE_MODEL
    assert _settings(anthropic_api_key="k").llm_configured


def test_model_uses_override_base_url_and_max_tokens():
    s = _settings(
        anthropic_api_key="token",
        anthropic_base_url="https://bedrock-mantle.us-east-2.api.aws/anthropic",
        llm_model="anthropic.claude-sonnet-5-5",
        llm_lightweight_model="anthropic.claude-haiku-4-5",
    )
    model = build_chat_model(s)
    assert type(model).__name__ == "ChatAnthropic"
    assert model.model == "anthropic.claude-sonnet-5-5"
    assert model.anthropic_api_url == "https://bedrock-mantle.us-east-2.api.aws/anthropic"
    assert model.max_tokens == ANTHROPIC_MAX_TOKENS
    assert build_chat_model(s, lightweight=True).model == "anthropic.claude-haiku-4-5"


def test_lightweight_model_falls_back_to_the_chat_model():
    s = _settings(anthropic_api_key="token", llm_model="claude-x")
    assert s.lightweight_model_name == "claude-x"


def test_no_openai_dependency_remains():
    import importlib.util

    assert importlib.util.find_spec("openai") is None
    assert importlib.util.find_spec("langchain_openai") is None


@pytest.mark.parametrize(
    "content, expected",
    [
        ("plain text", "plain text"),
        ([{"type": "text", "text": "Hello "}, {"type": "text", "text": "world"}], "Hello world"),
        ([{"type": "thinking", "thinking": "hmm"}, {"type": "text", "text": "Answer"}, {"type": "tool_use", "name": "x"}], "Answer"),
        ([], ""),
        (None, ""),
    ],
)
def test_message_text_keeps_only_visible_text(content, expected):
    assert message_text(content) == expected
