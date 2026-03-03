[← Getting Started](getting-started.md) · [Back to README](../README.md) · [Configuration →](configuration.md)

# Architecture

## Service Model

The target system has two application services and one edge component:

- `telegram-bot`: collects leads from Telegram chat flows
- `web-assistant`: collects leads from website conversations
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
| `request` | Free-form request text |
| `source` | `telegram_bot` or `website_assistant` |

Validation rule: at least one contact must be provided (`telegram_username` or `phone`).

### Website Contact Model

Website assistant collects `phone` or `email` and stores both as first-class columns in PostgreSQL.
`source` is always `website_assistant` for web channel rows.

## Data and Observability

- Primary storage: PostgreSQL with tables `leads` and `lead_events`.
- Read path: web-assistant provides `/api/leads` + `/leads` (token-protected) for operations visibility.
- Logs: all services write to stdout for container aggregation.
- Correlation: include `lead_id` and/or `session_id` in logs where possible.

## TLS Strategy

One strategy must be fixed before implementation planning:

1. `certbot` + Let's Encrypt managed at nginx level
2. external certificate/ingress management (for example cloud edge)

## See Also

- [Getting Started](getting-started.md) - first-session workflow
- [Configuration](configuration.md) - env vars and secrets
- [Deployment](deployment.md) - Docker network and runtime baseline
