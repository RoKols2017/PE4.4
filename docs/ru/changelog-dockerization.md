[← Развертывание](deployment.md) · [Назад к README](../../README.md) · [Тестирование →](testing.md)

# История dockerизации

Английская версия: [Dockerization Changelog](../changelog-dockerization.md)

## Название изменения

Укрепление Docker-стека и разделение compose-профилей для dev/prod

## Зачем это делалось

- Разделить удобный локальный dev UX и production hardening без дублирования сервисных определений.
- Улучшить безопасность контейнеров и наблюдаемость перед rollout.
- Стандартизировать deployment entrypoints вокруг единого root `.env` контракта.

## Что изменилось

- Легаси `docker-compose.yml` заменен на:
  - `compose.yml` (базовый)
  - `compose.override.yml` (development)
  - `compose.production.yml` (production overlay)
- `bot/Dockerfile` и `web_assistant/Dockerfile` переведены на multi-stage сборку (`deps`, `builder`, `development`, `production`) с:
  - BuildKit cache mounts для `pip`
  - non-root runtime user в production
  - Dockerfile healthchecks
- В `web_assistant/routes.py` добавлен `GET /health`.
- Базовый edge proxy затем эволюционировал от `nginx` к `Caddy` с автоматическим HTTPS, health checks и security headers.
- Добавлены `.dockerignore` для root, bot и web assistant build contexts.
- Добавлен root `.env.example` с единым конфигурационным контрактом.
- В `deploy/scripts/` добавлены production helper scripts:
  - `deploy.sh`, `update.sh`, `logs.sh`, `health-check.sh`, `rollback.sh`, `backup.sh`

## Что было проверено

- `docker compose --env-file .env -f compose.yml -f compose.override.yml config` выполнялся успешно.
- `docker compose --env-file .env -f compose.yml -f compose.production.yml config` выполнялся успешно.
- `docker compose --env-file .env -f compose.yml -f compose.override.yml up --build -d` в той среде падал на `pip install` для `bot` из-за временного `JSONDecodeError` при чтении package index.
- Синтаксическая проверка скриптов проходила: `bash -n deploy/scripts/*.sh`.
- Проверка Python-синтаксиса для route-файла проходила: `python3 -m compileall web_assistant/routes.py`.

## Дальнейшие шаги

- Повторно запустить build/start, когда network/package index стабильны.
- При необходимости зафиксировать Python dependencies с hash'ами для лучшей воспроизводимости.

## См. также

- [Развертывание](deployment.md) - текущая схема runtime и rollout
- [Тестирование](testing.md) - валидация Docker-стека
- [Архитектура](architecture.md) - границы сервисов за edge proxy
