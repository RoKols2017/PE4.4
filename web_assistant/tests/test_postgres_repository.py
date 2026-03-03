from __future__ import annotations

from domain import LeadDraft, parse_contact


def test_contact_parsing_email() -> None:
    phone, email = parse_contact("ivan@example.com")
    assert phone == ""
    assert email == "ivan@example.com"


def test_website_draft_holds_contact_data() -> None:
    draft = LeadDraft(source_user_id="sid-1", name="Ivan", phone="+79990001122", email="", request="Need details")
    assert draft.phone == "+79990001122"
