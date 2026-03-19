[← Конфигурация](configuration.md) · [Назад к README](../../README.md) · [История dockerизации →](changelog-dockerization.md)

# Развертывание

Английская версия: [Deployment](../deployment.md)

## Топология runtime

Ожидаемый набор контейнеров:

- `postgres` (основное реляционное хранилище)
- `caddy` (публичный edge и завершение HTTPS)
- `web-assistant` (внутреннее Flask-приложение по HTTP)
- `telegram-bot` (outbound worker)

Compose-файлы:

- `compose.yml` - базовая конфигурация
- `compose.override.yml` - локальные dev overrides
- `compose.production.yml` - production overlay с hardening

Тестовые сервисы в `compose.yml`:

- `telegram-bot-test` -> запускает `python -m pytest tests -q` в dev-образе бота
- `web-assistant-test` -> запускает `python -m pytest tests -q` в dev-образе веб-сервиса

Текущая внутренняя маршрутизация:

- `caddy` -> `web-assistant:5000`
- `web-assistant` запускает Flask через `python app.py` в Docker
- `web-assistant` отдает `/health` для container health checks

Состояние Caddy:

- volume `caddy-data` хранит ACME-сертификаты и account state
- volume `caddy-config` хранит runtime config data

## Сетевая база

- Используйте одну Docker bridge-сеть для внутренних коммуникаций.
- Наружу должны быть опубликованы только порты Caddy.
- Прикладные контейнеры должны оставаться приватными.

Текущие порты edge:

- Dev по умолчанию: `8080 -> caddy:80`, при необходимости `8443 -> caddy:443`
- Production по умолчанию: `${CADDY_HTTP_PORT:-80} -> caddy:80`, `${CADDY_HTTPS_PORT:-443} -> caddy:443`

## База безопасности

- На edge должен выполняться redirect с HTTP на HTTPS.
- Должны быть включены HSTS и стандартные security headers.
- Для website endpoint'ов должно действовать ограничение размера запроса.
- Секреты не должны попадать в образы.
- В production app-контейнеры запускаются от non-root пользователя.
- В production используются `read_only`, `tmpfs`, `no-new-privileges` и `cap_drop: [ALL]`, при этом для Caddy разрешается `NET_BIND_SERVICE`.

## Чеклист перед production deploy

| Проверка | Статус |
|----------|--------|
| DNS `A`/`AAAA` запись указывает на VPS | Обязательно |
| `CADDY_SITE_HOST` настроен | Обязательно |
| Порты `80` и `443` открыты на VPS/firewall | Обязательно |
| Caddy выпустил TLS-сертификаты | Обязательно |
| В env доступны токены бота | Обязательно |
| Для web-assistant доступен OpenAI API key | Обязательно |
| PostgreSQL credentials передаются безопасно | Обязательно |
| Логи контейнеров доступны для просмотра | Обязательно |

## Операционные замечания

- `telegram-bot` может работать в режиме polling без публичного webhook.
- Для bot и web сервисов рекомендуется сохранять restart policy.
- Оба сервиса записывают лиды в таблицу `leads` и события в `lead_events`.
- Health checks настроены для `postgres`, `telegram-bot`, `web-assistant` и `caddy`.
- Production helper scripts лежат в `deploy/scripts/`.
- `deploy/scripts/health-check.sh` проверяет здоровье контейнеров, HTTP `/health`, HTTPS `/health` и redirect с HTTP на HTTPS.

## Команды

- Development: `docker compose --env-file .env -f compose.yml -f compose.override.yml up --build -d`
- Production: `docker compose --env-file .env -f compose.yml -f compose.production.yml up -d`
- Проверка production config: `docker compose --env-file .env -f compose.yml -f compose.production.yml config`
- Проверка compose + Caddy config: `./deploy/scripts/validate-config.sh`
- Запуск тестов: `docker compose --profile test run --rm telegram-bot-test && docker compose --profile test run --rm web-assistant-test`

## См. также

- [Быстрый старт](getting-started.md) - подготовка перед выкладкой
- [Конфигурация](configuration.md) - env-переменные и секреты
- [Тестирование](testing.md) - smoke checks и тестовый workflow
