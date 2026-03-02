from session import SessionStore


def test_session_store_reset_and_get() -> None:
    store = SessionStore()
    first = store.get_or_create(chat_id=1, source_user_id="1", source_username="user1")
    assert first.step == "name"
    assert first.draft.source_user_id == "1"

    first.step = "request"
    store.save(first)

    loaded = store.get_or_create(chat_id=1, source_user_id="1", source_username="user1")
    assert loaded.step == "request"

    reset = store.reset(chat_id=1, source_user_id="1", source_username="user1")
    assert reset.step == "name"
