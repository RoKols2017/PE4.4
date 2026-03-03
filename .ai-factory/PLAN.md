# Implementation Plan: Просмотр лидов из PostgreSQL на сайте

Branch: feature/postgres-lead-storage
Created: 2026-03-03

## Settings
- Testing: yes
- Logging: verbose
- Docs: yes

## Commit Plan
- **Commit 1** (after tasks 1-3): `feat(web): add leads read model and repository query`
- **Commit 2** (after tasks 4-6): `feat(web): add leads page and protected api endpoint`
- **Commit 3** (after tasks 7-8): `test/docs: cover leads view flow and update docs`

## Tasks

### Phase 1: Contract и доступ к данным
- [x] Task 1: Уточнить контракт чтения лидов в `web_assistant/domain.py`: добавить DTO для списка лидов (поля карточки/таблицы) и метод репозитория `list_leads(limit, offset, source)` для страницы просмотра. Логирование: DEBUG входные параметры пагинации/фильтров, WARNING при невалидных параметрах, ERROR при нарушении контракта.
- [x] Task 2: Реализовать чтение лидов из PostgreSQL в `web_assistant/postgres_repository.py` (select из `leads` с сортировкой `created_at_utc DESC`, limit/offset, опциональный фильтр `source`). Логирование: DEBUG SQL-граница вызова (без секретов), INFO размер выдачи, ERROR с `session_id`/context при исключениях.
- [x] Task 3: Добавить защиту доступа к просмотру лидов через env-токен в `web_assistant/config.py` и `.env.example` (например `LEADS_VIEW_TOKEN`), чтобы не светить персональные данные публично. Логирование: WARNING при попытке доступа без/с неверным токеном, INFO при успешной авторизации просмотра.

### Phase 2: Backend маршруты и UI
- [x] Task 4: Добавить в `web_assistant/routes.py` страницу `GET /leads` (render template) и API `GET /api/leads` с валидацией query-параметров `limit`, `offset`, `source`, проверкой токена и возвратом JSON-структуры для фронта. Логирование: DEBUG входящие параметры и `session_id`, INFO успешная выдача, WARNING некорректные фильтры, ERROR ошибки БД/сериализации.
- [x] Task 5: Создать шаблон `web_assistant/templates/leads.html` для просмотра лидов (таблица/карточки, фильтр по source, пагинация, empty-state, error-state) в стиле текущего сайта. Логирование: через клиентский `/api/client-log` события `leads_view_opened`, `leads_filter_changed`, `leads_page_changed`.
- [x] Task 6: Добавить клиентский скрипт `web_assistant/static/js/leads.js` и стили в `web_assistant/static/css/styles.css` для загрузки `/api/leads`, отрисовки списка и управления фильтрами/пагинацией. Логирование: DEBUG client-log для запросов/ответов (без PII в payload), WARNING для неуспешных ответов API.

### Phase 3: Тесты и документация
- [x] Task 7: Расширить `web_assistant/tests/test_routes.py` тестами на `GET /api/leads` (успех, unauthorized, invalid params, пустая выдача) и добавить фейковую реализацию `list_leads` в `FakeLeadRepo`. Логирование: в тестовом контуре фиксировать ключевые события через `caplog`/assert по кодам ответов.
- [x] Task 8: Обновить документацию `README.md`, `docs/configuration.md`, `docs/getting-started.md`, `docs/architecture.md`, `AGENTS.md` с описанием маршрута `/leads`, env `LEADS_VIEW_TOKEN`, и процесса проверки данных в БД. Логирование: задокументировать требования к логам доступа к просмотру лидов (INFO/WARN/ERROR).
