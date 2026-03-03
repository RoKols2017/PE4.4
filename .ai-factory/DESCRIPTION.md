Product
- Два сервиса: telegram-bot и web-assistant (сайт с чат-виджетом).
- Оба запускаются в Docker, внешний вход для сайта через nginx reverse proxy.
- Хранилище заявок: PostgreSQL, единая схема для обоих каналов.

Tech stack
- Telegram bot: Python 3.12, pyTelegramBotAPI, OpenAI API.
- Website assistant: Python 3.12, Flask, OpenAI API.
- Интеграция с БД: PostgreSQL (psycopg), DDL + миграции в `db/migrations`.

Functional
- Общая доменная модель Lead: `name`, контакт, `request`, `source`, метаданные.
- Обязательное правило: хотя бы один контакт.
- Источник заявки: `source = telegram_bot | website_assistant`.
- Контакт для сайта: телефон или email.
- Email сайта сохраняется в отдельную колонку `email` в PostgreSQL.
- Ассистент ведет пошаговый диалог и мягко возвращает пользователя к сценарию при отклонении.

Website UX
- Лендинг одностраничный, чат-виджет всегда доступен справа внизу.
- Виджет: темный нейтральный стиль, автопрокрутка, индикатор "ассистент печатает".

Non-functional
- Конфиги только через env/.env (локально), секреты в env/secret в контейнерах.
- Логи в stdout, уровень через `LOG_LEVEL`, с корреляцией по `lead_id/session_id`.
- Session state in-memory на первом этапе (сброс при рестарте допустим).

Security
- Ключи и пароль БД не коммитить.
- Nginx: sane headers, лимит размера запроса, TLS/redirect стратегия по окружению.

ai-factory ожидает короткое и однозначное описание, чтобы планирование было предсказуемым.
