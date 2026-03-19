[← Deployment](deployment.md) · [Back to README](../README.md) · [Testing →](testing.md)

# Dockerization Changelog

## Title
Harden Docker stack and split compose profiles for dev/prod

## Why
- Separate local developer UX from production hardening without duplicating service definitions.
- Improve container security defaults and observability before rollout.
- Standardize deployment entrypoints around a single root `.env` contract.

## What Changed
- Replaced legacy `docker-compose.yml` with:
  - `compose.yml` (base)
  - `compose.override.yml` (development)
  - `compose.production.yml` (hardened production overlay)
- Upgraded `bot/Dockerfile` and `web_assistant/Dockerfile` to multi-stage builds (`deps`, `builder`, `development`, `production`) with:
  - BuildKit cache mounts for `pip`
  - non-root runtime user for production
  - Dockerfile healthchecks
- Added web health endpoint `GET /health` in `web_assistant/routes.py`.
- Updated the edge proxy baseline that later evolved from `nginx` to `Caddy` for automatic HTTPS, health checks, and security headers.
- Added `.dockerignore` files for root, bot, and web assistant build contexts.
- Added root `.env.example` for unified stack configuration.
- Added production operations scripts under `deploy/scripts/`:
  - `deploy.sh`, `update.sh`, `logs.sh`, `health-check.sh`, `rollback.sh`, `backup.sh`

## Validation Notes
- `docker compose --env-file .env -f compose.yml -f compose.override.yml config` succeeded.
- `docker compose --env-file .env -f compose.yml -f compose.production.yml config` succeeded.
- `docker compose --env-file .env -f compose.yml -f compose.override.yml up --build -d` failed in this environment during `pip install` for `bot` with transient `JSONDecodeError` while reading package index response.
- Script syntax checks passed (`bash -n deploy/scripts/*.sh`).
- Python syntax check passed for updated route file (`python3 -m compileall web_assistant/routes.py`).

## Follow-up
- Re-run stack build/start when package index/network conditions are stable.
- Optionally pin Python dependencies with hashes for stronger reproducibility.

## See Also

- [Deployment](deployment.md) - current runtime and rollout baseline
- [Testing](testing.md) - validation workflow for the Docker stack
- [Architecture](architecture.md) - service boundaries behind the edge proxy
