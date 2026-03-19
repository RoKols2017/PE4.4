[← API](api.md) · [Back to README](../README.md) · [Deployment →](deployment.md)

# Configuration

## Configuration Principles

- Use environment variables for all runtime settings.
- Keep secrets out of git history.
- Keep defaults safe for local development.

## Core Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `LOG_LEVEL` | No | Log verbosity (`info` by default) |
| `TELEGRAM_BOT_TOKEN` | Yes (bot) | Telegram API access |
| `OPENAI_API_KEY` | Yes (bot) | OpenAI API authentication |
| `OPENAI_MODEL` | No | LLM model for dialog prompts |
| `DATABASE_URL` | Yes | PostgreSQL DSN for both services |
| `POSTGRES_DB` | Yes (compose) | PostgreSQL database name |
| `POSTGRES_USER` | Yes (compose) | PostgreSQL user |
| `POSTGRES_PASSWORD` | Yes (compose) | PostgreSQL password |
| `DB_CONNECT_TIMEOUT_SECONDS` | No | PostgreSQL connection timeout |
| `LOCAL_TIMEZONE` | No | Local timezone for `created_at_local` |
| `MAX_RETRY_ATTEMPTS` | No | Retry count for PostgreSQL writes |
| `RETRY_DELAY_SECONDS` | No | Delay between write retries |
| `WEB_ASSISTANT_HOST` | No | Flask bind host (`0.0.0.0`) |
| `WEB_ASSISTANT_PORT` | No | Flask bind port (`5000`) |
| `LEADS_VIEW_TOKEN` | Yes (web UI) | Access token for `/leads` and `/api/leads` |
| `CADDY_SITE_HOST` | Yes (prod) | Public HTTPS host name served by Caddy |
| `CADDY_HTTP_PORT` | No | Host port published for HTTP (`80`) |
| `CADDY_HTTPS_PORT` | No | Host port published for HTTPS (`443`) |
| `CADDY_LOG_LEVEL` | No | Caddy runtime log level (`INFO`) |
| `MAX_REQUEST_SIZE` | No | Request size guard for web ingress |

## Secrets Policy

- Do not commit database credentials.
- Prefer secret stores or CI/CD secret injection in production.
- Use local `.env` only for development, never for production deployment history.
- Website and Telegram services share one PostgreSQL database schema (`leads`, `lead_events`).
- `CADDY_SITE_HOST` must resolve to the VPS public IP before first HTTPS issuance.
- Leads viewer endpoints (`/leads`, `/api/leads`) require `LEADS_VIEW_TOKEN`.

## Local Configuration Workflow

1. Define local variables in a non-committed `.env`.
2. Validate all required variables before bootstrapping services.
3. Start with minimal privileges for external integrations.

## Logging and Error Handling

- Emit structured logs to stdout.
- Keep personally identifiable information masked where possible.
- Keep user-facing errors clear and operational errors detailed in logs.
- Correlate service logs by `lead_id` and `session_id` where available.
- Include `step`, `validation_hint`, and `offscript_count` in debug flow logs for dialog diagnostics.
- Recommended log level: `DEBUG` for local development and dialog-quality troubleshooting, `INFO` for production.

## Data Quality Rules

- Name is normalized before save (intro phrases like `"я ..."` are stripped).
- Contact step rejects free-form request text and asks for phone/email (web) or phone/Telegram (bot).
- Request step rejects contact-like input and asks for short task description.
- Quality markers are persisted in `lead_events.payload` (`qa_flags`, `offscript_count`).

## See Also

- [Getting Started](getting-started.md) - setup and execution flow
- [API](api.md) - routes guarded by runtime config
- [Architecture](architecture.md) - service boundaries
