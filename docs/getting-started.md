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
| PostgreSQL | Required as primary lead storage |
| OpenAI API key | Required for website assistant AI responses |

## First Session Flow

1. Copy root env template: `cp .env.example .env`.
2. Fill `TELEGRAM_BOT_TOKEN`, `OPENAI_API_KEY`, `DATABASE_URL`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `LEADS_VIEW_TOKEN` in `.env`.
3. Validate compose config: `docker compose --env-file .env -f compose.yml -f compose.override.yml config`.
4. Build and run full dev stack: `docker compose --env-file .env -f compose.yml -f compose.override.yml up --build -d`.
5. Run tests in Docker (default verification path for this project):
   - `docker compose --env-file .env -f compose.yml -f compose.override.yml --profile test run --rm telegram-bot-test`
   - `docker compose --env-file .env -f compose.yml -f compose.override.yml --profile test run --rm web-assistant-test`
6. Open edge endpoint: `http://localhost:8080`.
7. Open leads viewer: `http://localhost:8080/leads?token=<LEADS_VIEW_TOKEN>`.

## First Checks After Boot

- `GET /health` through nginx should return `{"status": "ok"}`.
- `GET /api/leads` without token should return `401`.
- `GET /api/leads` with `X-Leads-View-Token` should return paginated JSON.
- Telegram bot should answer `/start` and continue with `name -> contact -> request -> confirm` flow.

## Quick Verification

Use this checklist before implementation starts:

- `AGENTS.md` exists and matches current structure
- `.ai-factory/DESCRIPTION.md` reflects current business scope
- `.ai-factory/ARCHITECTURE.md` captures deployment decisions
- Required skills are present in `.ai-factory.json`
- `.env` contains valid secrets

## Dialog Quality Smoke Checks

Run a quick manual check after startup:

- Name normalization: send `"я Вовочка"` and ensure summary contains `"Вовочка"`.
- Contact guard: on contact step send `"Хочу лендинг"` and ensure assistant asks for contact again.
- Request guard: on request step send `"+79990001122"` or `"user@example.com"` and ensure assistant asks for request text.
- Confirm that successful lead save writes diagnostics in `lead_events.payload` (`qa_flags`, `offscript_count`).

## Next Step

Continue with architecture details and service boundaries in `docs/architecture.md`.

## See Also

- [Architecture](architecture.md) - service boundaries and flow
- [API](api.md) - HTTP routes and payloads
- [Configuration](configuration.md) - env vars and secret handling
- [Deployment](deployment.md) - runtime and rollout baseline
