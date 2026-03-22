from __future__ import annotations

import json
from dataclasses import asdict, dataclass


ALLOWED_INTENTS = (
    "answer_current_step",
    "edit_name",
    "edit_contact",
    "edit_request",
    "mixed_input",
    "clarify",
    "confirm_yes",
    "confirm_no",
    "unknown",
)

FALLBACK_REASON_MODEL_CALL_FAILED = "model_call_failed"
FALLBACK_REASON_INTENT_NOT_ALLOWED = "intent_not_allowed"

STEP_BASE_MESSAGES = {
    "name": "Подскажите, как к вам обращаться?",
    "contact": "Оставьте, пожалуйста, контакт.",
    "request": "Коротко опишите задачу.",
    "confirm": "Проверьте данные и подтвердите отправку или выберите поле для правки.",
}

EXPECTED_TOP_LEVEL_KEYS = {
    "detected_intent",
    "candidate_fields",
    "needs_clarification",
    "user_facing_message",
}

VALIDATION_EXPLANATIONS = {
    "name_required": "Нужно только имя, без лишних пояснений.",
    "name_too_short": "Имя получилось слишком коротким.",
    "name_looks_like_contact": "Это похоже на контакт, а здесь нужно имя.",
    "name_looks_like_request": "Это похоже на описание задачи, а здесь нужно имя.",
    "name_invalid_chars": "В имени есть лишние символы.",
    "contact_required": "Нужен контакт, чтобы мы могли связаться.",
    "contact_looks_like_text": "Это похоже на описание задачи, а здесь нужен контакт.",
    "phone_invalid": "Телефон не распознался.",
    "telegram_invalid": "Telegram username не распознался.",
    "request_too_short": "Пока не хватает деталей по задаче.",
    "request_looks_like_contact": "Это похоже на контакт, а здесь нужно описание задачи.",
    "confirm_expected": "Можно подтвердить отправку или выбрать поле для правки.",
}

RETRY_EXAMPLES = {
    "name": "Например: Иван.",
    "contact": "Например: +79991234567 или @example.",
    "request": "Например: нужен лендинг для студии.",
    "confirm": "Можно написать: отправляй, исправь имя, исправь контакт или исправь задачу.",
}


@dataclass(frozen=True)
class CandidateFields:
    name: str | None = None
    contact: str | None = None
    request: str | None = None


@dataclass(frozen=True)
class StructuredAIResponse:
    detected_intent: str
    candidate_fields: CandidateFields
    needs_clarification: bool
    user_facing_message: str
    used_fallback: bool = False
    fallback_reason: str = ""


@dataclass(frozen=True)
class ResponsePolicyInput:
    current_step: str
    known_fields: dict
    validation_result: str
    offscript_count: int
    last_user_message: str


def allowed_intents_for_step(step: str) -> tuple[str, ...]:
    common = ("answer_current_step", "mixed_input", "clarify", "unknown")
    if step == "confirm":
        return common + ("edit_name", "edit_contact", "edit_request", "confirm_yes", "confirm_no")
    return common


def deterministic_message(step: str, validation_result: str = "") -> str:
    reason = VALIDATION_EXPLANATIONS.get(validation_result, "")
    base = STEP_BASE_MESSAGES.get(step, STEP_BASE_MESSAGES["confirm"])

    example = RETRY_EXAMPLES.get(step, "")
    parts = [base]
    if reason:
        parts.append(reason)
    if example:
        parts.append(example)
    return " ".join(part for part in parts if part)


def fallback_response(step: str, validation_result: str = "", reason: str = "") -> StructuredAIResponse:
    intent = "clarify" if validation_result else "answer_current_step"
    if step == "confirm" and validation_result == "confirm_expected":
        intent = "clarify"
    return StructuredAIResponse(
        detected_intent=intent,
        candidate_fields=CandidateFields(),
        needs_clarification=bool(validation_result) or step == "confirm",
        user_facing_message=deterministic_message(step, validation_result),
        used_fallback=True,
        fallback_reason=reason,
    )


def build_invalid_intent_reason(intent: str) -> str:
    return f"{FALLBACK_REASON_INTENT_NOT_ALLOWED}:{intent}"


def build_system_prompt(contact_label: str) -> str:
    intents = ", ".join(ALLOWED_INTENTS)
    return (
        "Ты помогаешь backend FSM собирать заявку. "
        "Не управляй шагами, не подтверждай сохранение, не выдумывай данные. "
        f"Допустимые intent: {intents}. "
        "Верни только JSON по схеме без markdown. "
        f"Поле contact содержит один кандидат-контакт ({contact_label})."
    )


def build_user_prompt(policy_input: ResponsePolicyInput, contact_label: str) -> str:
    allowed = ", ".join(allowed_intents_for_step(policy_input.current_step))
    payload = {
        "current_step": policy_input.current_step,
        "known_fields": policy_input.known_fields,
        "validation_result": policy_input.validation_result or "none",
        "offscript_count": policy_input.offscript_count,
        "last_user_message": policy_input.last_user_message,
        "allowed_intents": allowed,
        "contact_format": contact_label,
        "required_schema": {
            "detected_intent": "string",
            "candidate_fields": {
                "name": "string|null",
                "contact": "string|null",
                "request": "string|null",
            },
            "needs_clarification": True,
            "user_facing_message": "string",
        },
    }
    return json.dumps(payload, ensure_ascii=False)


def parse_structured_response(raw_text: str) -> StructuredAIResponse:
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json\n", "", 1).strip()
    data = json.loads(cleaned)
    if not isinstance(data, dict):
        raise ValueError("top-level payload must be object")
    if set(data.keys()) != EXPECTED_TOP_LEVEL_KEYS:
        raise ValueError("unexpected top-level keys")

    intent = data["detected_intent"]
    if intent not in ALLOWED_INTENTS:
        raise ValueError("unknown intent")

    fields = data["candidate_fields"]
    if not isinstance(fields, dict):
        raise ValueError("candidate_fields must be object")

    normalized_fields: dict[str, str | None] = {}
    for key in ("name", "contact", "request"):
        value = fields.get(key)
        if value is not None and not isinstance(value, str):
            raise ValueError(f"candidate field {key} must be string or null")
        normalized_fields[key] = value.strip() if isinstance(value, str) and value.strip() else None

    if set(fields.keys()) != {"name", "contact", "request"}:
        raise ValueError("unexpected candidate_fields keys")

    clarification = data["needs_clarification"]
    if not isinstance(clarification, bool):
        raise ValueError("needs_clarification must be boolean")

    message = data["user_facing_message"]
    if not isinstance(message, str):
        raise ValueError("user_facing_message must be string")
    message = " ".join(message.strip().split())
    if not message:
        raise ValueError("user_facing_message is empty")

    return StructuredAIResponse(
        detected_intent=intent,
        candidate_fields=CandidateFields(**normalized_fields),
        needs_clarification=clarification,
        user_facing_message=message,
    )


def resolve_response_policy(policy_input: ResponsePolicyInput, response: StructuredAIResponse) -> StructuredAIResponse:
    allowed = allowed_intents_for_step(policy_input.current_step)
    if response.detected_intent not in allowed:
        return fallback_response(
            policy_input.current_step,
            policy_input.validation_result,
            reason=build_invalid_intent_reason(response.detected_intent),
        )
    return response


def response_to_dict(response: StructuredAIResponse) -> dict:
    return {
        "detected_intent": response.detected_intent,
        "candidate_fields": asdict(response.candidate_fields),
        "needs_clarification": response.needs_clarification,
        "user_facing_message": response.user_facing_message,
        "used_fallback": response.used_fallback,
        "fallback_reason": response.fallback_reason,
    }
