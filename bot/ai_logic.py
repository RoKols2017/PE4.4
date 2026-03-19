from __future__ import annotations

import logging

from openai import OpenAI


LOGGER = logging.getLogger(__name__)


SYSTEM_PROMPT = (
    "Ты AI-ассистент для сбора заявок в сервисе digital-услуг. "
    "Стиль: дружелюбный и деловой, 1-2 коротких предложения. "
    "Никогда не выдумывай данные за пользователя и не меняй его ввод. "
    "Если пользователь отклоняется от сценария, мягко верни к текущему шагу. "
    "Сценарий: имя -> контакт (телефон или Telegram username) -> суть запроса -> подтверждение. "
    "Если имя введено как фраза ('я Вовочка', 'меня зовут Анна'), попроси ввести только имя. "
    "Если вместо контакта прислали описание задачи, попроси именно контакт. "
    "Если вместо запроса прислали контакт, попроси коротко описать задачу. "
    "Пиши по-русски, без лишних деталей."
)

STEP_HINTS = {
    "name": "Запроси только имя пользователя.",
    "contact": "Запроси только один контакт: телефон или Telegram username.",
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
    "telegram_invalid": "Telegram username невалиден.",
    "request_too_short": "Запрос слишком короткий.",
    "request_looks_like_contact": "Пользователь прислал контакт вместо описания запроса.",
    "confirm_expected": "Ожидается подтверждение 'да' или 'нет'.",
}


def generate_reply(
    client: OpenAI,
    model: str,
    current_step: str,
    collected: dict,
    user_text: str,
    validation_hint: str,
) -> str:
    step_hint = STEP_HINTS.get(current_step, "Верни пользователя к текущему шагу.")
    hint_text = VALIDATION_HINTS.get(validation_hint, validation_hint or "")
    prompt = (
        f"Текущий шаг: {current_step}\n"
        f"Инструкция шага: {step_hint}\n"
        f"Собранные поля: {collected}\n"
        f"Сообщение пользователя: {user_text}\n"
        f"Подсказка валидации: {hint_text}\n\n"
        "Сформируй один ответ ассистента."
    )

    LOGGER.debug(
        "[ai_logic.generate_reply] Sending prompt to model",
        extra={"step": current_step, "validation_hint": validation_hint},
    )

    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )

    text = response.output_text.strip()
    LOGGER.debug("[ai_logic.generate_reply] Model response received")
    return text or "Продолжим, пожалуйста. Уточните ответ по текущему шагу."


class AssistantAI:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def reply(self, current_step: str, collected: dict, user_text: str, validation_hint: str) -> str:
        try:
            LOGGER.debug(
                "[AssistantAI.reply] Generating reply",
                extra={"step": current_step, "hint": validation_hint},
            )
            return generate_reply(
                client=self._client,
                model=self._model,
                current_step=current_step,
                collected=collected,
                user_text=user_text,
                validation_hint=validation_hint,
            )
        except Exception as error:  # noqa: BLE001
            LOGGER.error("[AssistantAI.reply] OpenAI call failed: %s", error)
            return self.fallback(current_step)

    @staticmethod
    def fallback(step: str) -> str:
        if step == "name":
            return "Как вас зовут?"
        if step == "contact":
            return "Оставьте контакт: телефон (+79991234567) или Telegram username (@example)."
        if step == "request":
            return "Опишите, пожалуйста, ваш запрос коротко в одном-двух предложениях."
        return "Подтвердите отправку: напишите 'да' или 'нет'."
