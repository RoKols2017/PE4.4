# PE4.4 Lead Capture Context

> AI Factory context and implementation repository for a two-channel lead capture product.
> Контекст AI Factory и репозиторий реализации для двухканального продукта сбора лидов.

This repository contains planning context, architecture constraints, reusable AI skills, and implementations for both channels:
- Telegram bot in `bot/`
- Website assistant (Flask + landing widget) in `web_assistant/`

Этот репозиторий содержит проектный контекст, архитектурные ограничения, AI skills и реализации для двух каналов:
- Telegram-бот в `bot/`
- Веб-ассистент (Flask + landing widget) в `web_assistant/`

## Language / Язык

- English docs: `docs/`
- Русская документация: `docs/ru/`

## Quick Start / Быстрый старт

```bash
cp .env.example .env
./deploy/scripts/validate-config.sh
docker compose --profile test build telegram-bot-test web-assistant-test
docker compose --profile test run --rm telegram-bot-test
docker compose --profile test run --rm web-assistant-test
```

## Key Features / Ключевые возможности

- **Python Telegram bot** / **Telegram-бот на Python** (`telebot`) с пошаговым flow сбора заявок
- **Flask website assistant** / **Веб-ассистент на Flask** с одностраничным лендингом и chat widget
- **Protected leads viewer** / **Защищенная страница заявок** по адресу `/leads`
- **Leads API** / **API заявок** на `/api/leads` с токеном, пагинацией и фильтром `source`
- **AI recovery replies** / **AI-ответы для recovery flow** через OpenAI API без выдумывания данных
- **Structured response policy** / **Структурированный response_policy** с JSON-контрактом для `gpt-4o-mini`
- **Deterministic validation guards** / **Детерминированные проверки** для `name/contact/request`
- **Shared PostgreSQL persistence** / **Общее хранилище PostgreSQL** в `leads` и `lead_events`
- **Docker-first deployment with Caddy** / **Docker-first развертывание с Caddy и HTTPS**

## Example / Пример

```text
User opens landing chat widget
Assistant: Как вас зовут?
User: Иван
Assistant: Укажите контакт (телефон или email)...
...
Assistant: Спасибо! Заявка отправлена. Номер: <lead_id>
```

Expected result / Ожидаемый результат: validated lead is saved to PostgreSQL with `source=website_assistant`.

Data quality note / Примечание по качеству данных: intro phrases in names (for example `"я Вовочка"`) are normalized before save, and repeated invalid attempts are tracked in `lead_events.payload` (`qa_flags`, `offscript_count`).

Leads UI access / Доступ к UI заявок: `/leads?token=<LEADS_VIEW_TOKEN>`

## Documentation / Документация

### English

| Guide | Description |
|-------|-------------|
| [Getting Started](docs/getting-started.md) | Setup flow and first AI Factory steps |
| [Architecture](docs/architecture.md) | Service boundaries and data flow |
| [Workflow](docs/workflow.md) | Lead capture flow for web and Telegram |
| [API](docs/api.md) | Web assistant HTTP endpoints |
| [Configuration](docs/configuration.md) | Environment variables and secrets policy |
| [Deployment](docs/deployment.md) | Docker and Caddy deployment baseline |
| [Dockerization Changelog](docs/changelog-dockerization.md) | Historical notes about the Docker stack evolution |
| [Testing](docs/testing.md) | Docker-based test workflow |

### Русский

| Раздел | Описание |
|--------|----------|
| [Быстрый старт](docs/ru/getting-started.md) | Сценарий запуска и первые шаги |
| [Архитектура](docs/ru/architecture.md) | Границы сервисов и поток данных |
| [Workflow](docs/ru/workflow.md) | Flow сбора заявок на сайте и в Telegram |
| [API](docs/ru/api.md) | HTTP endpoint'ы веб-ассистента |
| [Конфигурация](docs/ru/configuration.md) | Переменные окружения и политика секретов |
| [Развертывание](docs/ru/deployment.md) | Docker и Caddy для production |
| [История dockerизации](docs/ru/changelog-dockerization.md) | История эволюции Docker-стека |
| [Тестирование](docs/ru/testing.md) | Тесты и smoke checks в Docker |

## License / Лицензия

No license file is defined in this repository yet.
Файл лицензии в репозитории пока не добавлен.
