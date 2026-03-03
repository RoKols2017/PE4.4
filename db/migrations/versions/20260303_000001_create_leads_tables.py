"""create leads and lead_events tables

Revision ID: 20260303_000001
Revises:
Create Date: 2026-03-03 00:00:01
"""

from __future__ import annotations

import logging

from alembic import op


revision = "20260303_000001"
down_revision = None
branch_labels = None
depends_on = None

LOGGER = logging.getLogger(__name__)


def upgrade() -> None:
    LOGGER.info("[db.migration] Running upgrade for leads schema", extra={"revision": revision})
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS leads (
            lead_id UUID PRIMARY KEY,
            source TEXT NOT NULL CHECK (source IN ('telegram_bot', 'website_assistant')),
            source_user_id TEXT NOT NULL,
            source_username TEXT NOT NULL DEFAULT '',
            name TEXT NOT NULL,
            telegram_username TEXT NOT NULL DEFAULT '',
            phone TEXT NOT NULL DEFAULT '',
            email TEXT NOT NULL DEFAULT '',
            contact_ok BOOLEAN NOT NULL,
            preferred_contact_method TEXT NOT NULL CHECK (preferred_contact_method IN ('phone', 'telegram', 'email', 'both', 'not_specified')),
            request TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'new',
            priority TEXT NOT NULL DEFAULT 'normal',
            utm_source TEXT NOT NULL DEFAULT '',
            utm_campaign TEXT NOT NULL DEFAULT '',
            manager_note TEXT NOT NULL DEFAULT '',
            created_at_utc TIMESTAMPTZ NOT NULL,
            created_at_local TIMESTAMPTZ NOT NULL,
            last_update_at_utc TIMESTAMPTZ NOT NULL,
            CHECK (contact_ok = ((phone <> '') OR (telegram_username <> '') OR (email <> '')))
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_leads_source_created_at ON leads (source, created_at_utc DESC)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_leads_status_created_at ON leads (status, created_at_utc DESC)")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS lead_events (
            event_id BIGSERIAL PRIMARY KEY,
            lead_id UUID NOT NULL REFERENCES leads(lead_id) ON DELETE CASCADE,
            event_type TEXT NOT NULL,
            payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            source TEXT NOT NULL DEFAULT '',
            session_id TEXT NOT NULL DEFAULT '',
            created_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_lead_events_lead_id_created_at ON lead_events (lead_id, created_at_utc DESC)")


def downgrade() -> None:
    LOGGER.info("[db.migration] Running downgrade for leads schema", extra={"revision": revision})
    try:
        op.execute("DROP TABLE IF EXISTS lead_events")
        op.execute("DROP TABLE IF EXISTS leads")
    except Exception as error:  # noqa: BLE001
        LOGGER.error("[db.migration] Rollback failed", extra={"revision": revision, "error": str(error)})
        raise
