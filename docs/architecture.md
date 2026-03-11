[← Getting Started](getting-started.md) · [Back to README](../README.md) · [API →](api.md)

# Architecture

## Service Model

The target system has two application services and one edge component:

- `telegram-bot`: collects leads from Telegram chat flows
- `web-assistant`: collects leads from website conversations and serves protected leads viewer UI
- `nginx`: public HTTPS entry point for web traffic

## Boundary Rules

- Public inbound traffic is allowed only through `nginx`.
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
- Wrong-field inputs stay on the same step and get a retry prompt plus AI-generated recovery text.
- Final confirmation persists the lead and resets the session state.

## TLS Strategy

One strategy must be fixed before implementation planning:

1. `certbot` + Let's Encrypt managed at nginx level
2. external certificate/ingress management (for example cloud edge)

## See Also

- [Getting Started](getting-started.md) - first-session workflow
- [API](api.md) - route surface and response shapes
- [Configuration](configuration.md) - env vars and secrets
- [Deployment](deployment.md) - Docker network and runtime baseline
