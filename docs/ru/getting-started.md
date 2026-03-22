[Назад к README](../../README.md) · [Архитектура →](architecture.md)

# Быстрый старт

Английская версия: [Getting Started](../getting-started.md)

## Что находится в репозитории

В этом репозитории хранятся AI Factory контекст, Telegram-бот на Python и веб-ассистент на Flask.

## Предварительные требования

| Инструмент | Зачем нужен |
|------------|-------------|
| Python 3.12 | Опциональный локальный запуск вне Docker |
| Docker + Docker Compose | Основная среда запуска для бота, веб-сервиса, PostgreSQL и Caddy |
| Telegram bot token | Нужен для интеграции Telegram-бота |
| OpenAI API key | Нужен для ответов веб-ассистента |

## Первый запуск

1. Скопируйте шаблон env: `cp .env.example .env`.
2. Заполните в `.env` значения `TELEGRAM_BOT_TOKEN`, `OPENAI_API_KEY`, `DATABASE_URL`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `LEADS_VIEW_TOKEN` и `CADDY_SITE_HOST`.
3. Проверьте compose- и Caddy-конфиг: `./deploy/scripts/validate-config.sh`.
4. Поднимите dev-стек: `docker compose --env-file .env -f compose.yml -f compose.override.yml up --build -d`.
5. Запустите тесты в Docker:
   - `docker compose --env-file .env -f compose.yml -f compose.override.yml --profile test run --rm telegram-bot-test`
   - `docker compose --env-file .env -f compose.yml -f compose.override.yml --profile test run --rm web-assistant-test`
6. Откройте edge endpoint: `http://localhost:8080`.
7. При необходимости проверьте локальный HTTPS: `https://localhost:8443`.
8. Откройте страницу заявок: `http://localhost:8080/leads?token=test-token`.

## Первые проверки после запуска

- `GET /health` через Caddy должен вернуть `{"status": "ok"}`.
- `GET /api/leads` без токена должен вернуть `401`.
- `GET /api/leads` с `X-Leads-View-Token` должен вернуть JSON с пагинацией.
- Telegram-бот должен отвечать на `/start` и проходить шаги `name -> contact -> request -> confirm`.

## Быстрая самопроверка

- `AGENTS.md` существует и отражает текущую структуру проекта.
- `.ai-factory/DESCRIPTION.md` описывает актуальный продуктовый scope.
- `.ai-factory/ARCHITECTURE.md` содержит текущие решения по развертыванию.
- В `.ai-factory.json` доступны нужные skills.
- В `.env` заполнены рабочие секреты.

## Smoke-check качества диалога

- На шаге имени отправьте `"я Вовочка"` и убедитесь, что в summary сохраняется `"Вовочка"`.
- На шаге контакта отправьте `"Хочу лендинг"` и убедитесь, что ассистент повторно просит контакт.
- На шаге запроса отправьте `"+79990001122"` или `"user@example.com"` и убедитесь, что ассистент просит описать задачу.
- Проверьте, что после успешного сохранения лида в `lead_events.payload` есть `qa_flags` и `offscript_count`.

## Следующий шаг

Дальше переходите к описанию архитектуры в `docs/ru/architecture.md`.

## См. также

- [Архитектура](architecture.md) - границы сервисов и поток данных
- [API](api.md) - HTTP-маршруты и форматы ответов
- [Конфигурация](configuration.md) - env-переменные и секреты
