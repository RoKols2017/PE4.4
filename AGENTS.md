# AGENTS.md

> Project map for AI agents. Keep this file up-to-date as the project evolves.

## Project Overview
This repository currently stores AI Factory project context and agent skills for a lead-capture product with two services: a Telegram bot and a website assistant.
The repository includes a Python Telegram bot in `bot/` and a Flask website assistant with landing widget in `web_assistant/`.

## Tech Stack
- **Language:** Python 3.12 (telegram bot + website assistant), TypeScript (experimental service scaffold)
- **Framework:** pyTelegramBotAPI (`telebot`), Flask (website assistant)
- **Database:** PostgreSQL
- **ORM:** Not used (raw SQL via psycopg)

## Project Structure
```text
.
|- .ai-factory.json            # AI Factory setup state (installed skills, MCP toggles)
|- AGENTS.md                   # This project map
|- README.md                   # Landing page for project context
|- bot/
|  |- bot.py                   # Telegram bot entrypoint
|  |- config.py                # Env parsing and settings
|  |- ai_logic.py              # OpenAI interaction wrapper
|  |- postgres_repository.py   # PostgreSQL lead persistence adapter
|  |- domain.py                # Lead validation, normalization, and field-type guards
|  |- session.py               # In-memory dialog sessions with QA flags
|  |- requirements.txt         # Python dependencies
|  `- tests/                   # Unit tests for bot modules
|- web_assistant/
|  |- app.py                   # Flask entrypoint
|  |- routes.py                # Chat, landing, and leads-view HTTP routes
|  |- ai_logic.py              # OpenAI assistant policy wrapper
|  |- postgres_repository.py   # PostgreSQL lead persistence adapter
|  |- domain.py                # Website lead validation, normalization, and field-type guards
|  |- session.py               # In-memory chat sessions with QA flags
|  |- templates/index.html     # Landing page with widget shell
|  |- templates/leads.html     # Token-protected leads viewer page
|  |- static/                  # Widget JS/CSS assets
|  |- requirements.txt         # Flask service dependencies
|  `- tests/                   # Tests for web assistant flow
|- .ai-factory/
|  |- DESCRIPTION.md           # Product and non-functional requirements
|  |- ARCHITECTURE.md          # Architecture constraints and deployment options
|  `- DATA_MODEL.md            # Domain model notes
|- db/
|  |- schema.sql               # Bootstrap SQL schema for PostgreSQL
|  `- migrations/              # Migration files
|- docs/
|  |- getting-started.md       # Setup flow and first steps
|  |- architecture.md          # Service boundaries and data flow
|  |- api.md                   # Web assistant HTTP endpoints
|  |- configuration.md         # Env vars and secret policy
|  |- deployment.md            # Docker/Caddy deployment baseline
|  |- changelog-dockerization.md # Docker stack evolution notes
|  |- ru/                      # Russian-language documentation mirror
|  `- testing.md               # Docker test workflow and smoke checks
|- infra/
|  `- caddy/
|     `- Caddyfile            # Edge reverse proxy and HTTPS config
`- .opencode/
   |- package.json             # OpenCode runtime dependencies
   |- bun.lock                 # Dependency lock file
   |- skills/                  # Installed AI Factory skills
   `- node_modules/            # Local dependencies for OpenCode tooling
```

## Key Entry Points
| File | Purpose |
|------|---------|
| `.ai-factory/DESCRIPTION.md` | Project specification and requirements source |
| `.ai-factory/ARCHITECTURE.md` | Architecture decisions and constraints |
| `bot/bot.py` | Telegram polling bot runtime |
| `bot/postgres_repository.py` | Telegram lead PostgreSQL adapter |
| `web_assistant/app.py` | Flask web assistant runtime |
| `web_assistant/routes.py` | Website assistant API, landing, and leads routes |
| `infra/caddy/Caddyfile` | Caddy edge routing, headers, and HTTPS behavior |
| `web_assistant/postgres_repository.py` | Website lead PostgreSQL adapter |
| `README.md` | Entry point for setup and docs navigation |
| `.ai-factory.json` | AI Factory metadata (skills and MCP status) |
| `.opencode/package.json` | OpenCode tooling dependencies |

## Documentation
| Document | Path | Description |
|----------|------|-------------|
| README | `README.md` | Project landing page |
| Getting Started | `docs/getting-started.md` | Setup flow and first steps |
| Architecture | `docs/architecture.md` | Service boundaries and data flow |
| API | `docs/api.md` | Web assistant HTTP endpoints |
| Configuration | `docs/configuration.md` | Env vars and secret policy |
| Deployment | `docs/deployment.md` | Docker and Caddy baseline |
| Dockerization Changelog | `docs/changelog-dockerization.md` | Docker stack change history |
| Testing | `docs/testing.md` | Docker test workflow |
| Getting Started (RU) | `docs/ru/getting-started.md` | Русский сценарий запуска |
| Architecture (RU) | `docs/ru/architecture.md` | Русская архитектура сервиса |
| API (RU) | `docs/ru/api.md` | Русское описание HTTP API |
| Configuration (RU) | `docs/ru/configuration.md` | Русские env и секреты |
| Deployment (RU) | `docs/ru/deployment.md` | Русское руководство по deploy |
| Dockerization Changelog (RU) | `docs/ru/changelog-dockerization.md` | История Docker-изменений на русском |
| Testing (RU) | `docs/ru/testing.md` | Русские тесты и smoke checks |
| Project description | `.ai-factory/DESCRIPTION.md` | Product scope and requirements |
| AI architecture notes | `.ai-factory/ARCHITECTURE.md` | Planning constraints and options |
| Data model | `.ai-factory/DATA_MODEL.md` | Lead schema notes |

## AI Context Files
| File | Purpose |
|------|---------|
| `AGENTS.md` | This file - project structure map |
| `.ai-factory/DESCRIPTION.md` | Project specification and tech context |
| `.ai-factory/ARCHITECTURE.md` | Architecture decisions and guidelines |
| `.ai-factory.json` | AI Factory setup state for this workspace |
