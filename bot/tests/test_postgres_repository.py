from __future__ import annotations

from domain import LeadDraft
from postgres_repository import build_lead_record


def test_build_lead_record_sets_defaults() -> None:
    draft = LeadDraft(
        source_user_id="42",
        source_username="origin_user",
        name="Ivan",
        telegram_username="@ivan_user",
        request="Need consultation",
    )
    lead = build_lead_record(lead_id="74f28be3-cebe-43f1-a2b5-f7e0dc6cbf0f", draft=draft, local_timezone="UTC")

    assert lead.source == "telegram_bot"
    assert lead.contact_ok is True
    assert lead.preferred_contact_method == "telegram"
    assert lead.status == "new"
    assert lead.priority == "normal"
    assert lead.email == ""
