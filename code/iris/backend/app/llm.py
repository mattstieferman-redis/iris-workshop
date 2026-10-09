"""Chat-model provider selection (OpenAI or Claude) and provider-neutral message helpers."""

from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel

from backend.app.settings import OPENAI_KEY_PLACEHOLDER, Settings

# Anthropic requires max_tokens on every request.
ANTHROPIC_MAX_TOKENS = 4096


def build_chat_model(settings: Settings, *, lightweight: bool = False) -> BaseChatModel:
    """Build the LangChain chat model for the configured provider.

    ``lightweight=True`` returns the cheaper model used for answer verification.
    """
    name = settings.lightweight_model_name if lightweight else settings.chat_model_name
    if settings.uses_anthropic:
        from langchain_anthropic import ChatAnthropic

        kwargs: dict[str, Any] = {
            "model": name,
            "temperature": 0.2,
            "max_tokens": ANTHROPIC_MAX_TOKENS,
            "api_key": settings.anthropic_api_key or OPENAI_KEY_PLACEHOLDER,
        }
        if settings.anthropic_base_url:
            kwargs["base_url"] = settings.anthropic_base_url
        return ChatAnthropic(**kwargs)

    from langchain_openai import ChatOpenAI

    kwargs = {
        "model": name,
        "temperature": 0.2,
        "api_key": settings.openai_api_key or OPENAI_KEY_PLACEHOLDER,
    }
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    return ChatOpenAI(**kwargs)


def message_text(content: Any) -> str:
    """Plain text of a message's content.

    OpenAI returns a string. Claude returns a list of blocks (text, tool_use, thinking...), of which
    only the text blocks are user-visible.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("type", "text") == "text":
                text = item.get("text")
                if text:
                    parts.append(str(text))
        return "".join(parts)
    return "" if content is None else str(content)
