from pathlib import Path

from flask import Flask

from domain import LeadListItem

from routes import bp
from session import SessionStore


class FakeAI:
    def reply(self, step: str, draft: dict, user_text: str, validation_hint: str) -> str:
        return f"fallback:{step}:{validation_hint}"


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
