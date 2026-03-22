from pathlib import Path

from flask import Flask

from domain import LeadListItem
from runtime_policy import CandidateFields, StructuredAIResponse

from routes import bp
from session import SessionStore


class FakeAI:
    def respond(
        self,
        *,
        current_step: str,
        known_fields: dict,
        validation_result: str,
        offscript_count: int,
        last_user_message: str,
        correlation_id: str,
    ) -> StructuredAIResponse:
        del known_fields, offscript_count, correlation_id
        message = f"fallback:{current_step}:{validation_result or 'none'}"
        intent = "answer_current_step"
        candidates = CandidateFields()

        if current_step == "confirm":
            lowered = last_user_message.lower()
            if lowered == "да":
                intent = "confirm_yes"
            elif lowered == "нет":
                intent = "confirm_no"
            elif "контакт" in lowered:
                intent = "edit_contact"
            return StructuredAIResponse(intent, candidates, validation_result != "", message)

        if current_step == "name" and validation_result == "":
            candidates = CandidateFields(name=last_user_message)
        elif current_step == "contact" and validation_result == "":
            candidates = CandidateFields(contact=last_user_message)
        elif current_step == "request" and validation_result == "":
            candidates = CandidateFields(request=last_user_message)
        return StructuredAIResponse(intent, candidates, validation_result != "", message)


class FakeLeadRepo:
    def __init__(self) -> None:
        self.saved = []
        self.items = [
            LeadListItem(
                lead_id="lead-1",
                source="website_assistant",
                name="Ivan",
                phone="",
                email="ivan@example.com",
                request="Need consultation",
                status="new",
                created_at_utc="2026-03-03T12:00:00+00:00",
            )
        ]

    def save_website_lead(self, lead_id: str, draft, session_id: str, quality_payload=None) -> None:  # noqa: ANN001
        self.saved.append((lead_id, draft.name, session_id, quality_payload or {}))

    def list_leads(self, limit: int, offset: int, source: str | None = None) -> tuple[list[LeadListItem], int]:
        filtered = [item for item in self.items if source is None or item.source == source]
        return filtered[offset : offset + limit], len(filtered)


def create_test_client():
    app_root = Path(__file__).resolve().parents[1]
    app = Flask(__name__, root_path=str(app_root), template_folder="templates", static_folder="static")
    app.config["TESTING"] = True
    app.config["session_store"] = SessionStore()
    app.config["assistant_ai"] = FakeAI()
    app.config["lead_repo"] = FakeLeadRepo()
    app.config["leads_view_token"] = "test-token"
    app.register_blueprint(bp)
    return app.test_client(), app.config["lead_repo"]


def test_full_flow_submit() -> None:
    client, lead_repo = create_test_client()
    sid = "sid-test"

    start = client.post("/api/chat/start", headers={"X-Session-Id": sid})
    assert start.status_code == 200

    step1 = client.post("/api/chat/message", json={"message": "я Иван"}, headers={"X-Session-Id": sid})
    assert step1.status_code == 200

    step2 = client.post(
        "/api/chat/message",
        json={"message": "ivan@example.com"},
        headers={"X-Session-Id": sid},
    )
    assert step2.status_code == 200

    step3 = client.post(
        "/api/chat/message",
        json={"message": "Хочу узнать стоимость"},
        headers={"X-Session-Id": sid},
    )
    assert step3.status_code == 200

    final = client.post("/api/chat/message", json={"message": "да"}, headers={"X-Session-Id": sid})
    assert final.status_code == 200
    assert lead_repo.saved
    assert lead_repo.saved[0][1] == "Иван"


def test_request_step_rejects_contact_like_input() -> None:
    client, _lead_repo = create_test_client()
    sid = "sid-contact-in-request"

    client.post("/api/chat/start", headers={"X-Session-Id": sid})
    client.post("/api/chat/message", json={"message": "Иван"}, headers={"X-Session-Id": sid})
    client.post("/api/chat/message", json={"message": "ivan@example.com"}, headers={"X-Session-Id": sid})
    bad_request = client.post("/api/chat/message", json={"message": "+79991112233"}, headers={"X-Session-Id": sid})

    assert bad_request.status_code == 200
    payload = bad_request.get_json()
    assert payload["step"] == "request"
    assert "request_looks_like_contact" in payload["assistant_message"]


def test_confirm_step_allows_partial_contact_edit() -> None:
    client, lead_repo = create_test_client()
    sid = "sid-edit-contact"

    client.post("/api/chat/start", headers={"X-Session-Id": sid})
    client.post("/api/chat/message", json={"message": "Иван"}, headers={"X-Session-Id": sid})
    client.post("/api/chat/message", json={"message": "ivan@example.com"}, headers={"X-Session-Id": sid})
    client.post("/api/chat/message", json={"message": "Нужен сайт"}, headers={"X-Session-Id": sid})

    edit = client.post("/api/chat/message", json={"message": "исправь контакт"}, headers={"X-Session-Id": sid})
    assert edit.status_code == 200
    assert edit.get_json()["step"] == "contact"

    contact = client.post("/api/chat/message", json={"message": "+79990001122"}, headers={"X-Session-Id": sid})
    assert contact.status_code == 200
    assert contact.get_json()["step"] == "confirm"

    final = client.post("/api/chat/message", json={"message": "да"}, headers={"X-Session-Id": sid})
    assert final.status_code == 200
    assert lead_repo.saved


def test_name_edit_does_not_autofill_contact_and_request() -> None:
    client, _lead_repo = create_test_client()
    sid = "sid-edit-name"

    client.post("/api/chat/start", headers={"X-Session-Id": sid})
    client.post("/api/chat/message", json={"message": "Иван"}, headers={"X-Session-Id": sid})
    client.post("/api/chat/message", json={"message": "ivan@example.com"}, headers={"X-Session-Id": sid})
    client.post("/api/chat/message", json={"message": "Нужен сайт"}, headers={"X-Session-Id": sid})

    edit = client.post("/api/chat/message", json={"message": "исправь имя"}, headers={"X-Session-Id": sid})
    assert edit.status_code == 200
    assert edit.get_json()["step"] == "name"

    response = client.post(
        "/api/chat/message",
        json={"message": "Константин Хутькин, почта hut@gamil.com, нужен телеграм бот"},
        headers={"X-Session-Id": sid},
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["step"] == "name"
    assert "name_looks_like_request" in payload["assistant_message"]

    clean_name = client.post(
        "/api/chat/message",
        json={"message": "Константин Хутькин"},
        headers={"X-Session-Id": sid},
    )
    assert clean_name.status_code == 200
    payload = clean_name.get_json()
    assert payload["step"] == "confirm"
    assert "Константин Хутькин" in payload["assistant_message"]


def test_name_step_rejects_request_like_phrase() -> None:
    client, _lead_repo = create_test_client()
    sid = "sid-name-request-like"

    client.post("/api/chat/start", headers={"X-Session-Id": sid})
    response = client.post(
        "/api/chat/message",
        json={"message": "Хочу заказать телеграм бота"},
        headers={"X-Session-Id": sid},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["step"] == "name"
    assert "name_looks_like_request" in payload["assistant_message"]


def test_mixed_input_can_fill_whole_flow_until_confirm() -> None:
    client, _lead_repo = create_test_client()
    sid = "sid-mixed-input"
    app = client.application
    fake_ai = app.config["assistant_ai"]
    original_respond = fake_ai.respond

    def mixed_respond(**kwargs):
        if kwargs["current_step"] == "name":
            return StructuredAIResponse(
                "mixed_input",
                CandidateFields(name="Иван", contact="ivan@example.com", request="Нужен лендинг"),
                False,
                "Принял.",
            )
        return original_respond(**kwargs)

    fake_ai.respond = mixed_respond

    client.post("/api/chat/start", headers={"X-Session-Id": sid})
    response = client.post(
        "/api/chat/message",
        json={"message": "Я Иван, почта ivan@example.com, нужен лендинг"},
        headers={"X-Session-Id": sid},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["step"] == "confirm"
    assert "Иван" in payload["assistant_message"]


def test_leads_api_requires_token() -> None:
    client, _repo = create_test_client()
    response = client.get("/api/leads")
    assert response.status_code == 401


def test_leads_api_returns_items_with_token() -> None:
    client, _repo = create_test_client()
    response = client.get("/api/leads", headers={"X-Leads-View-Token": "test-token"})
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["pagination"]["total"] == 1
    assert payload["items"][0]["name"] == "Ivan"


def test_leads_api_rejects_invalid_params() -> None:
    client, _repo = create_test_client()
    response = client.get("/api/leads?limit=0", headers={"X-Leads-View-Token": "test-token"})
    assert response.status_code == 400


def test_leads_page_requires_token() -> None:
    client, _repo = create_test_client()
    response = client.get("/leads")
    assert response.status_code == 401


def test_leads_page_renders_with_token() -> None:
    client, _repo = create_test_client()
    response = client.get("/leads?token=test-token")
    assert response.status_code == 200
