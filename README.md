# PE4.4 Lead Capture Context

> AI Factory context for a two-channel lead capture product (Telegram bot + website assistant).

This repository stores planning context, architecture constraints, reusable AI skills,
and implementations for both channels:
- Telegram bot in `bot/`
- Website assistant (Flask + landing widget) in `web_assistant/`

## Quick Start

```bash
docker compose --profile test build telegram-bot-test web-assistant-test
docker compose --profile test run --rm telegram-bot-test
docker compose --profile test run --rm web-assistant-test
```

## Key Features

- **Python Telegram bot** (`telebot`) with in-memory step-by-step lead flow
- **Flask website assistant** with one-page landing and embedded chat widget
- **AI assistant replies** via OpenAI API with non-fabrication constraints
- **Shared Google Sheets persistence** for both sources in `Leads!A:R`
- **Docker-first deployment** with nginx as reverse proxy for web traffic
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

Expected result: validated lead is saved to shared Google Sheets with `source=website_assistant`.

---

## Documentation

| Guide | Description |
|-------|-------------|
| [Getting Started](docs/getting-started.md) | Setup flow and first AI Factory steps |
| [Architecture](docs/architecture.md) | Service boundaries and data flow |
| [Configuration](docs/configuration.md) | Environment variables and secrets policy |
| [Deployment](docs/deployment.md) | Docker and nginx deployment baseline |

## License

No license file is defined in this repository yet.
