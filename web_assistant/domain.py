from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol


PHONE_RE = re.compile(r"^\+?[0-9]{10,15}$")
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
NAME_RE = re.compile(r"^[A-Za-zА-Яа-яЁёІіЇїЄє'\- ]+$")
INTRO_PREFIX_RE = re.compile(
    r"^(?:я|это|меня\s+зовут|зовут|my\s+name\s+is|i\s+am|i['’]m)\s+",
    re.IGNORECASE,
)


@dataclass
class LeadDraft:
    source_user_id: str
    name: str = ""
    phone: str = ""
    email: str = ""
    request: str = ""


@dataclass(frozen=True)
class LeadListItem:
    lead_id: str
    source: str
    name: str
    phone: str
    email: str
    request: str
    status: str
    created_at_utc: str


class LeadRepository(Protocol):
    def ensure_schema(self) -> None:
        ...

    def save_website_lead(
        self,
        lead_id: str,
        draft: LeadDraft,
        session_id: str,
        quality_payload: dict | None = None,
    ) -> None:
        ...

    def list_leads(self, limit: int, offset: int, source: str | None = None) -> tuple[list[LeadListItem], int]:
        ...


def normalize_text(value: str) -> str:
    return " ".join(value.strip().split())


def normalize_name(value: str) -> str:
    normalized = normalize_text(value)
    stripped = INTRO_PREFIX_RE.sub("", normalized).strip(" .,!?:;\"'()[]{}")
    return normalize_text(stripped)


def normalize_phone(value: str) -> str:
    return re.sub(r"\s+", "", value.strip())


def normalize_email(value: str) -> str:
    return value.strip().lower()


def _looks_like_request_text(value: str) -> bool:
    cleaned = normalize_text(value)
    if len(cleaned.split()) >= 3:
        return True
    lowered = cleaned.lower()
    keywords = ("хочу", "нужно", "интересует", "тест", "заказать", "помощь", "консульта")
    return any(token in lowered for token in keywords)


def validate_name(value: str) -> tuple[bool, str]:
    normalized = normalize_name(value)
    if not normalized:
        return False, "name_required"
    phone, email = parse_contact(normalized)
    if phone or email:
        return False, "name_looks_like_contact"
    if _looks_like_request_text(normalized):
        return False, "name_looks_like_request"
    if len(normalized) < 2:
        return False, "name_too_short"
    if not NAME_RE.fullmatch(normalized):
        return False, "name_invalid_chars"
    return True, ""


def parse_contact(value: str) -> tuple[str, str]:
    text = normalize_text(value)
    phone = normalize_phone(text)
    email = normalize_email(text)
    if PHONE_RE.fullmatch(phone):
        return phone, ""
    if EMAIL_RE.fullmatch(email):
        return "", email
    return "", ""


def validate_contact(phone: str, email: str, raw_text: str = "") -> tuple[bool, str]:
    p = normalize_phone(phone) if phone else ""
    e = normalize_email(email) if email else ""
    if not p and not e:
        if raw_text and _looks_like_request_text(raw_text):
            return False, "contact_looks_like_text"
        return False, "contact_required"
    if p and not PHONE_RE.fullmatch(p):
        return False, "phone_invalid"
    if e and not EMAIL_RE.fullmatch(e):
        return False, "email_invalid"
    return True, ""


def validate_request(value: str) -> tuple[bool, str]:
    normalized = normalize_text(value)
    phone, email = parse_contact(normalized)
    if phone or email:
        return False, "request_looks_like_contact"
    if len(normalized) < 5:
        return False, "request_too_short"
    return True, ""
