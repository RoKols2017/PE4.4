[← API](api.md) · [Назад к README](../../README.md) · [Развертывание →](deployment.md)

# Конфигурация

Английская версия: [Configuration](../configuration.md)

## Принципы конфигурации

- Все runtime-настройки задаются через переменные окружения.
- Секреты не должны попадать в git history.
- Значения по умолчанию должны быть безопасными для локальной разработки.

## Основные переменные окружения

| Переменная | Обязательна | Назначение |
|------------|-------------|------------|
| `LOG_LEVEL` | Нет | Уровень логирования (`info` по умолчанию) |
| `TELEGRAM_BOT_TOKEN` | Да (bot) | Доступ к Telegram API |
| `OPENAI_API_KEY` | Да (bot/web) | Аутентификация в OpenAI API |
| `OPENAI_MODEL` | Нет | LLM-модель для recovery prompt'ов |
| `DATABASE_URL` | Да | PostgreSQL DSN для обоих сервисов |
| `POSTGRES_DB` | Да (compose) | Имя базы PostgreSQL |
| `POSTGRES_USER` | Да (compose) | Пользователь PostgreSQL |
| `POSTGRES_PASSWORD` | Да (compose) | Пароль PostgreSQL |
| `DB_CONNECT_TIMEOUT_SECONDS` | Нет | Таймаут подключения к PostgreSQL |
| `LOCAL_TIMEZONE` | Нет | Локальный timezone для `created_at_local` |
| `MAX_RETRY_ATTEMPTS` | Нет | Количество повторов записи в PostgreSQL |
| `RETRY_DELAY_SECONDS` | Нет | Задержка между повторными попытками |
| `WEB_ASSISTANT_HOST` | Нет | Flask bind host (`0.0.0.0`) |
| `WEB_ASSISTANT_PORT` | Нет | Flask bind port (`5000`) |
| `LEADS_VIEW_TOKEN` | Да (web UI) | Токен доступа к `/leads` и `/api/leads` |
| `CADDY_SITE_HOST` | Да (prod) | Публичный HTTPS-домен для Caddy |
| `CADDY_HTTP_PORT` | Нет | Порт HTTP на хосте (`80`) |
| `CADDY_HTTPS_PORT` | Нет | Порт HTTPS на хосте (`443`) |
| `CADDY_LOG_LEVEL` | Нет | Уровень логирования Caddy (`INFO`) |
| `MAX_REQUEST_SIZE` | Нет | Ограничение размера запроса на web ingress |

## Политика секретов

- Не коммитьте credentials к базе данных.
- В production используйте secret store или CI/CD injection.
- Локальный `.env` используйте только для разработки, не храните его в истории production deploy.
- Website и Telegram используют общую схему PostgreSQL (`leads`, `lead_events`).
- Перед первым выпуском HTTPS-сертификата `CADDY_SITE_HOST` должен резолвиться в публичный IP VPS.
- Для `/leads` и `/api/leads` обязателен `LEADS_VIEW_TOKEN`.

## Локальный workflow конфигурации

1. Задайте локальные переменные в некоммичиваемом `.env`.
2. Перед запуском проверьте обязательные значения.
3. Для внешних интеграций начинайте с минимальных прав.

## Логирование и обработка ошибок

- Пишите структурированные логи в stdout.
- По возможности маскируйте персональные данные.
- Пользовательские ошибки должны быть понятными, а операционные — подробными в логах.
- Коррелируйте логи по `lead_id` и `session_id`, если они доступны.
- Для диагностики диалога включайте в debug-логи `step`, `validation_hint` и `offscript_count`.
- Рекомендуемый уровень логирования: `DEBUG` для локальной разработки и разбора диалогов, `INFO` для production.

## Правила качества данных

- Имя нормализуется перед сохранением (например, удаляются вводные фразы вроде `"я ..."`).
- На шаге контакта отклоняется текст запроса и повторно запрашивается телефон/email (web) или телефон/Telegram (bot).
- На шаге запроса отклоняется контактоподобный ввод и повторно запрашивается краткое описание задачи.
- Метки качества сохраняются в `lead_events.payload` (`qa_flags`, `offscript_count`).

## См. также

- [Быстрый старт](getting-started.md) - запуск и базовая настройка
- [API](api.md) - маршруты, зависящие от runtime config
- [Архитектура](architecture.md) - границы сервисов
