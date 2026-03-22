from domain import normalize_name, parse_contact, validate_contact, validate_name, validate_request


def test_validate_name_short() -> None:
    ok, code = validate_name("A")
    assert ok is False
    assert code == "name_too_short"


def test_normalize_name_strips_intro_phrase() -> None:
    assert normalize_name("меня зовут Анна") == "Анна"


def test_parse_contact_email() -> None:
    phone, email = parse_contact("User@Example.com")
    assert phone == ""
    assert email == "user@example.com"


def test_validate_contact_requires_any() -> None:
    ok, code = validate_contact("", "")
    assert ok is False
    assert code == "contact_required"


def test_validate_contact_detects_request_text() -> None:
    ok, code = validate_contact("", "", raw_text="Хочу заказать лендинг")
    assert ok is False
    assert code == "contact_looks_like_text"


def test_validate_name_rejects_request_like_text() -> None:
    ok, code = validate_name("Хочу заказать лендинг")
    assert ok is False
    assert code == "name_looks_like_request"


def test_validate_request_short() -> None:
    ok, code = validate_request("abc")
    assert ok is False
    assert code == "request_too_short"


def test_validate_request_rejects_contact_like_text() -> None:
    ok, code = validate_request("user@example.com")
    assert ok is False
    assert code == "request_looks_like_contact"
