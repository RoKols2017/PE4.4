[← Architecture](architecture.md) · [Back to README](../README.md) · [Configuration →](configuration.md)

# API

## Scope

This project exposes HTTP endpoints from `web_assistant` only. The Telegram bot has no public HTTP API.

## Base URL

- Local through nginx: `http://localhost:8080`
- Direct Flask container in dev override: `http://localhost:5000`

## Authentication

| Surface | Auth |
|--------|------|
| `/api/chat/*` | none |
| `/health` | none |
| `/leads` | `token` query param |
| `/api/leads` | `X-Leads-View-Token` header or `token` query param |

If `LEADS_VIEW_TOKEN` is missing, leads-view endpoints return `503` with `{"error": "leads_view_not_configured"}`.

## Endpoints

### `GET /`

Returns the landing page with the embedded assistant widget.

### `GET /health`

Health endpoint used by Docker health checks.

Response:

```json
{"status": "ok"}
```

### `POST /api/chat/start`

Starts a new website assistant session.

Headers:

- Optional `X-Session-Id`: reuse an existing client session id

Response fields:

- `session_id`
- `step`
- `assistant_message`
- `typing`

### `POST /api/chat/message`

Processes a user message for the current step.

Headers:

- `X-Session-Id`: client session correlation id

Body:

```json
{"message": "Иван"}
```

Behavior:

- Empty message returns `400` with `{"error": "message_required"}`
- Valid input advances the flow to the next step
- Invalid input keeps the current step and returns retry guidance
- Final `да` saves the lead and returns a confirmation with generated `lead_id`
- Final `нет` resets the flow back to `name`

### `GET /leads`

Returns the protected leads viewer HTML page.

Example:

```text
/leads?token=<LEADS_VIEW_TOKEN>
```

### `GET /api/leads`

Returns paginated lead records from PostgreSQL.

Supported query params:

| Param | Default | Notes |
|------|---------|-------|
| `limit` | `20` | `1..100` |
| `offset` | `0` | `>= 0` |
| `source` | none | `telegram_bot` or `website_assistant` |

Success response shape:

```json
{
  "items": [],
  "pagination": {"limit": 20, "offset": 0, "total": 0},
  "source": "all"
}
```

Error codes:

- `401` -> `{"error": "unauthorized"}`
- `400` -> `{"error": "invalid_pagination"}` or `{"error": "invalid_pagination_range"}` or `{"error": "invalid_source"}`
- `500` -> `{"error": "leads_read_failed"}`

### `POST /api/client-log`

Accepts client-side widget telemetry and logs it server-side.

Body shape:

```json
{"event": "widget_opened", "details": {"source": "landing"}}
```

Response:

```json
{"ok": true}
```

## See Also

- [Architecture](architecture.md) - service boundaries and flow ownership
- [Configuration](configuration.md) - auth and env requirements
- [Testing](testing.md) - endpoint verification in Docker
