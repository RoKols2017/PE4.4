from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import Resource, build

from domain import Lead, LeadDraft, normalize_phone, normalize_telegram_username


LOGGER = logging.getLogger(__name__)

HEADERS = [
    "lead_id",
    "created_at_utc",
    "created_at_local",
    "source",
    "source_user_id",
    "source_username",
    "name",
    "telegram_username",
    "phone",
    "contact_ok",
    "preferred_contact_method",
    "request",
    "status",
    "priority",
    "utm_source",
    "utm_campaign",
    "manager_note",
    "last_update_at_utc",
]


class SheetsLeadRepository:
    def __init__(
        self,
        spreadsheet_id: str,
        service_account_info: dict,
        sheet_name: str,
        local_timezone: str,
        max_retry_attempts: int,
        retry_delay_seconds: float,
        service: Resource | None = None,
    ) -> None:
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name
        self.local_timezone = local_timezone
        self.max_retry_attempts = max_retry_attempts
        self.retry_delay_seconds = retry_delay_seconds

        if service is None:
            credentials = Credentials.from_service_account_info(
                service_account_info,
                scopes=["https://www.googleapis.com/auth/spreadsheets"],
            )
            self.service = build("sheets", "v4", credentials=credentials, cache_discovery=False)
        else:
            self.service = service

    def ensure_schema(self) -> None:
        LOGGER.info("[sheets.ensure_schema] Checking sheet and header")

        spreadsheet = (
            self.service.spreadsheets()
            .get(spreadsheetId=self.spreadsheet_id, includeGridData=False)
            .execute()
        )

        sheet_exists = any(
            s.get("properties", {}).get("title") == self.sheet_name
            for s in spreadsheet.get("sheets", [])
        )

        if not sheet_exists:
            LOGGER.warning("[sheets.ensure_schema] Sheet is missing, creating", extra={"sheet": self.sheet_name})
            (
                self.service.spreadsheets()
                .batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body={
                        "requests": [{"addSheet": {"properties": {"title": self.sheet_name}}}],
                    },
                )
                .execute()
            )

        range_name = f"{self.sheet_name}!A1:R1"
        existing = (
            self.service.spreadsheets()
            .values()
            .get(spreadsheetId=self.spreadsheet_id, range=range_name)
            .execute()
            .get("values", [])
        )

        if not existing or existing[0] != HEADERS:
            LOGGER.warning("[sheets.ensure_schema] Header mismatch, writing canonical header")
            (
                self.service.spreadsheets()
                .values()
                .update(
                    spreadsheetId=self.spreadsheet_id,
                    range=range_name,
                    valueInputOption="RAW",
                    body={"values": [HEADERS]},
                )
                .execute()
            )

    def append_lead(self, lead: Lead) -> None:
        payload = [
            lead.lead_id,
            lead.created_at_utc,
            lead.created_at_local,
            lead.source,
            lead.source_user_id,
            lead.source_username,
            lead.name,
            lead.telegram_username,
            lead.phone,
            str(lead.contact_ok).lower(),
            lead.preferred_contact_method,
            lead.request,
            lead.status,
            lead.priority,
            lead.utm_source,
            lead.utm_campaign,
            lead.manager_note,
            lead.last_update_at_utc,
        ]

        for attempt in range(1, self.max_retry_attempts + 1):
            try:
                LOGGER.debug(
                    "[sheets.append_lead] Appending lead row",
                    extra={"lead_id": lead.lead_id, "attempt": attempt},
                )
                (
                    self.service.spreadsheets()
                    .values()
                    .append(
                        spreadsheetId=self.spreadsheet_id,
                        range=f"{self.sheet_name}!A:R",
                        valueInputOption="RAW",
                        insertDataOption="INSERT_ROWS",
                        body={"values": [payload]},
                    )
                    .execute()
                )
                LOGGER.info("[sheets.append_lead] Lead saved", extra={"lead_id": lead.lead_id})
                return
            except Exception as error:  # noqa: BLE001
                if attempt == self.max_retry_attempts:
                    LOGGER.error(
                        "[sheets.append_lead] Failed to append lead",
                        extra={"lead_id": lead.lead_id, "attempt": attempt, "error": str(error)},
                    )
                    raise

                LOGGER.warning(
                    "[sheets.append_lead] Retry append",
                    extra={"lead_id": lead.lead_id, "attempt": attempt, "error": str(error)},
                )
                time.sleep(self.retry_delay_seconds)


def build_lead_record(
    lead_id: str,
    draft: LeadDraft,
    local_timezone: str,
) -> Lead:
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
