from __future__ import annotations

import json
import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_host: str
    app_port: int
    log_level: str
    openai_api_key: str
    openai_model: str
    google_sheets_id: str
    google_sheet_name: str
    google_service_account_json: str
    max_retry_attempts: int
    retry_delay_seconds: float
    local_timezone: str


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _int_env(name: str, default: int, minimum: int = 0) -> int:
    raw = os.getenv(name, str(default)).strip()
    value = int(raw)
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}, got {value}")
    return value


def _float_env(name: str, default: float, minimum: float = 0.0) -> float:
    raw = os.getenv(name, str(default)).strip()
    value = float(raw)
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}, got {value}")
    return value


def load_settings() -> Settings:
    return Settings(
        app_host=os.getenv("WEB_ASSISTANT_HOST", "0.0.0.0").strip() or "0.0.0.0",
        app_port=_int_env("WEB_ASSISTANT_PORT", 5000, minimum=1),
        log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper() or "INFO",
        openai_api_key=_required("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini",
        google_sheets_id=_required("GOOGLE_SHEETS_ID"),
        google_sheet_name=os.getenv("GOOGLE_SHEET_NAME", "Leads").strip() or "Leads",
        google_service_account_json=_required("GOOGLE_SERVICE_ACCOUNT_JSON"),
        max_retry_attempts=_int_env("MAX_RETRY_ATTEMPTS", 3, minimum=1),
        retry_delay_seconds=_float_env("RETRY_DELAY_SECONDS", 1.0, minimum=0.1),
        local_timezone=os.getenv("LOCAL_TIMEZONE", "UTC").strip() or "UTC",
    )


def load_service_account_info(raw: str) -> dict:
    if raw.startswith("{"):
        return json.loads(raw)
    with open(raw, "r", encoding="utf-8") as handle:
        return json.load(handle)
