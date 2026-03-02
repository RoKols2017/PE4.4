[Back to README](../README.md) · [Architecture →](architecture.md)

# Getting Started

## What Is In This Repository

This workspace contains AI Factory context and a working Python Telegram bot implementation.
The web-assistant service is still a placeholder container.

## Prerequisites

| Tool | Why it is needed |
|------|------------------|
| Python 3.12 | Run telegram-bot service and tests |
| Docker + Docker Compose | Planned runtime for bot, web, and nginx |
| Telegram bot token | Required when implementing bot integration |
| Google service account | Required for Google Sheets storage |

## First Session Flow

1. Copy env template: `cp bot/.env.example bot/.env`.
2. Fill `TELEGRAM_BOT_TOKEN`, `GOOGLE_SHEETS_ID`, `GOOGLE_SERVICE_ACCOUNT_JSON`.
3. Install dependencies: `cd bot && python3 -m pip install -r requirements.txt`.
4. Run locally: `python3 bot.py`.
5. Optionally run tests: `python3 -m pytest tests`.
6. For container run, align compose service with `bot/` runtime.

## Quick Verification

Use this checklist before implementation starts:

- `AGENTS.md` exists and matches current structure
- `.ai-factory/DESCRIPTION.md` reflects current business scope
- `.ai-factory/ARCHITECTURE.md` captures deployment decisions
- Required skills are present in `.ai-factory.json`
- `bot/.env` contains valid secrets

## Next Step

Continue with architecture details and service boundaries in `docs/architecture.md`.

## See Also

- [Architecture](architecture.md) - service boundaries and flow
- [Configuration](configuration.md) - env vars and secret handling
- [Deployment](deployment.md) - runtime and rollout baseline
