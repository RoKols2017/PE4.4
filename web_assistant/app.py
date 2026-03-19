from __future__ import annotations

import logging

from flask import Flask

from ai_logic import AssistantAI
from config import load_settings
from domain import LeadRepository
from postgres_repository import PostgresLeadRepository
from routes import bp
from session import SessionStore


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
            "storage_backend": "postgres",
            "openai_model": settings.openai_model,
            "leads_view_enabled": bool(settings.leads_view_token),
        },
    )

    app = Flask(__name__, static_folder="static", template_folder="templates")

    lead_repo: LeadRepository = PostgresLeadRepository(
        database_url=settings.database_url,
        local_timezone=settings.local_timezone,
        max_retry_attempts=settings.max_retry_attempts,
        retry_delay_seconds=settings.retry_delay_seconds,
        connect_timeout_seconds=settings.db_connect_timeout_seconds,
    )
    lead_repo.ensure_schema()

    app.config["assistant_ai"] = AssistantAI(settings.openai_api_key, settings.openai_model)
    app.config["session_store"] = SessionStore()
    app.config["lead_repo"] = lead_repo
    app.config["leads_view_token"] = settings.leads_view_token

    app.register_blueprint(bp)

    return app


if __name__ == "__main__":
    cfg = load_settings()
    application = create_app()
    application.run(host=cfg.app_host, port=cfg.app_port)
