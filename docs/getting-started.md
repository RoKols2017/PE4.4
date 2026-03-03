[Back to README](../README.md) · [Architecture →](architecture.md)

# Getting Started

## What Is In This Repository

This workspace contains AI Factory context, a Python Telegram bot, and a Flask website assistant.

## Prerequisites

| Tool | Why it is needed |
|------|------------------|
| Python 3.12 | Run telegram-bot service and tests |
| Docker + Docker Compose | Runtime for bot, web, and nginx |
| Telegram bot token | Required when implementing bot integration |
| Google service account | Required for Google Sheets storage |
| OpenAI API key | Required for website assistant AI responses |

## First Session Flow

1. Copy root env template: `cp .env.example .env`.
2. Fill `TELEGRAM_BOT_TOKEN`, `OPENAI_API_KEY`, `GOOGLE_SHEETS_ID`, `GOOGLE_SERVICE_ACCOUNT_JSON` in `.env`.
3. Validate compose config: `docker compose --env-file .env -f compose.yml -f compose.override.yml config`.
4. Build and run full dev stack: `docker compose --env-file .env -f compose.yml -f compose.override.yml up --build -d`.
5. Run tests in Docker:
   - `docker compose --env-file .env -f compose.yml -f compose.override.yml --profile test run --rm telegram-bot-test`
   - `docker compose --env-file .env -f compose.yml -f compose.override.yml --profile test run --rm web-assistant-test`
6. Open edge endpoint: `http://localhost:8080`.

## Quick Verification

Use this checklist before implementation starts:

- `AGENTS.md` exists and matches current structure
- `.ai-factory/DESCRIPTION.md` reflects current business scope
- `.ai-factory/ARCHITECTURE.md` captures deployment decisions
- Required skills are present in `.ai-factory.json`
- `.env` contains valid secrets

## Next Step

Continue with architecture details and service boundaries in `docs/architecture.md`.

## See Also

- [Architecture](architecture.md) - service boundaries and flow
- [Configuration](configuration.md) - env vars and secret handling
- [Deployment](deployment.md) - runtime and rollout baseline
