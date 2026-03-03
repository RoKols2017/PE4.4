from __future__ import annotations

import logging
import uuid
from dataclasses import asdict

from flask import Blueprint, Response, current_app, jsonify, render_template, request

from domain import parse_contact, validate_contact, validate_name, validate_request


LOGGER = logging.getLogger(__name__)
bp = Blueprint("web_assistant", __name__)
ALLOWED_SOURCES = {"telegram_bot", "website_assistant"}


def _session_id() -> str:
    return request.headers.get("X-Session-Id", "").strip() or str(uuid.uuid4())


def _step_prompt(step: str) -> str:
    if step == "name":
        return "Как вас зовут?"
    if step == "contact":
        return "Укажите контакт: телефон (+79991234567) или email (example@domain.com)."
    if step == "request":
        return "Кратко опишите суть вашего запроса."
    return "Проверьте и подтвердите отправку: напишите 'да' или 'нет'."


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
            "assistant_message": "Здравствуйте! Я помогу оформить заявку. Как вас зовут?",
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

    LOGGER.debug(
        "[web_assistant.routes] Message received",
        extra={"session_id": session_id, "step": state.step},
    )

    if state.step == "name":
        ok, code = validate_name(user_message)
        if not ok:
            state.offscript_count += 1
            store.save(state)
            LOGGER.warning("[web_assistant.routes] Name validation failed", extra={"session_id": session_id, "code": code})
            return jsonify(
                {
                    "session_id": session_id,
                    "step": state.step,
                    "typing": True,
                    "assistant_message": ai.reply(state.step, state.draft.__dict__, user_message, code),
                }
            )

        state.draft.name = " ".join(user_message.split())
        state.step = "contact"
        state.offscript_count = 0
        store.save(state)
        LOGGER.info("[web_assistant.routes] Step transition", extra={"session_id": session_id, "step": state.step})
        return jsonify({"session_id": session_id, "step": state.step, "typing": False, "assistant_message": _step_prompt(state.step)})

    if state.step == "contact":
        phone, email = parse_contact(user_message)
        ok, code = validate_contact(phone, email)
        if not ok:
            state.offscript_count += 1
            store.save(state)
            LOGGER.warning("[web_assistant.routes] Contact validation failed", extra={"session_id": session_id, "code": code})
            return jsonify(
                {
                    "session_id": session_id,
                    "step": state.step,
                    "typing": True,
                    "assistant_message": ai.reply(state.step, state.draft.__dict__, user_message, code),
                }
            )

        state.draft.phone = phone
        state.draft.email = email
        state.step = "request"
        state.offscript_count = 0
        store.save(state)
        LOGGER.info("[web_assistant.routes] Step transition", extra={"session_id": session_id, "step": state.step})
        return jsonify({"session_id": session_id, "step": state.step, "typing": False, "assistant_message": _step_prompt(state.step)})

    if state.step == "request":
        ok, code = validate_request(user_message)
        if not ok:
            state.offscript_count += 1
            store.save(state)
            LOGGER.warning("[web_assistant.routes] Request validation failed", extra={"session_id": session_id, "code": code})
            return jsonify(
                {
                    "session_id": session_id,
                    "step": state.step,
                    "typing": True,
                    "assistant_message": ai.reply(state.step, state.draft.__dict__, user_message, code),
                }
            )

        state.draft.request = " ".join(user_message.split())
        state.step = "confirm"
        state.offscript_count = 0
        store.save(state)
        LOGGER.info("[web_assistant.routes] Step transition", extra={"session_id": session_id, "step": state.step})

        contact = state.draft.phone or state.draft.email
        summary = (
            "Проверьте данные:\n"
            f"Имя: {state.draft.name}\n"
            f"Контакт: {contact}\n"
            f"Запрос: {state.draft.request}\n\n"
            "Подтверждаете отправку? (да/нет)"
        )
        return jsonify({"session_id": session_id, "step": state.step, "typing": False, "assistant_message": summary})

    answer = user_message.lower()
    if answer == "нет":
        store.reset(session_id)
        LOGGER.warning("[web_assistant.routes] User restarted flow", extra={"session_id": session_id})
        return jsonify({"session_id": session_id, "step": "name", "typing": False, "assistant_message": "Ок, начнем заново. Как вас зовут?"})

    if answer != "да":
        state.offscript_count += 1
        store.save(state)
        return jsonify(
            {
                "session_id": session_id,
                "step": state.step,
                "typing": True,
                "assistant_message": ai.reply(state.step, state.draft.__dict__, user_message, "confirm_expected"),
            }
        )

    lead_id = str(uuid.uuid4())
    LOGGER.debug("[web_assistant.routes] Saving lead", extra={"session_id": session_id, "lead_id": lead_id})
    lead_repo.save_website_lead(lead_id, state.draft, session_id)
    store.reset(session_id)
    LOGGER.info("[web_assistant.routes] Lead saved", extra={"session_id": session_id, "lead_id": lead_id})
    return jsonify(
        {
            "session_id": session_id,
            "step": "name",
            "typing": False,
            "assistant_message": f"Спасибо! Заявка отправлена. Номер: {lead_id}",
        }
    )


@bp.post("/api/client-log")
def client_log() -> Response:
    payload = request.get_json(silent=True) or {}
    event = str(payload.get("event", "unknown"))
    details = payload.get("details", {})
    LOGGER.debug("[web_assistant.client] Event", extra={"event": event, "details": details})
    return jsonify({"ok": True})
