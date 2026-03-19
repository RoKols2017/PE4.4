# PE4.4 Lead Capture Context

> AI Factory context for a two-channel lead capture product (Telegram bot + website assistant).

This repository stores planning context, architecture constraints, reusable AI skills,
and implementations for both channels:
- Telegram bot in `bot/`
- Website assistant (Flask + landing widget) in `web_assistant/`

## Quick Start

```bash
cp .env.example .env
./deploy/scripts/validate-config.sh
docker compose --profile test build telegram-bot-test web-assistant-test
docker compose --profile test run --rm telegram-bot-test
docker compose --profile test run --rm web-assistant-test
```

## Key Features

- **Python Telegram bot** (`telebot`) with in-memory step-by-step lead flow
- **Flask website assistant** with one-page landing and embedded chat widget
- **Protected leads viewer page** at `/leads` for PostgreSQL records
- **Leads API** at `/api/leads` with token auth, pagination, and source filter
- **AI assistant replies** via OpenAI API with non-fabrication constraints
- **Deterministic validation guards** for `name/contact/request` with LLM used only for recovery prompts
- **Shared PostgreSQL persistence** for both sources in `leads` + `lead_events`
- **Docker-first deployment** with Caddy as reverse proxy and automatic HTTPS for web traffic
- **Security baseline** for secrets, TLS headers, and request-size limits

## Example

```text
User opens landing chat widget
Assistant: Как вас зовут?
User: Иван
Assistant: Укажите контакт (телефон или email)...
...
Assistant: Спасибо! Заявка отправлена. Номер: <lead_id>
```

Expected result: validated lead is saved to PostgreSQL with `source=website_assistant`.

Data quality note: intro phrases in names (for example `"я Вовочка"`) are normalized before save,
and repeated invalid attempts are tracked in `lead_events.payload` (`qa_flags`, `offscript_count`).

Leads UI access: open `/leads?token=<LEADS_VIEW_TOKEN>`.
Leads API access: send `X-Leads-View-Token: <LEADS_VIEW_TOKEN>` to `/api/leads`.

---

## Documentation

| Guide | Description |
|-------|-------------|
| [Getting Started](docs/getting-started.md) | Setup flow and first AI Factory steps |
| [Architecture](docs/architecture.md) | Service boundaries and data flow |
| [API](docs/api.md) | Web assistant HTTP endpoints |
| [Configuration](docs/configuration.md) | Environment variables and secrets policy |
| [Deployment](docs/deployment.md) | Docker and Caddy deployment baseline |
| [Dockerization Changelog](docs/changelog-dockerization.md) | Historical notes about the Docker stack evolution |
| [Testing](docs/testing.md) | Docker-based test workflow |

## License

No license file is defined in this repository yet.
