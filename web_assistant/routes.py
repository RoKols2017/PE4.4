from __future__ import annotations

import logging
import uuid
from dataclasses import asdict

from flask import Blueprint, Response, current_app, jsonify, render_template, request

from domain import normalize_name, parse_contact, validate_contact, validate_name, validate_request
from runtime_policy import StructuredAIResponse


LOGGER = logging.getLogger(__name__)
bp = Blueprint("web_assistant", __name__)
ALLOWED_SOURCES = {"telegram_bot", "website_assistant"}
STEP_INDEX = {"name": 0, "contact": 1, "request": 2, "confirm": 3}
CONFIRM_YES = {"да", "yes", "ok", "ок", "отправляй", "подтверждаю", "подтвердить"}
CONFIRM_NO = {"нет", "no", "заново", "сначала", "начать заново"}


def _session_id() -> str:
    return request.headers.get("X-Session-Id", "").strip() or str(uuid.uuid4())


def _step_prompt(step: str) -> str:
    if step == "name":
        return "Как к вам обращаться?"
    if step == "contact":
        return "Оставьте, пожалуйста, телефон или email."
    if step == "request":
        return "Коротко опишите задачу."
    return "Проверьте данные. Если все верно, напишите 'да'. Если нужно что-то поправить, напишите 'исправь имя', 'исправь контакт' или 'исправь задачу'."


def _confirm_summary(state) -> str:  # noqa: ANN001
    contact = state.draft.phone or state.draft.email or "-"
    return (
        "Проверьте данные:\n"
        f"Имя: {state.draft.name or '-'}\n"
        f"Контакт: {contact}\n"
        f"Задача: {state.draft.request or '-'}\n\n"
        "Если все верно, напишите 'да'. Если нужно изменить поле, напишите 'исправь имя', 'исправь контакт' или 'исправь задачу'."
    )


def _next_step(state) -> str:  # noqa: ANN001
    if not state.draft.name:
        return "name"
    if not state.draft.phone and not state.draft.email:
        return "contact"
    if not state.draft.request:
        return "request"
    return "confirm"


def _set_step(state, step: str) -> None:  # noqa: ANN001
    state.step = step
    state.offscript_count = 0
    state.last_validation_result = ""


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
    if "контакт" in lowered or "телефон" in lowered or "email" in lowered or "почт" in lowered:
        return "contact"
    if "задач" in lowered or "запрос" in lowered:
        return "request"
    return ""


def _is_confirm_yes(text: str, ai_response: StructuredAIResponse) -> bool:
    return ai_response.detected_intent == "confirm_yes" or text.lower() in CONFIRM_YES


def _is_confirm_no(text: str, ai_response: StructuredAIResponse) -> bool:
    return ai_response.detected_intent == "confirm_no" or text.lower() in CONFIRM_NO


def _retry_message(ai, state, validation_code: str, user_text: str, session_id: str) -> str:  # noqa: ANN001
    retry_response = ai.respond(
        current_step=state.step,
        known_fields=state.draft.__dict__,
        validation_result=validation_code,
        offscript_count=state.offscript_count,
        last_user_message=user_text,
        correlation_id=session_id,
    )
    return retry_response.user_facing_message


def _apply_name_candidate(state, candidate: str | None, fallback_text: str | None) -> tuple[bool, str]:  # noqa: ANN001
    raw_value = candidate or fallback_text or ""
    ok, code = validate_name(raw_value)
    if not ok:
        return False, code
    state.draft.name = normalize_name(raw_value)
    if "name" not in state.accepted_candidate_fields:
        state.accepted_candidate_fields.append("name")
    return True, ""


def _apply_contact_candidate(state, candidate: str | None, fallback_text: str | None) -> tuple[bool, str]:  # noqa: ANN001
    raw_value = candidate or fallback_text or ""
    phone, email = parse_contact(raw_value)
    ok, code = validate_contact(phone, email, raw_text=raw_value)
    if not ok:
        return False, code
    state.draft.phone = phone
    state.draft.email = email
    if "contact" not in state.accepted_candidate_fields:
        state.accepted_candidate_fields.append("contact")
    return True, ""


def _apply_request_candidate(state, candidate: str | None, fallback_text: str | None) -> tuple[bool, str]:  # noqa: ANN001
    raw_value = candidate or fallback_text or ""
    ok, code = validate_request(raw_value)
    if not ok:
        return False, code
    state.draft.request = " ".join(raw_value.split())
    if "request" not in state.accepted_candidate_fields:
        state.accepted_candidate_fields.append("request")
    return True, ""


def _advance_or_retry(*, state, ai, user_message: str, policy_response: StructuredAIResponse, session_id: str) -> tuple[str, bool]:  # noqa: ANN001
    order = ("name", "contact", "request")
    start_index = STEP_INDEX.get(state.step, 0)
    process_all_fields = policy_response.detected_intent == "mixed_input"
    fields_to_process = order[start_index:] if process_all_fields else (state.step,)
    for field in fields_to_process:
        fallback_text = user_message if state.step == field else None
        if field == "name":
            ok, code = _apply_name_candidate(state, policy_response.candidate_fields.name, fallback_text)
        elif field == "contact":
            ok, code = _apply_contact_candidate(state, policy_response.candidate_fields.contact, fallback_text)
        else:
            ok, code = _apply_request_candidate(state, policy_response.candidate_fields.request, fallback_text)

        if not ok:
            state.step = field
            state.offscript_count += 1
            state.last_validation_result = code
            state.qa_flags.append(code)
            LOGGER.warning(
                "[web_assistant.routes] Field validation failed",
                extra={"session_id": session_id, "step": field, "code": code},
            )
            return _retry_message(ai, state, code, user_message, session_id), False

    _set_step(state, _next_step(state))
    if state.step == "confirm":
        return _confirm_summary(state), True
    return _step_prompt(state.step), True


@bp.get("/")
def index() -> str:
    return render_template("index.html")


def _authorize_leads_view() -> tuple[bool, Response | None]:
    expected = str(current_app.config.get("leads_view_token", "")).strip()
    provided = request.headers.get("X-Leads-View-Token", "").strip() or request.args.get("token", "").strip()

    if not expected:
        LOGGER.error("[web_assistant.routes] Leads view is not configured")
        response = jsonify({"error": "leads_view_not_configured"})
        response.status_code = 503
        return False, response

    if provided != expected:
        LOGGER.warning(
            "[web_assistant.routes] Unauthorized leads view access",
            extra={"path": request.path, "remote": request.remote_addr or "unknown"},
        )
        response = jsonify({"error": "unauthorized"})
        response.status_code = 401
        return False, response

    LOGGER.info("[web_assistant.routes] Leads view authorized", extra={"path": request.path})
    return True, None


def _parse_pagination() -> tuple[int, int, str | None, Response | None]:
    raw_limit = request.args.get("limit", "20").strip()
    raw_offset = request.args.get("offset", "0").strip()
    raw_source = request.args.get("source", "").strip()

    try:
        limit = int(raw_limit)
        offset = int(raw_offset)
    except ValueError:
        LOGGER.warning(
            "[web_assistant.routes] Invalid pagination parameters",
            extra={"limit": raw_limit, "offset": raw_offset},
        )
        response = jsonify({"error": "invalid_pagination"})
        response.status_code = 400
        return 0, 0, None, response

    if limit < 1 or limit > 100 or offset < 0:
        LOGGER.warning(
            "[web_assistant.routes] Pagination out of range",
            extra={"limit": limit, "offset": offset},
        )
        response = jsonify({"error": "invalid_pagination_range"})
        response.status_code = 400
        return 0, 0, None, response

    source = raw_source or None
    if source and source not in ALLOWED_SOURCES:
        LOGGER.warning("[web_assistant.routes] Invalid source filter", extra={"source": source})
        response = jsonify({"error": "invalid_source"})
        response.status_code = 400
        return 0, 0, None, response

    LOGGER.debug(
        "[web_assistant.routes] Leads pagination parsed",
        extra={"limit": limit, "offset": offset, "source": source or "all"},
    )
    return limit, offset, source, None


@bp.get("/leads")
def leads_page() -> str | Response:
    authorized, error_response = _authorize_leads_view()
    if not authorized:
        return error_response
    return render_template("leads.html", leads_view_token=current_app.config.get("leads_view_token", ""))


@bp.get("/api/leads")
def api_leads() -> Response:
    authorized, error_response = _authorize_leads_view()
    if not authorized:
        return error_response

    limit, offset, source, parse_error = _parse_pagination()
    if parse_error is not None:
        return parse_error

    lead_repo = current_app.config["lead_repo"]
    try:
        items, total = lead_repo.list_leads(limit=limit, offset=offset, source=source)
        LOGGER.info(
            "[web_assistant.routes] Leads loaded",
            extra={"limit": limit, "offset": offset, "source": source or "all", "count": len(items), "total": total},
        )
        return jsonify(
            {
                "items": [asdict(item) for item in items],
                "pagination": {"limit": limit, "offset": offset, "total": total},
                "source": source or "all",
            }
        )
    except Exception as error:  # noqa: BLE001
        LOGGER.error(
            "[web_assistant.routes] Failed to read leads",
            extra={"limit": limit, "offset": offset, "source": source or "all", "error": str(error)},
        )
        return jsonify({"error": "leads_read_failed"}), 500


@bp.get("/health")
def health() -> Response:
    return jsonify({"status": "ok"})


@bp.post("/api/chat/start")
def chat_start() -> Response:
    session_id = _session_id()
    store = current_app.config["session_store"]
    store.reset(session_id)
    LOGGER.info("[web_assistant.routes] Chat started", extra={"session_id": session_id})
    return jsonify(
        {
            "session_id": session_id,
            "step": "name",
            "assistant_message": "Здравствуйте! Помогу быстро оформить заявку. Как к вам обращаться?",
            "typing": False,
        }
    )


@bp.post("/api/chat/message")
def chat_message() -> Response:
    payload = request.get_json(silent=True) or {}
    user_message = str(payload.get("message", "")).strip()
    if not user_message:
        return jsonify({"error": "message_required"}), 400

    session_id = _session_id()
    store = current_app.config["session_store"]
    ai = current_app.config["assistant_ai"]
    lead_repo = current_app.config["lead_repo"]
    state = store.get_or_create(session_id)
    state.last_user_message = user_message

    LOGGER.debug("[web_assistant.routes] Message received", extra={"session_id": session_id, "step": state.step})

    if state.step == "confirm":
        policy_response = ai.respond(
            current_step="confirm",
            known_fields=state.draft.__dict__,
            validation_result="",
            offscript_count=state.offscript_count,
            last_user_message=user_message,
            correlation_id=session_id,
        )
        edit_target = _detect_edit_target(user_message, policy_response)
        if edit_target:
            state.confirm_edit_target = edit_target
            if edit_target == "name":
                state.draft.name = ""
            elif edit_target == "contact":
                state.draft.phone = ""
                state.draft.email = ""
            else:
                state.draft.request = ""
            _set_step(state, edit_target)
            store.save(state)
            LOGGER.info(
                "[web_assistant.routes] Confirm edit requested",
                extra={"session_id": session_id, "edit_target": edit_target},
            )
            return jsonify({"session_id": session_id, "step": state.step, "typing": False, "assistant_message": _step_prompt(state.step)})

        if _is_confirm_no(user_message, policy_response):
            store.reset(session_id)
            LOGGER.warning("[web_assistant.routes] User restarted flow", extra={"session_id": session_id})
            return jsonify({"session_id": session_id, "step": "name", "typing": False, "assistant_message": "Хорошо, начнем заново. Как к вам обращаться?"})

        if not _is_confirm_yes(user_message, policy_response):
            state.offscript_count += 1
            state.last_validation_result = "confirm_expected"
            state.qa_flags.append("confirm_expected")
            store.save(state)
            return jsonify(
                {
                    "session_id": session_id,
                    "step": state.step,
                    "typing": True,
                    "assistant_message": _retry_message(ai, state, "confirm_expected", user_message, session_id),
                }
            )

        lead_id = str(uuid.uuid4())
        LOGGER.debug("[web_assistant.routes] Saving lead", extra={"session_id": session_id, "lead_id": lead_id})
        quality_payload = {
            "offscript_count": state.offscript_count,
            "qa_flags": state.qa_flags,
            "accepted_candidate_fields": state.accepted_candidate_fields,
        }
        lead_repo.save_website_lead(lead_id, state.draft, session_id, quality_payload=quality_payload)
        store.reset(session_id)
        LOGGER.info("[web_assistant.routes] Lead saved", extra={"session_id": session_id, "lead_id": lead_id})
        return jsonify(
            {
                "session_id": session_id,
                "step": "name",
                "typing": False,
                "assistant_message": f"Готово, заявку отправил. Номер: {lead_id}",
            }
        )

    policy_response = ai.respond(
        current_step=state.step,
        known_fields=state.draft.__dict__,
        validation_result="",
        offscript_count=state.offscript_count,
        last_user_message=user_message,
        correlation_id=session_id,
    )
    state.confirm_edit_target = ""
    next_message, advanced = _advance_or_retry(
        state=state,
        ai=ai,
        user_message=user_message,
        policy_response=policy_response,
        session_id=session_id,
    )
    store.save(state)
    LOGGER.info(
        "[web_assistant.routes] Step processed",
        extra={"session_id": session_id, "step": state.step, "advanced": advanced},
    )
    return jsonify({"session_id": session_id, "step": state.step, "typing": not advanced, "assistant_message": next_message})


@bp.post("/api/client-log")
def client_log() -> Response:
    payload = request.get_json(silent=True) or {}
    event = str(payload.get("event", "unknown"))
    details = payload.get("details", {})
    LOGGER.debug("[web_assistant.client] Event", extra={"event": event, "details": details})
    return jsonify({"ok": True})
