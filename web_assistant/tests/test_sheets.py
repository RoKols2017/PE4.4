from domain import LeadDraft
from sheets_schema import HEADERS


def test_shared_headers_are_a_to_r() -> None:
    assert len(HEADERS) == 18
    assert HEADERS[0] == "lead_id"
    assert HEADERS[-1] == "last_update_at_utc"


def test_website_email_mapping_note_contract() -> None:
    draft = LeadDraft(source_user_id="sid-1", name="Test", email="a@b.com", request="Need details")
    assert draft.email == "a@b.com"
