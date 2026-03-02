import json
import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    openai_api_key: str
    openai_model: str
    google_sheets_id: str
    google_service_account_json: str
    google_sheet_name: str
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
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini",
        google_sheets_id=_required("GOOGLE_SHEETS_ID"),
        google_service_account_json=_required("GOOGLE_SERVICE_ACCOUNT_JSON"),
        google_sheet_name=os.getenv("GOOGLE_SHEET_NAME", "Leads").strip() or "Leads",
        local_timezone=os.getenv("LOCAL_TIMEZONE", "UTC").strip() or "UTC",
        poll_interval_seconds=_int_env("POLL_INTERVAL_SECONDS", 1, minimum=1),
        max_retry_attempts=_int_env("MAX_RETRY_ATTEMPTS", 3, minimum=1),
        retry_delay_seconds=_float_env("RETRY_DELAY_SECONDS", 1.0, minimum=0.1),
        log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper() or "INFO",
    )


def load_service_account_info(raw: str) -> dict:
    # Supports either raw JSON content or a path to a JSON file.
    if raw.startswith("{"):
        return json.loads(raw)

    with open(raw, "r", encoding="utf-8") as file:
        return json.load(file)


def _int_env(name: str, default: int, minimum: int = 0) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError as error:
        raise ValueError(f"Invalid integer for {name}: {raw}") from error

    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}, got {value}")

    return value


def _float_env(name: str, default: float, minimum: float = 0.0) -> float:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = float(raw)
    except ValueError as error:
        raise ValueError(f"Invalid float for {name}: {raw}") from error

    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}, got {value}")

    return value
