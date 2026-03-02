from __future__ import annotations

import time
from dataclasses import dataclass, field

from domain import LeadDraft


STEPS = ("name", "contact", "request", "confirm")


@dataclass
class Session:
    chat_id: int
    step: str = "name"
    draft: LeadDraft = field(default_factory=lambda: LeadDraft(source_user_id=""))
    offscript_count: int = 0
    updated_at: float = field(default_factory=time.time)


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[int, Session] = {}

    def get_or_create(self, chat_id: int, source_user_id: str, source_username: str) -> Session:
        existing = self._sessions.get(chat_id)
        if existing:
            return existing

        created = Session(
            chat_id=chat_id,
            step="name",
            draft=LeadDraft(source_user_id=source_user_id, source_username=source_username),
        )
        self._sessions[chat_id] = created
        return created

    def save(self, session: Session) -> None:
        session.updated_at = time.time()
        self._sessions[session.chat_id] = session

    def reset(self, chat_id: int, source_user_id: str, source_username: str) -> Session:
        reset = Session(
            chat_id=chat_id,
            step="name",
            draft=LeadDraft(source_user_id=source_user_id, source_username=source_username),
        )
        self._sessions[chat_id] = reset
        return reset
