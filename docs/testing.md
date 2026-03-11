[← Deployment](deployment.md) · [Back to README](../README.md)

# Testing

## Test Strategy

- Run tests in Docker by default.
- Keep bot and web assistant suites isolated in their own test services.
- Use fast unit and route tests for validation before manual smoke checks.

## Automated Test Commands

Build test images:

```bash
docker compose --profile test build telegram-bot-test web-assistant-test
```

Run both suites:

```bash
docker compose --profile test run --rm telegram-bot-test && \
docker compose --profile test run --rm web-assistant-test
```

Run a single suite:

```bash
docker compose --profile test run --rm telegram-bot-test
docker compose --profile test run --rm web-assistant-test
```

## Current Coverage

- `bot/tests/` covers domain validation and normalization behavior.
- `web_assistant/tests/` covers domain validation, route behavior, leads auth, and leads page rendering.
- Docker test services install `pytest` from each service's `requirements.txt`.

## Manual Smoke Checks

After `docker compose up --build -d`:

- Open `http://localhost:8080` and complete a web lead flow.
- Verify `/health` returns `200`.
- Verify `/leads` rejects requests without token.
- Verify `/api/leads?source=website_assistant` returns saved records with valid token.
- In Telegram, use `/start`, submit a lead, then retry with `/new`.

## Troubleshooting

- If tests fail after template changes, rebuild `web-assistant-test` so the updated templates are copied into the image.
- If environment changes affect startup, validate with `docker compose --profile test config`.
- For dialog debugging, set `LOG_LEVEL=DEBUG` in `.env` before rerunning the stack or tests.

## See Also

- [Getting Started](getting-started.md) - first-run setup and smoke checks
- [API](api.md) - endpoints exercised by route tests
- [Deployment](deployment.md) - compose topology and test services
