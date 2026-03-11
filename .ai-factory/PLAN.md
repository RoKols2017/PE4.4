# Implementation Plan: Улучшение распознавания данных лида и диалогового UX (bot + web)

Branch: none (fast mode)
Created: 2026-03-11

## Settings
- Testing: yes
- Logging: verbose
- Docs: yes

## Commit Plan
- **Commit 1** (after tasks 1-3): `feat(domain): harden lead normalization and validation across channels`
- **Commit 2** (after tasks 4-6): `feat(ai): improve prompts and invalid-input recovery flow`
- **Commit 3** (after tasks 7-9): `test/docs: cover edge cases and document data quality rules`

## Tasks

### Phase 1: Data quality contract (оба канала)
- [x] Task 1: Усилить нормализацию имени и контактов в `bot/domain.py` и `web_assistant/domain.py`: добавить очистку вводов вроде `"я Вовочка"`/`"меня зовут ..."`, унификацию регистра/пробелов и более строгие правила для мусорных значений, не ломая валидные короткие имена (например `Гадя`). Логирование: DEBUG исходное/нормализованное значение (без PII-переполнения), INFO причины успешной нормализации, WARNING код причины отклонения, ERROR для неожиданных исключений.
- [x] Task 2: Ввести расширенный набор `validation_hint` кодов в `bot/domain.py` и `web_assistant/domain.py` (например, `name_contains_intro_phrase`, `contact_looks_like_text`, `request_looks_like_contact`) и подключить их в текущие обработчики шагов `bot/bot.py` и `web_assistant/routes.py`. Логирование: DEBUG шаг и новый код валидации, INFO переходы шага после исправления, WARNING рост `offscript_count`, ERROR при неконсистентном состоянии сессии.
- [x] Task 3: Добавить слой защиты от ошибочного маппинга полей перед сохранением (name/contact/request) в `bot/bot.py` и `web_assistant/routes.py`: если значение больше похоже на другой тип поля, не сохранять и вернуть на корректный шаг. Логирование: DEBUG результат эвристики типа поля, WARNING срабатывание guard и причина, INFO успешное прохождение guard, ERROR сбой проверки перед записью.

### Phase 2: LLM-assisted UX improvements without losing deterministic flow
- [x] Task 4: Улучшить системные промпты и step hints в `bot/ai_logic.py` и `web_assistant/ai_logic.py`: добавить доменный контекст, явные инструкции по распознаванию пользовательских формулировок, запрет на подмену полей и на выдумывание данных, плюс короткие примеры корректного переспроса. Логирование: DEBUG отправляемый контекст (без токенов и PII), INFO успешный ответ модели по шагу, WARNING активация fallback, ERROR детали неуспешного вызова API.
- [x] Task 5: Добавить служебный признак качества диалога (например, `assistant_recovery_reason` или `qa_flags`) в runtime-состояние `bot/session.py` и `web_assistant/session.py`, чтобы фиксировать частые причины непонимания без изменения пользовательского UX. Логирование: DEBUG обновление флагов на каждом шаге, INFO финальные агрегированные флаги при успешной заявке, WARNING аномально высокий `offscript_count`, ERROR ошибка сериализации/чтения state.
- [x] Task 6: Улучшить UX-подсказки для повторного ввода в `bot/bot.py` и `web_assistant/routes.py`: при невалидных ответах давать короткий формат примера только для текущего шага, а для Telegram дополнить `/start` и `/new` более явными инструкциями по повторному сбору. Логирование: DEBUG какой шаблон подсказки выдан, INFO количество циклов до успешного шага, WARNING частые повторы, ERROR сбой отправки/формирования сообщения.

### Phase 3: Persistence visibility, tests, docs
- [x] Task 7: Расширить сохранение событий качества данных в `bot/postgres_repository.py` и `web_assistant/postgres_repository.py` (через существующий поток `lead_events`), чтобы видеть почему поле было отклонено/перезапрошено. Логирование: DEBUG payload события без секретов, INFO факт записи event с `lead_id/session_id`, WARNING частые однотипные event, ERROR ошибка записи event.
- [x] Task 8: Добавить edge-case тесты в `bot/tests/test_domain.py`, `bot/tests/test_dialog.py`, `web_assistant/tests/test_domain.py`, `web_assistant/tests/test_routes.py` на кейсы из прод-логов: `"я Вовочка"`, контакт в поле запроса, текст вместо контакта, нестабильные оффтоп-ответы, корректные короткие имена. Логирование: в тестах проверять коды валидации, переходы шагов и отсутствие регрессии happy-path.
- [x] Task 9: Обновить документацию `README.md`, `docs/architecture.md`, `docs/configuration.md`, `docs/getting-started.md`, `AGENTS.md` по новым правилам нормализации/валидации, назначению `validation_hint`, и диагностике качества лидов через логи/lead events. Логирование: задокументировать рекомендуемые уровни (`DEBUG` dev, `INFO` prod) и обязательные корреляционные поля (`session_id`, `lead_id`, `step`, `validation_hint`).
