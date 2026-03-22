import pytest

from runtime_policy import parse_structured_response, resolve_response_policy, ResponsePolicyInput


def test_parse_structured_response_accepts_valid_payload() -> None:
    payload = (
        '{"detected_intent":"answer_current_step","candidate_fields":{"name":"Иван","contact":null,'
        '"request":null},"needs_clarification":false,"user_facing_message":"Принял."}'
    )
    parsed = parse_structured_response(payload)
    assert parsed.detected_intent == "answer_current_step"
    assert parsed.candidate_fields.name == "Иван"


def test_parse_structured_response_rejects_unknown_intent() -> None:
    payload = (
        '{"detected_intent":"bad_intent","candidate_fields":{"name":null,"contact":null,'
        '"request":null},"needs_clarification":false,"user_facing_message":"Принял."}'
    )
    with pytest.raises(ValueError):
        parse_structured_response(payload)


def test_resolve_response_policy_falls_back_for_disallowed_confirm_intent() -> None:
    parsed = parse_structured_response(
        '{"detected_intent":"confirm_yes","candidate_fields":{"name":null,"contact":null,"request":null},'
        '"needs_clarification":false,"user_facing_message":"Отправляю."}'
    )
    resolved = resolve_response_policy(
        ResponsePolicyInput(
            current_step="request",
            known_fields={},
            validation_result="",
            offscript_count=0,
            last_user_message="да",
        ),
        parsed,
    )
    assert resolved.used_fallback is True
