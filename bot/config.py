import os
import logging
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    openai_api_key: str
    openai_model: str
    database_url: str
    db_connect_timeout_seconds: int
    local_timezone: str
    poll_interval_seconds: int
    max_retry_attempts: int
    retry_delay_seconds: float
    log_level: str


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def load_settings() -> Settings:
    return Settings(
        telegram_bot_token=_required("TELEGRAM_BOT_TOKEN"),
        openai_api_key=_required("OPENAI_API_KEY"),
        openai_model=_str_env("OPENAI_MODEL", "gpt-4o-mini"),
        database_url=_required("DATABASE_URL"),
        db_connect_timeout_seconds=_int_env("DB_CONNECT_TIMEOUT_SECONDS", 5, minimum=1),
        local_timezone=_str_env("LOCAL_TIMEZONE", "UTC"),
        poll_interval_seconds=_int_env("POLL_INTERVAL_SECONDS", 1, minimum=1),
        max_retry_attempts=_int_env("MAX_RETRY_ATTEMPTS", 3, minimum=1),
        retry_delay_seconds=_float_env("RETRY_DELAY_SECONDS", 1.0, minimum=0.1),
        log_level=_str_env("LOG_LEVEL", "INFO").upper(),
    )


def _str_env(name: str, default: str) -> str:
    raw = os.getenv(name)
    if raw is None:
        LOGGER.warning("[bot.config] Using default env value", extra={"name": name, "default": default})
        return default

    cleaned = raw.strip()
    if not cleaned:
        LOGGER.warning("[bot.config] Using default for empty env value", extra={"name": name, "default": default})
        return default
    return cleaned


def _int_env(name: str, default: int, minimum: int = 0) -> int:
    raw_input = os.getenv(name)
    if raw_input is None:
        LOGGER.warning("[bot.config] Using default env value", extra={"name": name, "default": default})
        raw = str(default)
    else:
        raw = raw_input.strip()
    try:
        value = int(raw)
    except ValueError as error:
        raise ValueError(f"Invalid integer for {name}: {raw}") from error

    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}, got {value}")

    return value


def _float_env(name: str, default: float, minimum: float = 0.0) -> float:
    raw_input = os.getenv(name)
    if raw_input is None:
        LOGGER.warning("[bot.config] Using default env value", extra={"name": name, "default": default})
        raw = str(default)
    else:
        raw = raw_input.strip()
    try:
        value = float(raw)
    except ValueError as error:
        raise ValueError(f"Invalid float for {name}: {raw}") from error

    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}, got {value}")

    return value
