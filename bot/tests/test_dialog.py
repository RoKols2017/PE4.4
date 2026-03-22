from session import SessionStore


def test_session_store_reset_and_get() -> None:
    store = SessionStore()
    first = store.get_or_create(chat_id=1, source_user_id="1", source_username="user1")
    assert first.step == "name"
    assert first.draft.source_user_id == "1"

    first.step = "request"
    first.qa_flags.append("name_too_short")
    store.save(first)

    loaded = store.get_or_create(chat_id=1, source_user_id="1", source_username="user1")
    assert loaded.step == "request"
    assert loaded.qa_flags == ["name_too_short"]

    loaded.last_user_message = "Привет"
    loaded.last_validation_result = "request_too_short"
    loaded.confirm_edit_target = "contact"
    loaded.accepted_candidate_fields.append("name")
    store.save(loaded)

    enriched = store.get_or_create(chat_id=1, source_user_id="1", source_username="user1")
    assert enriched.last_user_message == "Привет"
    assert enriched.last_validation_result == "request_too_short"
    assert enriched.confirm_edit_target == "contact"
    assert enriched.accepted_candidate_fields == ["name"]

    reset = store.reset(chat_id=1, source_user_id="1", source_username="user1")
    assert reset.step == "name"
    assert reset.qa_flags == []
    assert reset.confirm_edit_target == ""
