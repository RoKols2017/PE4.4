# AGENTS.md

> Project map for AI agents. Keep this file up-to-date as the project evolves.

## Project Overview
This repository currently stores AI Factory project context and agent skills for a lead-capture product with two services: a Telegram bot and a website assistant.
The repository includes a Python Telegram bot in `bot/` and a Flask website assistant with landing widget in `web_assistant/`.

## Tech Stack
- **Language:** Python 3.12 (telegram bot + website assistant), TypeScript (experimental service scaffold)
- **Framework:** pyTelegramBotAPI (`telebot`), Flask (website assistant)
- **Database:** Google Sheets (from `.ai-factory/DESCRIPTION.md`)
- **ORM:** Not applicable (based on current project description)

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
|  |- sheets.py                # Google Sheets schema + append logic
|  |- domain.py                # Lead validation and normalization
|  |- session.py               # In-memory dialog sessions
|  |- requirements.txt         # Python dependencies
|  `- tests/                   # Unit tests for bot modules
|- web_assistant/
|  |- app.py                   # Flask entrypoint
|  |- routes.py                # Chat and landing HTTP routes
|  |- ai_logic.py              # OpenAI assistant policy wrapper
|  |- sheets.py                # Shared Google Sheets write adapter
|  |- domain.py                # Website lead validation contract
|  |- session.py               # In-memory chat sessions
|  |- templates/index.html     # Landing page with widget shell
|  |- static/                  # Widget JS/CSS assets
|  |- requirements.txt         # Flask service dependencies
|  `- tests/                   # Tests for web assistant flow
|- .ai-factory/
|  |- DESCRIPTION.md           # Product and non-functional requirements
|  |- ARCHITECTURE.md          # Architecture constraints and deployment options
|  `- DATA_MODEL.md            # Domain model notes
|- docs/
|  |- getting-started.md       # Setup flow and first steps
|  |- architecture.md          # Service boundaries and data flow
|  |- configuration.md         # Env vars and secret policy
|  `- deployment.md            # Docker/nginx deployment baseline
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
| `bot/sheets.py` | Google Sheets persistence adapter |
| `web_assistant/app.py` | Flask web assistant runtime |
| `web_assistant/routes.py` | Website assistant API and landing routes |
| `README.md` | Entry point for setup and docs navigation |
| `.ai-factory.json` | AI Factory metadata (skills and MCP status) |
| `.opencode/package.json` | OpenCode tooling dependencies |

## Documentation
| Document | Path | Description |
|----------|------|-------------|
| README | `README.md` | Project landing page |
| Getting Started | `docs/getting-started.md` | Setup flow and first steps |
| Architecture | `docs/architecture.md` | Service boundaries and data flow |
| Configuration | `docs/configuration.md` | Env vars and secret policy |
| Deployment | `docs/deployment.md` | Docker and nginx baseline |
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
