[← Архитектура](architecture.md) · [Назад к README](../../README.md) · [Конфигурация →](configuration.md)

# API

Английская версия: [API](../api.md)

## Область действия

Публичные HTTP endpoint'ы предоставляет только `web_assistant`. У Telegram-бота нет публичного HTTP API.

## Базовые URL

- Локально через Caddy: `http://localhost:8080`
- Локальный HTTPS через Caddy: `https://localhost:8443`
- Прямой Flask-контейнер в dev override: `http://localhost:5000`

## Аутентификация

| Поверхность | Доступ |
|-------------|--------|
| `/api/chat/*` | без авторизации |
| `/health` | без авторизации |
| `/leads` | query-параметр `token` |
| `/api/leads` | заголовок `X-Leads-View-Token` или query-параметр `token` |

Если `LEADS_VIEW_TOKEN` не задан, endpoints для просмотра лидов возвращают `503` и `{"error": "leads_view_not_configured"}`.

## Endpoint'ы

### `GET /`

Возвращает landing page со встроенным виджетом ассистента.

### `GET /health`

Health endpoint для Docker health checks.

Ответ:

```json
{"status": "ok"}
```

### `POST /api/chat/start`

Запускает новую сессию website assistant.

Заголовки:

- Опциональный `X-Session-Id`: повторное использование существующего client session id

Поля ответа:

- `session_id`
- `step`
- `assistant_message`
- `typing`

### `POST /api/chat/message`

Обрабатывает сообщение пользователя на текущем шаге.

Заголовки:

- `X-Session-Id`: client session correlation id

Тело:

```json
{"message": "Иван"}
```

Поведение:

- Пустое сообщение возвращает `400` с `{"error": "message_required"}`
- Валидный ввод переводит на следующий шаг
- Невалидный ввод оставляет на текущем шаге и возвращает подсказку для повтора
- Финальное `да` сохраняет лид и возвращает подтверждение с `lead_id`
- Финальное `нет` сбрасывает flow обратно на `name`

### `GET /leads`

Возвращает HTML-страницу для просмотра заявок с токен-защитой.

Пример:

```text
/leads?token=<LEADS_VIEW_TOKEN>
```

### `GET /api/leads`

Возвращает записи лидов из PostgreSQL с пагинацией.

Поддерживаемые query-параметры:

| Параметр | По умолчанию | Примечание |
|----------|--------------|------------|
| `limit` | `20` | `1..100` |
| `offset` | `0` | `>= 0` |
| `source` | none | `telegram_bot` или `website_assistant` |

Успешный ответ:

```json
{
  "items": [],
  "pagination": {"limit": 20, "offset": 0, "total": 0},
  "source": "all"
}
```

Коды ошибок:

- `401` -> `{"error": "unauthorized"}`
- `400` -> `{"error": "invalid_pagination"}` или `{"error": "invalid_pagination_range"}` или `{"error": "invalid_source"}`
- `500` -> `{"error": "leads_read_failed"}`

### `POST /api/client-log`

Принимает клиентскую телеметрию виджета и пишет ее в серверные логи.

Формат тела:

```json
{"event": "widget_opened", "details": {"source": "landing"}}
```

Ответ:

```json
{"ok": true}
```

## См. также

- [Архитектура](architecture.md) - границы сервисов и владение flow
- [Конфигурация](configuration.md) - auth и env-требования
- [Тестирование](testing.md) - проверка endpoint'ов в Docker
