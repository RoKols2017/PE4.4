from runtime_policy import CandidateFields, StructuredAIResponse
from session import Session

from bot import _advance_or_retry


class StubAI:
    def respond(self, **kwargs):  # noqa: ANN003
        step = kwargs["current_step"]
        validation_result = kwargs["validation_result"]
        return StructuredAIResponse(
            detected_intent="clarify",
            candidate_fields=CandidateFields(),
            needs_clarification=True,
            user_facing_message=f"retry:{step}:{validation_result}",
            used_fallback=True,
            fallback_reason="stub",
        )


def make_session() -> Session:
    return Session(chat_id=1)


def test_name_step_without_mixed_intent_only_advances_to_contact() -> None:
    session = make_session()
    message, advanced = _advance_or_retry(
        session=session,
        ai=StubAI(),
        user_text="Константин",
        source_username="rom_vash",
        policy_response=StructuredAIResponse(
            detected_intent="answer_current_step",
            candidate_fields=CandidateFields(name="Константин", request="разработка бота"),
            needs_clarification=False,
            user_facing_message="ok",
        ),
        correlation_id="1",
    )

    assert advanced is True
    assert session.step == "contact"
    assert session.draft.name == "Константин"
    assert session.draft.request == ""
    assert "контакт" in message.lower()


def test_mixed_input_does_not_fallback_to_profile_username_as_contact() -> None:
    session = make_session()
    message, advanced = _advance_or_retry(
        session=session,
        ai=StubAI(),
        user_text="я Константин, мой email hut@gamil.com, хочу телеграм-бота",
        source_username="rom_vash",
        policy_response=StructuredAIResponse(
            detected_intent="mixed_input",
            candidate_fields=CandidateFields(name="Константин", contact=None, request="хочу телеграм-бота"),
            needs_clarification=False,
            user_facing_message="ok",
        ),
        correlation_id="1",
    )

    assert advanced is False
    assert session.step == "contact"
    assert session.draft.name == "Константин"
    assert session.draft.telegram_username == ""
    assert "contact_required" in session.qa_flags or "contact_looks_like_text" in session.qa_flags
    assert message.startswith("retry:contact:")
