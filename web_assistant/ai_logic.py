from __future__ import annotations

import logging

from openai import OpenAI


LOGGER = logging.getLogger(__name__)


SYSTEM_PROMPT = (
    "Ты ассистент сайта для приема заявок. "
    "Стиль: вежливый, деловой, краткий. "
    "Не уходи в продажи и не выдумывай данные. "
    "Если пользователь отклоняется от сценария, мягко верни к текущему шагу."
)


class AssistantAI:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def reply(self, step: str, draft: dict, user_text: str, validation_hint: str) -> str:
        try:
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
                            f"Draft: {draft}\n"
                            f"User: {user_text}\n"
                            f"Validation hint: {validation_hint}\n"
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
