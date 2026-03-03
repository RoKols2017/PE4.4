PostgreSQL schema

Table: leads
- lead_id (uuid, primary key)
- source (text, check: telegram_bot | website_assistant)
- source_user_id (text)
- source_username (text)
- name (text)
- telegram_username (text)
- phone (text)
- email (text)
- contact_ok (boolean)
- preferred_contact_method (text, check: phone | telegram | email | both | not_specified)
- request (text)
- status (text, default: new)
- priority (text, default: normal)
- utm_source (text)
- utm_campaign (text)
- manager_note (text)
- created_at_utc (timestamptz)
- created_at_local (timestamptz)
- last_update_at_utc (timestamptz)

Constraints and indexes
- CHECK: contact_ok equals `(phone != '' OR telegram_username != '' OR email != '')`
- Index: (source, created_at_utc desc)
- Index: (status, created_at_utc desc)

Table: lead_events
- event_id (bigserial, primary key)
- lead_id (uuid, foreign key -> leads.lead_id)
- event_type (text)
- payload (jsonb)
- source (text)
- session_id (text)
- created_at_utc (timestamptz, default now)

Indexes
- Index: (lead_id, created_at_utc desc)
