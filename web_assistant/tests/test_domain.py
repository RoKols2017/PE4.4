from domain import parse_contact, validate_contact, validate_name, validate_request


def test_validate_name_short() -> None:
    ok, code = validate_name("A")
    assert ok is False
    assert code == "name_too_short"


def test_parse_contact_email() -> None:
    phone, email = parse_contact("User@Example.com")
    assert phone == ""
    assert email == "user@example.com"


def test_validate_contact_requires_any() -> None:
    ok, code = validate_contact("", "")
    assert ok is False
    assert code == "contact_required"


def test_validate_request_short() -> None:
    ok, code = validate_request("abc")
    assert ok is False
    assert code == "request_too_short"
