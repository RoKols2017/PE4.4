# Implementation Plan: PostgreSQL migration for lead storage

Branch: feature/postgres-lead-storage
Created: 2026-03-03

## Settings
- Testing: yes
- Logging: verbose
- Docs: yes

## Commit Plan
- **Commit 1** (after tasks 1-3): `chore(db): add postgres config and schema foundation`
- **Commit 2** (after tasks 4-7): `feat(storage): add postgres repositories and wire services`
- **Commit 3** (after tasks 8-10): `test/docs: migrate tests and remove sheets references`

## Tasks

### Phase 1: Baseline and data model
- [x] Task 1: Зафиксировать baseline ветку и обновить план миграции в `README.md` и `.ai-factory/DESCRIPTION.md` (без изменения функционала). Логирование: INFO о старте миграции и выбранном storage backend в `bot/bot.py` и `web_assistant/app.py`, DEBUG снимок конфигурации без секретов.
- [x] Task 2: Спроектировать целевую модель данных PostgreSQL и оформить SQL DDL + миграцию Alembic: создать `db/migrations/versions/<timestamp>_create_leads_tables.py` с таблицами `leads` и `lead_events` (если события нужны), ограничениями, индексами и `CHECK` для контактов. Логирование: INFO при запуске миграции, ERROR при rollback/failed upgrade.
- [x] Task 3: Добавить общий контракт хранилища и доменные DTO для persistence в `bot/domain.py`, `web_assistant/domain.py` или новый общий модуль `shared/storage_contract.py` с интерфейсом `LeadRepository`. Логирование: DEBUG на границах вызова `save_lead`, INFO при успешном сохранении, ERROR с `lead_id/session_id` при сбоях.

### Phase 2: Postgres integration
- [x] Task 4: Ввести PostgreSQL-конфигурацию и парсинг env в `bot/config.py`, `web_assistant/config.py`, `.env.example`, `bot/.env.example`, `web_assistant/.env.example` (например, `DATABASE_URL` или `POSTGRES_*` набор). Логирование: WARNING при fallback на defaults, ERROR при отсутствии обязательных DB-переменных.
- [x] Task 5: Реализовать репозиторий для бота `bot/postgres_repository.py` (или переиспользовать переименованный `bot/sheets.py`) с транзакционной вставкой lead + retry-политикой, затем подключить в `bot/bot.py`. Логирование: DEBUG payload sans secrets, INFO `lead_saved`, WARNING retry attempt, ERROR final failure.
- [x] Task 6: Реализовать репозиторий для web assistant `web_assistant/postgres_repository.py` и подключить DI в `web_assistant/app.py`, `web_assistant/routes.py` (замена `sheets_repo` на нейтральный `lead_repo`). Логирование: DEBUG вход/шаг, INFO `lead_saved` с `lead_id`, WARNING при валидационных отклонениях, ERROR при DB исключениях.
- [x] Task 7: Обновить контейнерную инфраструктуру под Postgres: `compose.yml`, `compose.override.yml`, `compose.production.yml` (сервис `postgres`, healthcheck, depends_on, volume), при необходимости `deploy/scripts/deploy.sh` для ожидания готовности БД. Логирование: INFO о статусе readiness checks, ERROR при таймауте готовности.

### Phase 3: Tests, cleanup, docs
- [x] Task 8: Переписать/добавить тесты хранилища и интеграции: `bot/tests/test_sheets.py` -> `bot/tests/test_postgres_repository.py`, `web_assistant/tests/test_sheets.py` -> `web_assistant/tests/test_postgres_repository.py`, обновить `web_assistant/tests/test_routes.py` под `lead_repo`. Логирование: DEBUG только в test mode, INFO итог тестового сценария записи.
- [x] Task 9: Удалить или архивировать Google Sheets-зависимости и код: `bot/sheets.py`, `web_assistant/sheets.py`, `web_assistant/sheets_schema.py`, а также удалить `google-api-python-client`/`google-auth` из `bot/requirements.txt` и `web_assistant/requirements.txt`. Логирование: INFO о выбранном backend=`postgres`, отсутствие вызовов legacy адаптеров.
- [x] Task 10: Актуализировать документацию (`AGENTS.md`, `docs/architecture.md`, `docs/configuration.md`, `docs/getting-started.md`, `docs/deployment.md`, `README.md`, `.ai-factory/ARCHITECTURE.md`) под новую модель хранения и процесс запуска через compose. Логирование: добавить раздел стандартов логов с `lead_id/session_id` и уровнями DEBUG/INFO/WARN/ERROR.
