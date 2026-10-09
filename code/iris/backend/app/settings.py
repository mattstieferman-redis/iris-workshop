from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

DEFAULT_MEMORY_SIMILARITY_THRESHOLD = 0.3

# Lets the OpenAI clients be constructed (and the app boot) before a key is configured.
# Chat requests are rejected with a clear message until a real key is set.
OPENAI_KEY_PLACEHOLDER = "missing-openai-api-key"

# Default Claude model when LLM_PROVIDER=anthropic and LLM_MODEL is unset (Claude API model ID).
DEFAULT_CLAUDE_MODEL = "claude-sonnet-5-5"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = Field(default="")
    openai_base_url: str | None = Field(default=None)
    openai_chat_model: str = Field(default="gpt-4o")
    openai_embedding_model: str = Field(default="text-embedding-3-small")
    # Which provider serves the agent's chat model: "openai" (default) or "anthropic" (Claude, via the
    # Claude API or any Anthropic-compatible endpoint such as Amazon Bedrock).
    llm_provider: str = Field(default="openai")
    # Overrides OPENAI_CHAT_MODEL (or the default Claude model) when set. On Amazon Bedrock use e.g.
    # "anthropic.claude-sonnet-5-5".
    llm_model: str = Field(default="")
    llm_lightweight_model: str = Field(default="")
    anthropic_api_key: str = Field(default="")
    # Leave empty for the Claude API. For Bedrock: https://bedrock-mantle.<region>.api.aws/anthropic
    anthropic_base_url: str | None = Field(default=None)
    openai_reasoning_effort: str = Field(default="medium")
    openai_lightweight_model: str = Field(default="")
    openai_lightweight_reasoning_effort: str = Field(default="low")

    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    redis_username: str = Field(default="default")
    redis_password: str = Field(default="")
    redis_db: int = Field(default=0)
    redis_ssl: bool = Field(default=False)

    @field_validator("redis_port", mode="before")
    @classmethod
    def _empty_port_to_default(cls, v: object) -> object:
        if isinstance(v, str) and v.strip() == "":
            return 6379
        return v

    @field_validator("redis_db", mode="before")
    @classmethod
    def _empty_db_to_default(cls, v: object) -> object:
        if isinstance(v, str) and v.strip() == "":
            return 0
        return v

    ctx_admin_key: str = Field(default="")
    mcp_agent_key: str = Field(default="")
    ctx_surface_id: str = Field(default="")
    ctx_redis_instance_id: str = Field(default="")

    memory_api_base_url: str = Field(default="")
    memory_store_id: str = Field(default="")
    memory_api_key: str = Field(default="")
    memory_owner_id: str = Field(default="")
    memory_actor_id: str = Field(default="iris-agent")
    memory_namespace: str = Field(default="")
    memory_similarity_threshold: float | None = Field(default=None)
    memory_limit: int = Field(default=6)

    langcache_host: str = Field(default="")
    langcache_cache_id: str = Field(default="")
    langcache_api_key: str = Field(default="")
    langcache_threshold: float = Field(default=0.9)

    backend_host: str = Field(default="127.0.0.1")
    backend_port: int = Field(default=8040)
    cors_origin: str = Field(default="http://localhost:3040")
    guardrail_enabled: bool = Field(default=True)
    # Send the LLM only the tools a question needs (see ToolRoutingConfig in the domain manifest).
    tool_routing_enabled: bool = Field(default=True)
    demo_domain: str = Field(default="reddash")
    show_final_verifier_trace_step: bool = Field(default=False)
    show_llm_trace_steps: bool = Field(default=False)

    radish_hf_embedding_model: str = Field(
        default="sentence-transformers/all-mpnet-base-v2",
    )
    hf_token: str = Field(default="", validation_alias="HF_TOKEN")

    @field_validator("memory_similarity_threshold", mode="before")
    @classmethod
    def _empty_similarity_threshold_to_none(cls, v: object) -> object:
        if isinstance(v, str) and v.strip() == "":
            return None
        return v

    @property
    def effective_memory_namespace(self) -> str:
        return self.memory_namespace or f"{self.demo_domain}-demo"

    @property
    def effective_memory_actor_id(self) -> str:
        return self.memory_actor_id or f"{self.demo_domain}-agent"

    @property
    def uses_anthropic(self) -> bool:
        return self.llm_provider.strip().lower() == "anthropic"

    @property
    def chat_model_name(self) -> str:
        """Model name for the agent, whichever provider is selected."""
        if self.llm_model:
            return self.llm_model
        return DEFAULT_CLAUDE_MODEL if self.uses_anthropic else self.openai_chat_model

    @property
    def lightweight_model_name(self) -> str:
        return self.llm_lightweight_model or self.openai_lightweight_model or self.chat_model_name

    @property
    def llm_configured(self) -> bool:
        """True when the selected provider has an API key."""
        return bool(self.anthropic_api_key if self.uses_anthropic else self.openai_api_key)

    @property
    def llm_key_env_var(self) -> str:
        return "ANTHROPIC_API_KEY" if self.uses_anthropic else "OPENAI_API_KEY"


def get_settings() -> Settings:
    return Settings()
