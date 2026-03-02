from domain import LeadDraft
from sheets import HEADERS, build_lead_record


def test_headers_match_data_model_length() -> None:
    assert len(HEADERS) == 18
    assert HEADERS[0] == "lead_id"
    assert HEADERS[-1] == "last_update_at_utc"


def test_build_lead_record_sets_defaults() -> None:
    draft = LeadDraft(
        source_user_id="42",
        source_username="origin_user",
        name="Ivan",
        telegram_username="@ivan_user",
        request="Нужна консультация",
    )
    lead = build_lead_record(lead_id="lead-1", draft=draft, local_timezone="UTC")
    assert lead.source == "telegram_bot"
    assert lead.contact_ok is True
    assert lead.preferred_contact_method == "telegram"
    assert lead.status == "new"
    assert lead.priority == "normal"
