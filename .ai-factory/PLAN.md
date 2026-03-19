# Implementation Plan: Замена nginx на Caddy и подготовка HTTPS-публикации на VPS

Branch: none (fast mode)
Created: 2026-03-19

## Settings
- Testing: yes
- Logging: verbose
- Docs: yes

## Commit Plan
- **Commit 1** (after tasks 1-3): `feat(deploy): replace nginx edge with caddy for automatic https`
- **Commit 2** (after tasks 4-6): `chore(deploy): align scripts env and health checks for vps rollout`
- **Commit 3** (after tasks 7-8): `docs(test): document caddy-based https deployment`

## Tasks

### Phase 1: Edge proxy replacement and production topology
- [x] Task 1: Заменить сервис `nginx` на `caddy` в `compose.yml`, `compose.production.yml` и `compose.override.yml`: сохранить внутреннюю схему `caddy -> web-assistant:5000`, не публиковать `web-assistant` наружу в production, открыть `80/443` только для edge-сервиса, добавить постоянные volumes для ACME state/config. Логирование: оставить stdout-логи контейнеров, INFO для статуса edge-сервиса, WARNING при деградации healthcheck, ERROR при невалидной compose-конфигурации.
- [x] Task 2: Создать конфиг `Caddyfile` (например, в `infra/caddy/Caddyfile`) с reverse proxy на `web-assistant:5000`, авто-выпуском HTTPS по домену, HTTP->HTTPS редиректом, security headers и отдельным `/health` endpoint либо корректным проксированием health-маршрута. Логирование: INFO для запросов edge-уровня, WARNING для TLS/ACME проблем, ERROR для конфигурационных ошибок Caddy.
- [x] Task 3: Удалить или архивировать привязки к `infra/nginx/default.conf`, проверить что новые volume mounts и пути не конфликтуют с production hardening, и при необходимости скорректировать `read_only`, `tmpfs`, user/cap settings под Caddy в `compose.production.yml`. Логирование: INFO о примененной security-модели edge-контейнера, WARNING если приходится ослабить hardening ради ACME, ERROR при несовместимости прав/путей.

### Phase 2: Runtime contract, health checks, and VPS readiness
- [x] Task 4: Обновить `.env.example` и конфигурационный контракт deployment: заменить `NGINX_HTTP_PORT`/`NGINX_SERVER_NAME` на Caddy-ориентированные переменные (например, публичный домен, HTTP/HTTPS порты, email для ACME если нужен), описать безопасные значения по умолчанию для VPS и сохранить совместимость остальных сервисов. Логирование: задокументировать INFO-уровень для production и WARNING для отсутствующих обязательных edge env vars.
- [x] Task 5: Переписать `deploy/scripts/deploy.sh`, `deploy/scripts/health-check.sh`, `deploy/scripts/update.sh` и `deploy/scripts/rollback.sh`, чтобы они ожидали сервис `caddy`, проверяли readiness без привязки к nginx и валидировали HTTP/HTTPS edge доступ на VPS. Логирование: INFO на этапах rollout, WARNING при частичной деградации или недоступности HTTP redirect, ERROR если контейнер edge не стал healthy или TLS endpoint не отвечает.
- [x] Task 6: Проверить и при необходимости скорректировать healthchecks в compose: edge healthcheck должен проверять Caddy-маршрут, `web-assistant` остается внутренним `/health`, а production smoke path должен подтверждать готовность сайта для домена на VPS. Логирование: INFO при успешной проверке маршрута и reverse proxy, WARNING при нестабильных ответах backend, ERROR при timeout/502/loop redirect.

### Phase 3: Verification, docs, and operator guidance
- [x] Task 7: Добавить или обновить deployment-oriented tests/validation steps: минимум `docker compose ... config`, smoke-проверки edge-контейнера, и при наличии уместных тестов — покрытие путей, которые зависят от `/health` и reverse proxy assumptions. Файлы: CI/tests docs и при необходимости shell validation helpers. Логирование: INFO о выполняемых smoke-checks, WARNING о неполном локальном покрытии HTTPS из-за отсутствия реального домена, ERROR при несоответствии compose/health сценариев.
- [x] Task 8: Обновить `README.md`, `docs/deployment.md`, `docs/configuration.md`, `docs/architecture.md`, `docs/getting-started.md`, `docs/testing.md`, `docs/api.md` и `AGENTS.md`: заменить `nginx` на `caddy`, описать публикацию на VPS с доменом и автоматическим HTTPS, DNS/портовые требования (`80`, `443`), хранение сертификатов, smoke-check команды и ограничения локальной проверки TLS без публичного домена. Логирование: явно зафиксировать рекомендуемые production-логи edge/app/postgres и команды диагностики для проблем с ACME/TLS.
