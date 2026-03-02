from domain import parse_contact, validate_contact, validate_name, validate_request


def test_validate_name_rejects_short() -> None:
    ok, code = validate_name("A")
    assert ok is False
    assert code == "name_too_short"


def test_parse_contact_phone() -> None:
    phone, tg = parse_contact("+7 999 123 45 67")
    assert phone == "+79991234567"
    assert tg == ""


def test_validate_contact_accepts_telegram() -> None:
    ok, code = validate_contact("", "@valid_user")
    assert ok is True
    assert code == ""


def test_validate_request_rejects_short() -> None:
    ok, code = validate_request("abc")
    assert ok is False
    assert code == "request_too_short"
