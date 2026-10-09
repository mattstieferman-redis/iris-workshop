import pytest

from backend.app.llm import ANTHROPIC_MAX_TOKENS, build_chat_model, message_text
from backend.app.settings import DEFAULT_CLAUDE_MODEL, Settings


def _settings(**overrides) -> Settings:
    base = {"openai_api_key": "", "anthropic_api_key": "", "llm_provider": "openai", "llm_model": ""}
    return Settings(_env_file=None, **{**base, **overrides})


def test_openai_is_the_default_provider():
    s = _settings(openai_api_key="sk-test", openai_chat_model="gpt-4o")
    assert not s.uses_anthropic
    assert s.chat_model_name == "gpt-4o"
    assert s.llm_configured and s.llm_key_env_var == "OPENAI_API_KEY"
    assert type(build_chat_model(s)).__name__ == "ChatOpenAI"


def test_anthropic_provider_needs_its_own_key():
    s = _settings(llm_provider="anthropic", openai_api_key="sk-test")
    assert s.uses_anthropic
    assert not s.llm_configured  # an OpenAI key does not configure Claude
    assert s.llm_key_env_var == "ANTHROPIC_API_KEY"
    assert s.chat_model_name == DEFAULT_CLAUDE_MODEL


def test_anthropic_model_uses_override_base_url_and_max_tokens():
    s = _settings(
        llm_provider="Anthropic",
        anthropic_api_key="token",
        anthropic_base_url="https://bedrock-mantle.us-east-1.api.aws/anthropic",
        llm_model="anthropic.claude-sonnet-5-5",
        llm_lightweight_model="anthropic.claude-haiku-4-5",
    )
    model = build_chat_model(s)
    assert type(model).__name__ == "ChatAnthropic"
    assert model.model == "anthropic.claude-sonnet-5-5"
    assert model.anthropic_api_url == "https://bedrock-mantle.us-east-1.api.aws/anthropic"
    assert model.max_tokens == ANTHROPIC_MAX_TOKENS
    assert build_chat_model(s, lightweight=True).model == "anthropic.claude-haiku-4-5"


def test_lightweight_model_falls_back_to_the_chat_model():
    s = _settings(llm_provider="anthropic", anthropic_api_key="token", llm_model="claude-x")
    assert s.lightweight_model_name == "claude-x"


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
