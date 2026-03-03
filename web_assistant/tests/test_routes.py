from flask import Flask

from routes import bp
from session import SessionStore


class FakeAI:
    def reply(self, step: str, draft: dict, user_text: str, validation_hint: str) -> str:
        return f"fallback:{step}:{validation_hint}"


class FakeLeadRepo:
    def __init__(self) -> None:
        self.saved = []

    def save_website_lead(self, lead_id: str, draft, session_id: str) -> None:  # noqa: ANN001
        self.saved.append((lead_id, draft.name, session_id))


def create_test_client():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["session_store"] = SessionStore()
    app.config["assistant_ai"] = FakeAI()
    app.config["lead_repo"] = FakeLeadRepo()
    app.register_blueprint(bp)
    return app.test_client(), app.config["lead_repo"]


def test_full_flow_submit() -> None:
    client, lead_repo = create_test_client()
    sid = "sid-test"

    start = client.post("/api/chat/start", headers={"X-Session-Id": sid})
    assert start.status_code == 200

    step1 = client.post("/api/chat/message", json={"message": "Иван"}, headers={"X-Session-Id": sid})
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
