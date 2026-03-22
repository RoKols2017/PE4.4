[← Getting Started](getting-started.md) · [Back to README](../README.md) · [Workflow →](workflow.md)

# Architecture

## Service Model

The target system has two application services and one edge component:

- `telegram-bot`: collects leads from Telegram chat flows
- `web-assistant`: collects leads from website conversations and serves protected leads viewer UI
- `caddy`: public HTTPS entry point for web traffic

## Boundary Rules

- Public inbound traffic is allowed only through `caddy`.
- `web-assistant` is internal HTTP-only service behind reverse proxy.
- `telegram-bot` can work as outbound polling client without open inbound port.

## Shared Domain

Both channels use a shared `Lead` model:

| Field | Notes |
|-------|-------|
| `name` | Lead name |
| `telegram_username` | Optional contact |
| `phone` | Optional contact |
| `email` | Optional web contact |
| `request` | Free-form request text |
| `source` | `telegram_bot` or `website_assistant` |

Validation rule: at least one contact must be provided. For Telegram that means `phone` or `telegram_username`; for web that means `phone` or `email`.

Name inputs are normalized before persistence (for example `"я Вовочка"` -> `"Вовочка"`).
If a value looks like the wrong field type (contact in request field, request text in contact field),
the flow keeps the current step and asks for corrected input.

### Website Contact Model

Website assistant collects `phone` or `email` and stores both as first-class columns in PostgreSQL.
`source` is always `website_assistant` for web channel rows.

## Data and Observability

- Primary storage: PostgreSQL with tables `leads` and `lead_events`.
- Read path: web-assistant provides `/api/leads` + `/leads` (token-protected) for operations visibility.
- Data quality events: `lead_events.payload` stores `qa_flags` and `offscript_count` for diagnostics.
- Logs: all services write to stdout for container aggregation.
- Correlation: include `lead_id` and/or `session_id` in logs where possible.

## Dialog Flow

- `telegram-bot`: `/start` or `/new` resets the in-memory session and starts the collection flow.
- `web-assistant`: `POST /api/chat/start` issues `session_id` and begins the same four-step flow.
- Validation happens before save on every step: `name`, `contact`, `request`, `confirm`.
- A narrow `response_policy` layer sits above the FSM: the model may return structured intent, candidate fields, and a short user-facing message, but it never owns transitions, validation, or persistence.
- Wrong-field inputs stay on the same step and get a retry prompt resolved by backend validators plus deterministic fallback copy.
- Final confirmation persists the lead and resets the session state.

## Runtime AI Boundary

- Runtime model output is constrained to a small JSON contract.
- Backend validators remain the source of truth for `name`, `contact`, and `request`.
- Candidate fields extracted by the model are treated as hints only and are checked field-by-field before draft mutation.
- Deterministic resolver code decides partial accepts, retries, confirm edits, and save/no-save outcomes.

## TLS Strategy

TLS is managed by Caddy directly:

1. `CADDY_SITE_HOST` points to the public domain on the VPS.
2. Caddy terminates HTTPS, redirects HTTP to HTTPS, and stores ACME material in Docker volumes.
3. `web-assistant` stays HTTP-only on the internal Docker network.

## See Also

- [Getting Started](getting-started.md) - first-session workflow
- [Workflow](workflow.md) - lead capture flow and improvement ideas
- [API](api.md) - route surface and response shapes
