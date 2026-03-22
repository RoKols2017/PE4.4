from __future__ import annotations

import logging
import uuid

import telebot

from ai_logic import AssistantAI
from config import load_settings
from domain import LeadRepository, normalize_name, parse_contact, validate_contact, validate_name, validate_request
from postgres_repository import PostgresLeadRepository, build_lead_record
from runtime_policy import StructuredAIResponse
from session import Session, SessionStore


LOGGER = logging.getLogger(__name__)

STEP_INDEX = {"name": 0, "contact": 1, "request": 2, "confirm": 3}
CONFIRM_YES = {"да", "yes", "ok", "ок", "отправляй", "подтверждаю", "подтвердить"}
CONFIRM_NO = {"нет", "no", "заново", "сначала", "начать заново"}


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def build_step_prompt(step: str) -> str:
    if step == "name":
        return "Как к вам обращаться?"
    if step == "contact":
        return "Оставьте контакт - телефон или Telegram username."
    if step == "request":
        return "Коротко расскажите, какая задача у вас сейчас."
    return "Проверьте данные ниже. Если все верно - напишите 'да'. Если нужно что-то поправить - напишите, например, 'исправь контакт'."


def _contact_summary(session: Session) -> str:
    if session.draft.phone:
        return session.draft.phone
    if session.draft.telegram_username:
        return f"@{session.draft.telegram_username}"
    return "-"


def build_confirm_summary(session: Session) -> str:
    return (
        "Проверьте данные:\n"
        f"Имя: {session.draft.name or '-'}\n"
        f"Контакт: {_contact_summary(session)}\n"
        f"Задача: {session.draft.request or '-'}\n\n"
        "Если все верно, напишите 'да'. Если нужно изменить поле, напишите 'исправь имя', 'исправь контакт' или 'исправь задачу'."
    )


def _next_step(session: Session) -> str:
    if not session.draft.name:
        return "name"
    if not session.draft.phone and not session.draft.telegram_username:
        return "contact"
    if not session.draft.request:
        return "request"
    return "confirm"


def _set_step(session: Session, step: str) -> None:
    session.step = step
    session.offscript_count = 0
    session.last_validation_result = ""


def _detect_edit_target(text: str, ai_response: StructuredAIResponse) -> str:
    if ai_response.detected_intent == "edit_name":
        return "name"
    if ai_response.detected_intent == "edit_contact":
        return "contact"
    if ai_response.detected_intent == "edit_request":
        return "request"

    lowered = text.lower()
    if "имя" in lowered:
        return "name"
    if "контакт" in lowered or "телефон" in lowered or "телеграм" in lowered:
        return "contact"
    if "задач" in lowered or "запрос" in lowered:
        return "request"
    return ""


def _is_confirm_yes(text: str, ai_response: StructuredAIResponse) -> bool:
    return ai_response.detected_intent == "confirm_yes" or text.lower() in CONFIRM_YES


def _is_confirm_no(text: str, ai_response: StructuredAIResponse) -> bool:
    return ai_response.detected_intent == "confirm_no" or text.lower() in CONFIRM_NO


def _apply_name_candidate(session: Session, candidate: str | None, fallback_text: str | None) -> tuple[bool, str]:
    raw_value = candidate or fallback_text or ""
    ok, code = validate_name(raw_value)
    if not ok:
        return False, code
    session.draft.name = normalize_name(raw_value)
    if "name" not in session.accepted_candidate_fields:
        session.accepted_candidate_fields.append("name")
    return True, ""


def _apply_contact_candidate(
    session: Session,
    candidate: str | None,
    fallback_text: str | None,
    source_username: str,
) -> tuple[bool, str]:
    raw_value = candidate or fallback_text or ""
    phone, telegram_username = parse_contact(raw_value)
    if not phone and not telegram_username and source_username:
        telegram_username = source_username
    ok, code = validate_contact(phone, telegram_username, raw_text=raw_value)
    if not ok:
        return False, code
    session.draft.phone = phone
    session.draft.telegram_username = telegram_username
    if "contact" not in session.accepted_candidate_fields:
        session.accepted_candidate_fields.append("contact")
    return True, ""


def _apply_request_candidate(session: Session, candidate: str | None, fallback_text: str | None) -> tuple[bool, str]:
    raw_value = candidate or fallback_text or ""
    ok, code = validate_request(raw_value)
    if not ok:
        return False, code
    session.draft.request = " ".join(raw_value.split())
    if "request" not in session.accepted_candidate_fields:
        session.accepted_candidate_fields.append("request")
    return True, ""


def _retry_message(
    ai: AssistantAI,
    session: Session,
    *,
    validation_code: str,
    user_text: str,
    correlation_id: str,
) -> str:
    retry_response = ai.respond(
        current_step=session.step,
        known_fields=session.draft.__dict__,
        validation_result=validation_code,
        offscript_count=session.offscript_count,
        last_user_message=user_text,
        correlation_id=correlation_id,
    )
    return retry_response.user_facing_message


def _advance_or_retry(
    *,
    session: Session,
    ai: AssistantAI,
    user_text: str,
    source_username: str,
    policy_response: StructuredAIResponse,
    correlation_id: str,
) -> tuple[str, bool]:
    order = ("name", "contact", "request")
    start_index = STEP_INDEX.get(session.step, 0)
    for field in order[start_index:]:
        fallback_text = user_text if session.step == field else None
        if field == "name":
            ok, code = _apply_name_candidate(session, policy_response.candidate_fields.name, fallback_text)
        elif field == "contact":
            ok, code = _apply_contact_candidate(session, policy_response.candidate_fields.contact, fallback_text, source_username)
        else:
            ok, code = _apply_request_candidate(session, policy_response.candidate_fields.request, fallback_text)

        if not ok:
            session.step = field
            session.offscript_count += 1
            session.last_validation_result = code
            session.qa_flags.append(code)
            message = _retry_message(
                ai,
                session,
                validation_code=code,
                user_text=user_text,
                correlation_id=correlation_id,
            )
            LOGGER.warning(
                "[bot.flow] Field validation failed",
                extra={"chat_id": correlation_id, "step": field, "code": code},
            )
            return message, False

    _set_step(session, _next_step(session))
    if session.step == "confirm":
        return build_confirm_summary(session), True
    return build_step_prompt(session.step), True


def _handle_confirm(
    *,
    bot: telebot.TeleBot,
    message: telebot.types.Message,
    sessions: SessionStore,
    session: Session,
    ai: AssistantAI,
    lead_repo: LeadRepository,
    settings,
    source_username: str,
) -> None:
    text = (message.text or "").strip()
    chat_id = message.chat.id
    user_id = str(message.from_user.id) if message.from_user else str(chat_id)
    policy_response = ai.respond(
        current_step="confirm",
        known_fields=session.draft.__dict__,
        validation_result="",
        offscript_count=session.offscript_count,
        last_user_message=text,
        correlation_id=str(chat_id),
    )

    edit_target = _detect_edit_target(text, policy_response)
    if edit_target:
        session.confirm_edit_target = edit_target
        session.last_user_message = text
        if edit_target == "name":
            session.draft.name = ""
        elif edit_target == "contact":
            session.draft.phone = ""
            session.draft.telegram_username = ""
        else:
            session.draft.request = ""
        _set_step(session, edit_target)
        sessions.save(session)
        LOGGER.info(
            "[bot.flow] Confirm edit requested",
            extra={"chat_id": chat_id, "edit_target": edit_target},
        )
        bot.send_message(chat_id, build_step_prompt(edit_target))
        return

    if _is_confirm_no(text, policy_response):
        sessions.reset(chat_id, source_user_id=user_id, source_username=source_username)
        LOGGER.warning("[bot.flow] User restarted flow", extra={"chat_id": chat_id})
        bot.send_message(chat_id, "Хорошо, начнем заново.")
        bot.send_message(chat_id, build_step_prompt("name"))
        return

    if not _is_confirm_yes(text, policy_response):
        session.offscript_count += 1
        session.last_validation_result = "confirm_expected"
        session.qa_flags.append("confirm_expected")
        sessions.save(session)
        bot.send_message(
            chat_id,
            _retry_message(
                ai,
                session,
                validation_code="confirm_expected",
                user_text=text,
                correlation_id=str(chat_id),
            ),
        )
        return

    lead_id = str(uuid.uuid4())
    lead = build_lead_record(lead_id=lead_id, draft=session.draft, local_timezone=settings.local_timezone)
    quality_payload = {
        "offscript_count": session.offscript_count,
        "qa_flags": session.qa_flags,
        "accepted_candidate_fields": session.accepted_candidate_fields,
    }
    LOGGER.debug("[bot.flow] Saving lead", extra={"chat_id": chat_id, "lead_id": lead_id})
    lead_repo.save_lead(lead, quality_payload=quality_payload)
    LOGGER.info("[bot.flow] Lead saved", extra={"chat_id": chat_id, "lead_id": lead_id})
    sessions.reset(chat_id, source_user_id=user_id, source_username=source_username)
    bot.send_message(chat_id, f"Готово, заявку отправил. Номер: {lead_id}")


def main() -> None:
    settings = load_settings()
    configure_logging(settings.log_level)

    LOGGER.info("[bot.main] Starting telegram bot")
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
        bot.send_message(chat_id, "Здравствуйте! Помогу быстро оформить заявку.")
        bot.send_message(chat_id, build_step_prompt("name"))

    @bot.message_handler(commands=["new"])
    def reset_handler(message: telebot.types.Message) -> None:
        chat_id = message.chat.id
        user_id = str(message.from_user.id) if message.from_user else str(chat_id)
        source_username = message.from_user.username if message.from_user else ""
        sessions.reset(chat_id=chat_id, source_user_id=user_id, source_username=source_username or "")
        LOGGER.info("[bot.reset_handler] Session reset by /new", extra={"chat_id": chat_id})
        bot.send_message(chat_id, "Ок, давайте начнем сначала.")
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
        session.last_user_message = text

        LOGGER.debug("[bot.text_handler] Message received", extra={"chat_id": chat_id, "step": session.step})

        try:
            if session.step == "confirm":
                _handle_confirm(
                    bot=bot,
                    message=message,
                    sessions=sessions,
                    session=session,
                    ai=ai,
                    lead_repo=lead_repo,
                    settings=settings,
                    source_username=source_username or "",
                )
                return

            policy_response = ai.respond(
                current_step=session.step,
                known_fields=session.draft.__dict__,
                validation_result="",
                offscript_count=session.offscript_count,
                last_user_message=text,
                correlation_id=str(chat_id),
            )
            session.confirm_edit_target = ""
            next_message, advanced = _advance_or_retry(
                session=session,
                ai=ai,
                user_text=text,
                source_username=source_username or "",
                policy_response=policy_response,
                correlation_id=str(chat_id),
            )
            sessions.save(session)
            LOGGER.info(
                "[bot.flow] Step processed",
                extra={"chat_id": chat_id, "step": session.step, "advanced": advanced},
            )
            bot.send_message(chat_id, next_message)
        except Exception as error:  # noqa: BLE001
            LOGGER.error(
                "[bot.text_handler] Unhandled error",
                extra={"chat_id": chat_id, "error": str(error)},
            )
            bot.send_message(chat_id, "Техническая ошибка. Попробуйте еще раз чуть позже.")

    LOGGER.info("[bot.main] Polling started")
    bot.infinity_polling(timeout=20, long_polling_timeout=20, interval=settings.poll_interval_seconds)


if __name__ == "__main__":
    main()
