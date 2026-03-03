from session import SessionStore


def test_session_store_lifecycle() -> None:
    store = SessionStore()
    state = store.get_or_create("s1")
    assert state.step == "name"

    state.step = "request"
    store.save(state)
    loaded = store.get_or_create("s1")
    assert loaded.step == "request"

    reset = store.reset("s1")
    assert reset.step == "name"
