from session import SessionStore


def test_session_store_lifecycle() -> None:
    store = SessionStore()
    state = store.get_or_create("s1")
    assert state.step == "name"

    state.step = "request"
    state.qa_flags.append("name_too_short")
    store.save(state)
    loaded = store.get_or_create("s1")
    assert loaded.step == "request"
    assert loaded.qa_flags == ["name_too_short"]

    reset = store.reset("s1")
    assert reset.step == "name"
    assert reset.qa_flags == []
