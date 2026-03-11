Product
- Два сервиса: telegram-bot и web-assistant (сайт с чат-виджетом).
- Оба запускаются в Docker, внешний вход для сайта через nginx reverse proxy.
- Хранилище заявок: PostgreSQL, единая схема для обоих каналов.

Tech stack
- Telegram bot: Python 3.12, pyTelegramBotAPI, OpenAI API.
- Website assistant: Python 3.12, Flask, OpenAI API.
- Интеграция с БД: PostgreSQL (psycopg), bootstrap DDL в `db/schema.sql`.

Functional
- Общая доменная модель Lead: `name`, контакт, `request`, `source`, метаданные.
- Обязательное правило: хотя бы один контакт.
- Источник заявки: `source = telegram_bot | website_assistant`.
- Контакт для сайта: телефон или email.
- Email сайта сохраняется в отдельную колонку `email` в PostgreSQL.
- Ассистент ведет пошаговый диалог и мягко возвращает пользователя к сценарию при отклонении.
- Web service отдает token-protected leads UI (`/leads`) и JSON API (`/api/leads`) для просмотра заявок.
- На каждом канале есть детерминированные проверки для `name`, `contact`, `request`; LLM используется только для recovery-ответов.
- Нормализация имени удаляет вводные фразы вроде `я ...` перед сохранением.
- Диагностика качества диалога сохраняется в `lead_events.payload` через `qa_flags` и `offscript_count`.

Website UX
- Лендинг одностраничный, чат-виджет всегда доступен справа внизу.
- Виджет: темный нейтральный стиль, автопрокрутка, индикатор "ассистент печатает".

Non-functional
- Конфиги только через env/.env (локально), секреты в env/secret в контейнерах.
- Логи в stdout, уровень через `LOG_LEVEL`, с корреляцией по `lead_id/session_id`.
- Для локальной отладки рекомендован `LOG_LEVEL=DEBUG`, для production — `LOG_LEVEL=INFO`.
- Session state in-memory на первом этапе (сброс при рестарте допустим).
- Тесты проекта запускаются в Docker через compose profile `test`.

Security
- Ключи и пароль БД не коммитить.
- Nginx: sane headers, лимит размера запроса, TLS/redirect стратегия по окружению.

ai-factory ожидает короткое и однозначное описание, чтобы планирование было предсказуемым.
