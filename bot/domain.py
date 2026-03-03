from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol


PHONE_RE = re.compile(r"^\+?[0-9]{10,15}$")
TG_RE = re.compile(r"^[A-Za-z0-9_]{5,32}$")


@dataclass(frozen=True)
class Lead:
    lead_id: str
    created_at_utc: str
    created_at_local: str
    source: str
    source_user_id: str
    source_username: str
    name: str
    telegram_username: str
    phone: str
    email: str
    contact_ok: bool
    preferred_contact_method: str
    request: str
    status: str
    priority: str
    utm_source: str
    utm_campaign: str
    manager_note: str
    last_update_at_utc: str


@dataclass
class LeadDraft:
    source_user_id: str
    source_username: str = ""
    name: str = ""
    telegram_username: str = ""
    phone: str = ""
    request: str = ""


class LeadRepository(Protocol):
    def ensure_schema(self) -> None:
        ...

    def save_lead(self, lead: Lead) -> None:
        ...


def normalize_text(value: str) -> str:
    return " ".join(value.strip().split())


def normalize_phone(value: str) -> str:
    return re.sub(r"\s+", "", value.strip())


def normalize_telegram_username(value: str) -> str:
    return value.strip().lstrip("@")


def parse_contact(value: str) -> tuple[str, str]:
    cleaned = normalize_text(value)
    as_phone = normalize_phone(cleaned)
    as_tg = normalize_telegram_username(cleaned)

    if PHONE_RE.fullmatch(as_phone):
        return as_phone, ""
    if TG_RE.fullmatch(as_tg):
        return "", as_tg
    return "", ""


def validate_name(name: str) -> tuple[bool, str]:
    normalized = normalize_text(name)
    if len(normalized) < 2:
        return False, "name_too_short"
    return True, ""


def validate_contact(phone: str, telegram_username: str) -> tuple[bool, str]:
    normalized_phone = normalize_phone(phone) if phone else ""
    normalized_tg = normalize_telegram_username(telegram_username) if telegram_username else ""

    if not normalized_phone and not normalized_tg:
        return False, "contact_required"
    if normalized_phone and not PHONE_RE.fullmatch(normalized_phone):
        return False, "phone_invalid"
    if normalized_tg and not TG_RE.fullmatch(normalized_tg):
        return False, "telegram_invalid"
    return True, ""


def validate_request(request_text: str) -> tuple[bool, str]:
    normalized = normalize_text(request_text)
    if len(normalized) < 5:
        return False, "request_too_short"
    return True, ""
