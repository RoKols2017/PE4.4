from __future__ import annotations

import logging

from openai import OpenAI


LOGGER = logging.getLogger(__name__)


SYSTEM_PROMPT = (
    "Ты AI-ассистент для сбора заявок. "
    "Стиль: дружелюбный и деловой. "
    "Не выдумывай данные за пользователя. "
    "Если пользователь уходит от сценария, мягко верни к текущему шагу сбора. "
    "Текущий сценарий: имя -> контакт (телефон или Telegram username) -> суть запроса. "
    "Пиши кратко, по делу, на русском языке."
)

STEP_HINTS = {
    "name": "Запроси только имя пользователя.",
    "contact": "Запроси только один контакт: телефон или Telegram username.",
    "request": "Запроси краткую суть запроса пользователя.",
    "confirm": "Попроси подтвердить отправку словом 'да' или начать заново словом 'нет'.",
}


def generate_reply(
    client: OpenAI,
    model: str,
    current_step: str,
    collected: dict,
    user_text: str,
    validation_hint: str,
) -> str:
    prompt = (
        f"Текущий шаг: {current_step}\n"
        f"Собранные поля: {collected}\n"
        f"Сообщение пользователя: {user_text}\n"
        f"Подсказка валидации: {validation_hint}\n\n"
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
