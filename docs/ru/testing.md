[← История dockerизации](changelog-dockerization.md) · [Назад к README](../../README.md)

# Тестирование

Английская версия: [Testing](../testing.md)

## Стратегия тестирования

- По умолчанию тесты запускаются в Docker.
- Наборы тестов для бота и веб-ассистента изолированы в отдельных test-сервисах.
- Для быстрой проверки используются unit- и route-тесты, после них выполняются ручные smoke checks.

## Автоматические команды

Перед запуском стека проверьте compose и edge-конфиг:

```bash
./deploy/scripts/validate-config.sh
```

Собрать test-образы:

```bash
docker compose --profile test build telegram-bot-test web-assistant-test
```

Запустить оба набора тестов:

```bash
docker compose --profile test run --rm telegram-bot-test && \
docker compose --profile test run --rm web-assistant-test
```

Запустить один набор тестов:

```bash
docker compose --profile test run --rm telegram-bot-test
docker compose --profile test run --rm web-assistant-test
```

## Текущее покрытие

- `bot/tests/` покрывает валидацию и нормализацию доменной модели.
- `web_assistant/tests/` покрывает доменную валидацию, поведение маршрутов, авторизацию на просмотр лидов и рендеринг страницы заявок.
- Тесты runtime policy покрывают разбор JSON-схемы, невалидные intent'ы и deterministic fallback.
- Docker test-сервисы устанавливают `pytest` из `requirements.txt` каждого сервиса.

## Ручные smoke checks

После `docker compose up --build -d`:

- Откройте `http://localhost:8080` и пройдите web lead flow.
- При необходимости проверьте локальный TLS: `https://localhost:8443` (браузер может попросить доверить local CA Caddy).
- Убедитесь, что `/health` возвращает `200`.
- Проверьте, что `/leads` отклоняет запросы без токена.
- Проверьте, что `/api/leads?source=website_assistant` возвращает сохраненные записи при валидном токене.
- В Telegram используйте `/start`, отправьте лид и затем повторите с `/new`.
- В обоих каналах проверьте confirm-stage edits (`исправь имя`, `исправь контакт`, `исправь задачу`).
- Проверьте, что пустой или битый ответ модели не пропускает валидацию и приводит к deterministic retry prompt.

## Устранение неполадок

- Если тесты падают после изменения шаблонов, пересоберите `web-assistant-test`, чтобы новые templates попали в образ.
- Если изменения env влияют на старт, заново запустите `./deploy/scripts/validate-config.sh`.
- Для отладки диалогов выставьте `LOG_LEVEL=DEBUG` в `.env` перед повторным запуском стека или тестов.

## См. также

- [Быстрый старт](getting-started.md) - первый запуск и smoke checks
- [API](api.md) - endpoints, которые покрываются route-тестами
- [Развертывание](deployment.md) - topology compose и test-сервисы
