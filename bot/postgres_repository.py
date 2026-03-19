from __future__ import annotations

import logging
import json
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import psycopg

from domain import Lead, LeadDraft, normalize_phone, normalize_telegram_username


LOGGER = logging.getLogger(__name__)


class PostgresLeadRepository:
    def __init__(
        self,
        database_url: str,
        local_timezone: str,
        max_retry_attempts: int,
        retry_delay_seconds: float,
        connect_timeout_seconds: int,
    ) -> None:
        self.database_url = database_url
        self.local_timezone = local_timezone
        self.max_retry_attempts = max_retry_attempts
        self.retry_delay_seconds = retry_delay_seconds
        self.connect_timeout_seconds = connect_timeout_seconds

    def ensure_schema(self) -> None:
        LOGGER.info("[bot.postgres.ensure_schema] Checking database connectivity")
        with psycopg.connect(self.database_url, connect_timeout=self.connect_timeout_seconds) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
        LOGGER.info("[bot.postgres.ensure_schema] Database is reachable")

    def save_lead(self, lead: Lead, quality_payload: dict | None = None) -> None:
        payload = {
            "lead_id": lead.lead_id,
            "source": lead.source,
            "source_user_id": lead.source_user_id,
            "source_username": lead.source_username,
            "name": lead.name,
            "telegram_username": lead.telegram_username,
            "phone": lead.phone,
            "email": lead.email,
            "contact_ok": lead.contact_ok,
            "preferred_contact_method": lead.preferred_contact_method,
            "request": lead.request,
            "status": lead.status,
            "priority": lead.priority,
            "utm_source": lead.utm_source,
            "utm_campaign": lead.utm_campaign,
            "manager_note": lead.manager_note,
            "created_at_utc": lead.created_at_utc,
            "created_at_local": lead.created_at_local,
            "last_update_at_utc": lead.last_update_at_utc,
        }

        for attempt in range(1, self.max_retry_attempts + 1):
            try:
                LOGGER.debug(
                    "[bot.postgres.save_lead] Persisting lead",
                    extra={
                        "lead_id": lead.lead_id,
                        "attempt": attempt,
                        "source": lead.source,
                        "quality_payload": quality_payload or {},
                    },
                )
                with psycopg.connect(self.database_url, connect_timeout=self.connect_timeout_seconds) as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            """
                            INSERT INTO leads (
                                lead_id,
                                source,
                                source_user_id,
                                source_username,
                                name,
                                telegram_username,
                                phone,
                                email,
                                contact_ok,
                                preferred_contact_method,
                                request,
                                status,
                                priority,
                                utm_source,
                                utm_campaign,
                                manager_note,
                                created_at_utc,
                                created_at_local,
                                last_update_at_utc
                            ) VALUES (
                                %(lead_id)s,
                                %(source)s,
                                %(source_user_id)s,
                                %(source_username)s,
                                %(name)s,
                                %(telegram_username)s,
                                %(phone)s,
                                %(email)s,
                                %(contact_ok)s,
                                %(preferred_contact_method)s,
                                %(request)s,
                                %(status)s,
                                %(priority)s,
                                %(utm_source)s,
                                %(utm_campaign)s,
                                %(manager_note)s,
                                %(created_at_utc)s,
                                %(created_at_local)s,
                                %(last_update_at_utc)s
                            )
                            """,
                            payload,
                        )
                        cursor.execute(
                            """
                            INSERT INTO lead_events (
                                lead_id,
                                event_type,
                                payload,
                                source,
                                session_id,
                                created_at_utc
                            ) VALUES (
                                %(lead_id)s,
                                %(event_type)s,
                                %(payload)s::jsonb,
                                %(source)s,
                                %(session_id)s,
                                %(created_at_utc)s
                            )
                            """,
                            {
                                "lead_id": lead.lead_id,
                                "event_type": "lead_submitted",
                                "payload": json.dumps(quality_payload or {}),
                                "source": lead.source,
                                "session_id": lead.source_user_id,
                                "created_at_utc": lead.created_at_utc,
                            },
                        )
                    conn.commit()
                LOGGER.info("[bot.postgres.save_lead] lead_saved", extra={"lead_id": lead.lead_id, "source": lead.source})
                return
            except Exception as error:  # noqa: BLE001
                if attempt == self.max_retry_attempts:
                    LOGGER.error(
                        "[bot.postgres.save_lead] Final save failure",
                        extra={"lead_id": lead.lead_id, "attempt": attempt, "error": str(error)},
                    )
                    raise

                LOGGER.warning(
                    "[bot.postgres.save_lead] Retrying save",
                    extra={"lead_id": lead.lead_id, "attempt": attempt, "error": str(error)},
                )
                time.sleep(self.retry_delay_seconds)


def build_lead_record(lead_id: str, draft: LeadDraft, local_timezone: str) -> Lead:
    created_at_utc_dt = datetime.now(timezone.utc)
    created_at_utc = created_at_utc_dt.isoformat()
    created_at_local = created_at_utc_dt.astimezone(ZoneInfo(local_timezone)).isoformat()

    phone = normalize_phone(draft.phone) if draft.phone else ""
    telegram_username = normalize_telegram_username(draft.telegram_username) if draft.telegram_username else ""
    contact_ok = bool(phone or telegram_username)

    if phone and telegram_username:
        preferred = "both"
    elif phone:
        preferred = "phone"
    elif telegram_username:
        preferred = "telegram"
    else:
        preferred = "not_specified"

    return Lead(
        lead_id=lead_id,
        created_at_utc=created_at_utc,
        created_at_local=created_at_local,
        source="telegram_bot",
        source_user_id=draft.source_user_id,
        source_username=normalize_telegram_username(draft.source_username) if draft.source_username else "",
        name=draft.name,
        telegram_username=telegram_username,
        phone=phone,
        email="",
        contact_ok=contact_ok,
        preferred_contact_method=preferred,
        request=draft.request,
        status="new",
        priority="normal",
        utm_source="",
        utm_campaign="",
        manager_note="",
        last_update_at_utc=created_at_utc,
    )
