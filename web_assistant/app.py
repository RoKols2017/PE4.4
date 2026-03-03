from __future__ import annotations

import logging

from flask import Flask

from ai_logic import AssistantAI
from config import load_service_account_info, load_settings
from routes import bp
from session import SessionStore
from sheets import SheetsLeadRepository


def _configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def create_app() -> Flask:
    settings = load_settings()
    _configure_logging(settings.log_level)

    logging.getLogger(__name__).info("[web_assistant.app] Initializing Flask app")
    logging.getLogger(__name__).debug(
        "[web_assistant.app] Config snapshot",
        extra={
            "app_port": settings.app_port,
            "google_sheet_name": settings.google_sheet_name,
            "openai_model": settings.openai_model,
        },
    )

    app = Flask(__name__, static_folder="static", template_folder="templates")

    service_account_info = load_service_account_info(settings.google_service_account_json)
    sheets_repo = SheetsLeadRepository(
        spreadsheet_id=settings.google_sheets_id,
        sheet_name=settings.google_sheet_name,
        service_account_info=service_account_info,
        local_timezone=settings.local_timezone,
        max_retry_attempts=settings.max_retry_attempts,
        retry_delay_seconds=settings.retry_delay_seconds,
    )
    sheets_repo.ensure_schema()

    app.config["assistant_ai"] = AssistantAI(settings.openai_api_key, settings.openai_model)
    app.config["session_store"] = SessionStore()
    app.config["sheets_repo"] = sheets_repo

    app.register_blueprint(bp)

    return app


if __name__ == "__main__":
    cfg = load_settings()
    application = create_app()
    application.run(host=cfg.app_host, port=cfg.app_port)
