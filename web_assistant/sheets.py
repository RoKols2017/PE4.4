from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import Resource, build

from domain import LeadDraft, normalize_email, normalize_phone
from sheets_schema import HEADERS


LOGGER = logging.getLogger(__name__)


class SheetsLeadRepository:
    def __init__(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        service_account_info: dict,
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
        LOGGER.info("[web_assistant.sheets] Checking shared schema")
        spreadsheet = (
            self.service.spreadsheets()
            .get(spreadsheetId=self.spreadsheet_id, includeGridData=False)
            .execute()
        )
        exists = any(
            s.get("properties", {}).get("title") == self.sheet_name
            for s in spreadsheet.get("sheets", [])
        )
        if not exists:
            LOGGER.warning("[web_assistant.sheets] Missing sheet, creating", extra={"sheet": self.sheet_name})
            (
                self.service.spreadsheets()
                .batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body={"requests": [{"addSheet": {"properties": {"title": self.sheet_name}}}]},
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
            LOGGER.warning("[web_assistant.sheets] Writing canonical headers")
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

    def append_website_lead(self, lead_id: str, draft: LeadDraft) -> None:
        now_utc = datetime.now(timezone.utc)
        created_at_utc = now_utc.isoformat()
        created_at_local = now_utc.astimezone(ZoneInfo(self.local_timezone)).isoformat()

        phone = normalize_phone(draft.phone) if draft.phone else ""
        email = normalize_email(draft.email) if draft.email else ""
        telegram_username_column = f"email:{email}" if email else ""
        contact_ok = bool(phone or email)
        preferred_contact_method = "phone" if phone else "not_specified"

        row = [
            lead_id,
            created_at_utc,
            created_at_local,
            "website_assistant",
            draft.source_user_id,
            "",
            draft.name,
            telegram_username_column,
            phone,
            str(contact_ok).lower(),
            preferred_contact_method,
            draft.request,
            "new",
            "normal",
            "",
            "",
            "",
            created_at_utc,
        ]

        for attempt in range(1, self.max_retry_attempts + 1):
            try:
                LOGGER.debug("[web_assistant.sheets] Append row", extra={"lead_id": lead_id, "attempt": attempt})
                (
                    self.service.spreadsheets()
                    .values()
                    .append(
                        spreadsheetId=self.spreadsheet_id,
                        range=f"{self.sheet_name}!A:R",
                        valueInputOption="RAW",
                        insertDataOption="INSERT_ROWS",
                        body={"values": [row]},
                    )
                    .execute()
                )
                LOGGER.info("[web_assistant.sheets] Lead saved", extra={"lead_id": lead_id})
                return
            except Exception as error:  # noqa: BLE001
                if attempt == self.max_retry_attempts:
                    LOGGER.error(
                        "[web_assistant.sheets] Append failed",
                        extra={"lead_id": lead_id, "attempt": attempt, "error": str(error)},
                    )
                    raise
                LOGGER.warning(
                    "[web_assistant.sheets] Retrying append",
                    extra={"lead_id": lead_id, "attempt": attempt, "error": str(error)},
                )
                time.sleep(self.retry_delay_seconds)
