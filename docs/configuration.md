[← Architecture](architecture.md) · [Back to README](../README.md) · [Deployment →](deployment.md)

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
| `GOOGLE_SHEETS_ID` | Yes | Target spreadsheet identifier |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Yes | Service account credentials payload or path |
| `GOOGLE_SHEET_NAME` | No | Sheet name for lead rows (`Leads`) |
| `LOCAL_TIMEZONE` | No | Local timezone for `created_at_local` |
| `MAX_RETRY_ATTEMPTS` | No | Retry count for Google Sheets writes |
| `RETRY_DELAY_SECONDS` | No | Delay between write retries |
| `WEB_ASSISTANT_HOST` | No | Flask bind host (`0.0.0.0`) |
| `WEB_ASSISTANT_PORT` | No | Flask bind port (`5000`) |
| `WEB_PORT` | No | Internal web service port (example: `8000`) |
| `NGINX_SERVER_NAME` | Yes (prod) | Public HTTPS host name |
| `MAX_REQUEST_SIZE` | No | Request size guard for web ingress |

## Secrets Policy

- Do not commit service account JSON files.
- Prefer secret stores or CI/CD secret injection in production.
- Use local `.env` only for development, never for production deployment history.
- Website and Telegram services share one Google sheet (`GOOGLE_SHEET_NAME=Leads`).
- Website email values are written to shared column H as `email:<value>` for schema compatibility.

## Local Configuration Workflow

1. Define local variables in a non-committed `.env`.
2. Validate all required variables before bootstrapping services.
3. Start with minimal privileges for external integrations.

## Logging and Error Handling

- Emit structured logs to stdout.
- Keep personally identifiable information masked where possible.
- Keep user-facing errors clear and operational errors detailed in logs.

## See Also

- [Getting Started](getting-started.md) - setup and execution flow
- [Architecture](architecture.md) - service boundaries
- [Deployment](deployment.md) - runtime configuration in containers
