"""Server configuration via pydantic-settings: every knob comes from the
environment (or .env), with defaults that make the offline path work out of
the box. Never put real secrets in this file — see .env.sample."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    server_name: str = "kidspython-tutor-mcp"
    server_version: str = "0.1.0"

    # live tutor service (graceful degradation: only tutor_ask/eval need it)
    tutor_base_url: str = "http://127.0.0.1:8100"
    tutor_user: str = "demo"
    tutor_pass: str = "12345"
    tutor_timeout_s: float = 120.0  # LLM composition can be slow

    # offline knowledge base (chunks.jsonl; see mcp_PLAN.md §2 contracts)
    kb_path: Path = Path(
        "/home/yshao/chat/chatbot/datasets/kidspython-kb/1.1.0/built/chunks.jsonl"
    )
    kb_dataset: str = "kidspython-kb"
    kb_version: str = "1.1.0"

    # MCP-side long-term memory (episodic / semantic / procedural)
    store_path: Path = Path("./data/tutor_mcp.sqlite")

    # Langfuse (eval scores + observability); blank = eval tools unavailable
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://us.cloud.langfuse.com"


@lru_cache
def settings() -> Settings:
    return Settings()
