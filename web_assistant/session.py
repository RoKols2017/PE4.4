from __future__ import annotations

import time
from dataclasses import dataclass, field

from domain import LeadDraft


@dataclass
class SessionState:
    session_id: str
    step: str = "name"
    draft: LeadDraft = field(default_factory=lambda: LeadDraft(source_user_id=""))
    updated_at: float = field(default_factory=time.time)
    offscript_count: int = 0
    qa_flags: list[str] = field(default_factory=list)
    last_user_message: str = ""
    last_validation_result: str = ""
    confirm_edit_target: str = ""
    accepted_candidate_fields: list[str] = field(default_factory=list)


class SessionStore:
    def __init__(self) -> None:
        self._states: dict[str, SessionState] = {}

    def get_or_create(self, session_id: str) -> SessionState:
        existing = self._states.get(session_id)
        if existing is not None:
            return existing
        created = SessionState(session_id=session_id, draft=LeadDraft(source_user_id=session_id))
        self._states[session_id] = created
        return created

    def save(self, state: SessionState) -> None:
        state.updated_at = time.time()
        self._states[state.session_id] = state

    def reset(self, session_id: str) -> SessionState:
        state = SessionState(session_id=session_id, draft=LeadDraft(source_user_id=session_id))
        self._states[session_id] = state
        return state
