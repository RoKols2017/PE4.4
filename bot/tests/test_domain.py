from domain import normalize_name, parse_contact, validate_contact, validate_name, validate_request


def test_validate_name_rejects_short() -> None:
    ok, code = validate_name("A")
    assert ok is False
    assert code == "name_too_short"


def test_normalize_name_strips_intro_phrase() -> None:
    assert normalize_name("я Вовочка") == "Вовочка"


def test_validate_name_rejects_request_like_text() -> None:
    ok, code = validate_name("Хочу заказать телеграм бота")
    assert ok is False
    assert code == "name_looks_like_request"


def test_parse_contact_phone() -> None:
    phone, tg = parse_contact("+7 999 123 45 67")
    assert phone == "+79991234567"
    assert tg == ""


def test_validate_contact_accepts_telegram() -> None:
    ok, code = validate_contact("", "@valid_user")
    assert ok is True
    assert code == ""


def test_validate_contact_text_hint_when_request_instead_of_contact() -> None:
    ok, code = validate_contact("", "", raw_text="Хочу заказать лендинг")
    assert ok is False
    assert code == "contact_looks_like_text"


def test_validate_request_rejects_short() -> None:
    ok, code = validate_request("abc")
    assert ok is False
    assert code == "request_too_short"


def test_validate_request_rejects_contact_like_text() -> None:
    ok, code = validate_request("+79990001122")
    assert ok is False
    assert code == "request_looks_like_contact"
