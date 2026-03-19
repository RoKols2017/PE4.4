from __future__ import annotations

import logging
import uuid

import telebot

from ai_logic import AssistantAI
from config import load_settings
from domain import (
    LeadRepository,
    normalize_name,
    parse_contact,
    validate_contact,
    validate_name,
    validate_request,
)
from postgres_repository import PostgresLeadRepository, build_lead_record
from session import SessionStore


LOGGER = logging.getLogger(__name__)


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def build_step_prompt(step: str) -> str:
    if step == "name":
        return "Как вас зовут?"
    if step == "contact":
        return "Укажите контакт: телефон (+79991234567) или Telegram username (@example)."
    if step == "request":
        return "Кратко опишите суть вашего запроса."
    return "Подтвердите отправку: напишите 'да' или 'нет'."


def build_retry_prompt(step: str, code: str) -> str:
    if step == "name":
        return "Укажите только имя, например: Иван."
    if step == "contact":
        return "Укажите только контакт, например: +79991234567 или @example."
    if step == "request":
        return "Коротко опишите запрос, например: Нужен лендинг для студии."
    if step == "confirm":
        return "Ответьте одним словом: да или нет."
    return f"Уточните ответ по шагу ({code})."


def main() -> None:
    settings = load_settings()
    configure_logging(settings.log_level)

    LOGGER.info("[bot.main] Starting telegram bot")
    LOGGER.debug(
        "[bot.main] Runtime config",
        extra={
            "openai_model": settings.openai_model,
            "storage_backend": "postgres",
            "poll_interval_seconds": settings.poll_interval_seconds,
            "max_retry_attempts": settings.max_retry_attempts,
        },
    )

    lead_repo: LeadRepository = PostgresLeadRepository(
        database_url=settings.database_url,
        local_timezone=settings.local_timezone,
        max_retry_attempts=settings.max_retry_attempts,
        retry_delay_seconds=settings.retry_delay_seconds,
        connect_timeout_seconds=settings.db_connect_timeout_seconds,
    )
    lead_repo.ensure_schema()

    ai = AssistantAI(api_key=settings.openai_api_key, model=settings.openai_model)
    sessions = SessionStore()
    bot = telebot.TeleBot(settings.telegram_bot_token)

    @bot.message_handler(commands=["start"])
    def start_handler(message: telebot.types.Message) -> None:
        chat_id = message.chat.id
        user_id = str(message.from_user.id) if message.from_user else str(chat_id)
        source_username = message.from_user.username if message.from_user else ""
        sessions.reset(chat_id=chat_id, source_user_id=user_id, source_username=source_username or "")
        LOGGER.info("[bot.start_handler] Session reset", extra={"chat_id": chat_id})
        bot.send_message(
            chat_id,
            "Здравствуйте! Я помогу оформить заявку. Соберем 3 поля: имя, контакт и ваш запрос.",
        )
        bot.send_message(chat_id, build_step_prompt("name"))

    @bot.message_handler(commands=["new"])
    def reset_handler(message: telebot.types.Message) -> None:
        chat_id = message.chat.id
        user_id = str(message.from_user.id) if message.from_user else str(chat_id)
        source_username = message.from_user.username if message.from_user else ""
        sessions.reset(chat_id=chat_id, source_user_id=user_id, source_username=source_username or "")
        LOGGER.info("[bot.reset_handler] Session reset by /new", extra={"chat_id": chat_id})
        bot.send_message(chat_id, "Начинаем заново. Давайте соберем заявку по шагам.")
        bot.send_message(chat_id, build_step_prompt("name"))

    @bot.message_handler(func=lambda _: True)
    def text_handler(message: telebot.types.Message) -> None:
        text = (message.text or "").strip()
        if not text:
            return

        chat_id = message.chat.id
        user_id = str(message.from_user.id) if message.from_user else str(chat_id)
        source_username = message.from_user.username if message.from_user else ""
        session = sessions.get_or_create(chat_id, source_user_id=user_id, source_username=source_username or "")

        LOGGER.debug(
            "[bot.text_handler] Message received",
            extra={"chat_id": chat_id, "step": session.step},
        )

        try:
            if session.step == "name":
                ok, code = validate_name(text)
                if not ok:
                    session.offscript_count += 1
                    session.qa_flags.append(code)
                    sessions.save(session)
                    LOGGER.warning("[bot.text_handler] Name validation failed", extra={"chat_id": chat_id, "code": code})
                    answer = ai.reply(session.step, session.draft.__dict__, text, code)
                    answer = f"{answer}\n\n{build_retry_prompt(session.step, code)}"
                    bot.send_message(chat_id, answer)
                    return

                session.draft.name = normalize_name(text)
                session.step = "contact"
                session.offscript_count = 0
                sessions.save(session)
                LOGGER.info("[bot.text_handler] Step transition", extra={"chat_id": chat_id, "to": "contact"})
                bot.send_message(chat_id, build_step_prompt("contact"))
                return

            if session.step == "contact":
                phone, tg = parse_contact(text)
                if not phone and not tg and source_username:
                    tg = source_username

                ok, code = validate_contact(phone, tg, raw_text=text)
                if not ok:
                    session.offscript_count += 1
                    session.qa_flags.append(code)
                    sessions.save(session)
                    LOGGER.warning(
                        "[bot.text_handler] Contact validation failed",
                        extra={"chat_id": chat_id, "code": code},
                    )
                    answer = ai.reply(session.step, session.draft.__dict__, text, code)
                    answer = f"{answer}\n\n{build_retry_prompt(session.step, code)}"
                    bot.send_message(chat_id, answer)
                    return

                session.draft.phone = phone
                session.draft.telegram_username = tg
                session.step = "request"
                session.offscript_count = 0
                sessions.save(session)
                LOGGER.info("[bot.text_handler] Step transition", extra={"chat_id": chat_id, "to": "request"})
                bot.send_message(chat_id, build_step_prompt("request"))
                return

            if session.step == "request":
                ok, code = validate_request(text)
                if not ok:
                    session.offscript_count += 1
                    session.qa_flags.append(code)
                    sessions.save(session)
                    LOGGER.warning("[bot.text_handler] Request validation failed", extra={"chat_id": chat_id, "code": code})
                    answer = ai.reply(session.step, session.draft.__dict__, text, code)
                    answer = f"{answer}\n\n{build_retry_prompt(session.step, code)}"
                    bot.send_message(chat_id, answer)
                    return

                session.draft.request = " ".join(text.split())
                session.step = "confirm"
                session.offscript_count = 0
                sessions.save(session)
                LOGGER.info("[bot.text_handler] Step transition", extra={"chat_id": chat_id, "to": "confirm"})
                summary = (
                    f"Проверьте данные:\n"
                    f"Имя: {session.draft.name}\n"
                    f"Телефон: {session.draft.phone or '-'}\n"
                    f"Telegram: {'@' + session.draft.telegram_username if session.draft.telegram_username else '-'}\n"
                    f"Запрос: {session.draft.request}\n\n"
                    "Подтверждаете отправку? (да/нет)"
                )
                bot.send_message(chat_id, summary)
                return

            lower = text.lower()
            if lower == "нет":
                sessions.reset(chat_id, source_user_id=user_id, source_username=source_username or "")
                LOGGER.warning("[bot.text_handler] User restarted flow", extra={"chat_id": chat_id})
                bot.send_message(chat_id, "Ок, начнем заново.")
                bot.send_message(chat_id, build_step_prompt("name"))
                return

            if lower != "да":
                session.offscript_count += 1
                session.qa_flags.append("confirm_expected")
                sessions.save(session)
                answer = ai.reply(session.step, session.draft.__dict__, text, "confirm_expected")
                answer = f"{answer}\n\n{build_retry_prompt(session.step, 'confirm_expected')}"
                bot.send_message(chat_id, answer)
                return

            lead_id = str(uuid.uuid4())
            lead = build_lead_record(lead_id=lead_id, draft=session.draft, local_timezone=settings.local_timezone)
            LOGGER.debug("[bot.text_handler] Saving lead", extra={"chat_id": chat_id, "lead_id": lead_id})
            quality_payload = {
                "offscript_count": session.offscript_count,
                "qa_flags": session.qa_flags,
            }
            lead_repo.save_lead(lead, quality_payload=quality_payload)
            LOGGER.info("[bot.text_handler] Lead saved", extra={"chat_id": chat_id, "lead_id": lead_id})
            sessions.reset(chat_id, source_user_id=user_id, source_username=source_username or "")
            bot.send_message(chat_id, f"Спасибо! Заявка отправлена. Номер: {lead_id}")
        except Exception as error:  # noqa: BLE001
            LOGGER.error(
                "[bot.text_handler] Unhandled error",
                extra={"chat_id": chat_id, "error": str(error)},
            )
            bot.send_message(chat_id, "Техническая ошибка. Попробуйте снова через минуту.")

    LOGGER.info("[bot.main] Polling started")
    bot.infinity_polling(timeout=20, long_polling_timeout=20, interval=settings.poll_interval_seconds)


if __name__ == "__main__":
    main()
