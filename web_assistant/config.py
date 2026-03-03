from __future__ import annotations

import os
import logging
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class Settings:
    app_host: str
    app_port: int
    log_level: str
    openai_api_key: str
    openai_model: str
    database_url: str
    db_connect_timeout_seconds: int
    leads_view_token: str
    max_retry_attempts: int
    retry_delay_seconds: float
    local_timezone: str


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _int_env(name: str, default: int, minimum: int = 0) -> int:
    raw_input = os.getenv(name)
    if raw_input is None:
        LOGGER.warning("[web_assistant.config] Using default env value", extra={"env_var": name, "default": default})
        raw = str(default)
    else:
        raw = raw_input.strip()
    value = int(raw)
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}, got {value}")
    return value


def _float_env(name: str, default: float, minimum: float = 0.0) -> float:
    raw_input = os.getenv(name)
    if raw_input is None:
        LOGGER.warning("[web_assistant.config] Using default env value", extra={"env_var": name, "default": default})
        raw = str(default)
    else:
        raw = raw_input.strip()
    value = float(raw)
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}, got {value}")
    return value


def load_settings() -> Settings:
    return Settings(
        app_host=_str_env("WEB_ASSISTANT_HOST", "0.0.0.0"),
        app_port=_int_env("WEB_ASSISTANT_PORT", 5000, minimum=1),
        log_level=_str_env("LOG_LEVEL", "INFO").upper(),
        openai_api_key=_required("OPENAI_API_KEY"),
        openai_model=_str_env("OPENAI_MODEL", "gpt-4o-mini"),
        database_url=_required("DATABASE_URL"),
        db_connect_timeout_seconds=_int_env("DB_CONNECT_TIMEOUT_SECONDS", 5, minimum=1),
        leads_view_token=_str_env("LEADS_VIEW_TOKEN", ""),
        max_retry_attempts=_int_env("MAX_RETRY_ATTEMPTS", 3, minimum=1),
        retry_delay_seconds=_float_env("RETRY_DELAY_SECONDS", 1.0, minimum=0.1),
        local_timezone=_str_env("LOCAL_TIMEZONE", "UTC"),
    )


def _str_env(name: str, default: str) -> str:
    raw = os.getenv(name)
    if raw is None:
        LOGGER.warning("[web_assistant.config] Using default env value", extra={"env_var": name, "default": default})
        return default
    cleaned = raw.strip()
    if not cleaned:
        LOGGER.warning("[web_assistant.config] Using default for empty env value", extra={"env_var": name, "default": default})
        return default
    return cleaned
