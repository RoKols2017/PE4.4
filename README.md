# PE4.4 Lead Capture Context

> AI Factory context for a two-channel lead capture product (Telegram bot + website assistant).

This repository stores planning context, architecture constraints, reusable AI skills,
and a Python Telegram bot implementation under `bot/`.

## Quick Start

```bash
cd bot
python3 -m pip install -r requirements.txt
python3 bot.py
```

## Key Features

- **Python Telegram bot** (`telebot`) with in-memory step-by-step lead flow
- **AI assistant replies** via OpenAI API with non-fabrication constraints
- **Google Sheets persistence** aligned to `.ai-factory/DATA_MODEL.md` (`Leads!A:R`)
- **Docker-first deployment** with nginx as reverse proxy for web traffic
- **Security baseline** for secrets, TLS headers, and request-size limits

## Example

```text
User: /start
Bot: Как вас зовут?
User: Иван
Bot: Укажите контакт...
...
Bot: Спасибо! Ваша заявка принята. Номер: <lead_id>
```

Expected result: validated lead is saved to Google Sheets with `source=telegram_bot`.

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
