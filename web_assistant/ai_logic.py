from __future__ import annotations

import logging

from openai import OpenAI


LOGGER = logging.getLogger(__name__)


SYSTEM_PROMPT = (
    "Ты ассистент сайта для приема заявок на digital-услуги. "
    "Стиль: вежливый, деловой, краткий, 1-2 предложения. "
    "Не уходи в продажи, не выдумывай данные и не подменяй поля. "
    "Сценарий: имя -> контакт (телефон или email) -> суть запроса -> подтверждение. "
    "Если пользователь отклоняется от сценария, мягко верни к текущему шагу. "
    "Если имя введено как фраза ('я Вовочка', 'меня зовут Анна'), попроси ввести только имя. "
    "Если вместо контакта пришел текст запроса, попроси именно контакт. "
    "Если вместо запроса пришел контакт, попроси коротко описать задачу."
)

STEP_HINTS = {
    "name": "Запроси только имя пользователя.",
    "contact": "Запроси только один контакт: телефон или email.",
    "request": "Запроси краткую суть запроса пользователя.",
    "confirm": "Попроси подтвердить отправку словом 'да' или начать заново словом 'нет'.",
}

VALIDATION_HINTS = {
    "name_required": "Пользователь не ввел имя.",
    "name_too_short": "Имя слишком короткое.",
    "name_looks_like_contact": "Вместо имени пользователь прислал контакт.",
    "name_invalid_chars": "Имя содержит лишние символы.",
    "contact_required": "Контакт не распознан.",
    "contact_looks_like_text": "Пользователь прислал текст запроса вместо контакта.",
    "phone_invalid": "Телефон невалиден.",
    "email_invalid": "Email невалиден.",
    "request_too_short": "Запрос слишком короткий.",
    "request_looks_like_contact": "Пользователь прислал контакт вместо описания запроса.",
    "confirm_expected": "Ожидается подтверждение 'да' или 'нет'.",
}


class AssistantAI:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def reply(self, step: str, draft: dict, user_text: str, validation_hint: str) -> str:
        try:
            step_hint = STEP_HINTS.get(step, "Верни пользователя к текущему шагу.")
            hint_text = VALIDATION_HINTS.get(validation_hint, validation_hint or "")
            LOGGER.debug(
                "[web_assistant.ai] Generating response",
                extra={"step": step, "validation_hint": validation_hint},
            )
            response = self._client.responses.create(
                model=self._model,
                input=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": (
                            f"Current step: {step}\n"
                            f"Step hint: {step_hint}\n"
                            f"Draft: {draft}\n"
                            f"User: {user_text}\n"
                            f"Validation hint: {hint_text}\n"
                            "Ответь одной репликой ассистента на русском языке."
                        ),
                    },
                ],
            )
            LOGGER.info("[web_assistant.ai] Model response success", extra={"step": step})
            text = response.output_text.strip()
            return text or self.fallback(step)
        except Exception as error:  # noqa: BLE001
            LOGGER.error("[web_assistant.ai] Model call failed: %s", error)
            LOGGER.warning("[web_assistant.ai] Fallback activated", extra={"step": step})
            return self.fallback(step)

    @staticmethod
    def fallback(step: str) -> str:
        if step == "name":
            return "Подскажите, пожалуйста, как вас зовут?"
        if step == "contact":
            return "Оставьте контакт: телефон (+79991234567) или email (example@domain.com)."
        if step == "request":
            return "Кратко опишите, пожалуйста, ваш запрос."
        return "Подтвердите отправку заявки: напишите 'да' или 'нет'."
