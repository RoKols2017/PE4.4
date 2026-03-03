from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import psycopg

from domain import LeadDraft, normalize_email, normalize_phone


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
        LOGGER.info("[web_assistant.postgres.ensure_schema] Checking database connectivity")
        with psycopg.connect(self.database_url, connect_timeout=self.connect_timeout_seconds) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
        LOGGER.info("[web_assistant.postgres.ensure_schema] Database is reachable")

    def save_website_lead(self, lead_id: str, draft: LeadDraft, session_id: str) -> None:
        now_utc = datetime.now(timezone.utc)
        created_at_utc = now_utc.isoformat()
        created_at_local = now_utc.astimezone(ZoneInfo(self.local_timezone)).isoformat()

        phone = normalize_phone(draft.phone) if draft.phone else ""
        email = normalize_email(draft.email) if draft.email else ""
        contact_ok = bool(phone or email)

        if phone and email:
            preferred_contact_method = "both"
        elif phone:
            preferred_contact_method = "phone"
        elif email:
            preferred_contact_method = "email"
        else:
            preferred_contact_method = "not_specified"

        payload = {
            "lead_id": lead_id,
            "source": "website_assistant",
            "source_user_id": draft.source_user_id,
            "source_username": "",
            "name": draft.name,
            "telegram_username": "",
            "phone": phone,
            "email": email,
            "contact_ok": contact_ok,
            "preferred_contact_method": preferred_contact_method,
            "request": draft.request,
            "status": "new",
            "priority": "normal",
            "utm_source": "",
            "utm_campaign": "",
            "manager_note": "",
            "created_at_utc": created_at_utc,
            "created_at_local": created_at_local,
            "last_update_at_utc": created_at_utc,
        }

        for attempt in range(1, self.max_retry_attempts + 1):
            try:
                LOGGER.debug(
                    "[web_assistant.postgres.save_website_lead] Persisting lead",
                    extra={"lead_id": lead_id, "attempt": attempt, "source": payload["source"]},
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
                                "lead_id": lead_id,
                                "event_type": "lead_submitted",
                                "payload": "{}",
                                "source": payload["source"],
                                "session_id": session_id,
                                "created_at_utc": created_at_utc,
                            },
                        )
                    conn.commit()
                LOGGER.info("[web_assistant.postgres.save_website_lead] lead_saved", extra={"lead_id": lead_id})
                return
            except Exception as error:  # noqa: BLE001
                if attempt == self.max_retry_attempts:
                    LOGGER.error(
                        "[web_assistant.postgres.save_website_lead] Final save failure",
                        extra={"lead_id": lead_id, "attempt": attempt, "session_id": session_id, "error": str(error)},
                    )
                    raise

                LOGGER.warning(
                    "[web_assistant.postgres.save_website_lead] Retrying save",
                    extra={"lead_id": lead_id, "attempt": attempt, "session_id": session_id, "error": str(error)},
                )
                time.sleep(self.retry_delay_seconds)
