[← Configuration](configuration.md) · [Back to README](../README.md) · [Dockerization Changelog →](changelog-dockerization.md)

# Deployment

## Runtime Topology

Expected container set:

- `postgres` (primary relational storage)
- `caddy` (public edge, HTTPS termination)
- `web-assistant` (Flask internal HTTP app)
- `telegram-bot` (outbound integration worker)

Compose files:

- `compose.yml` - base config (shared)
- `compose.override.yml` - development overrides (auto-merged for local)
- `compose.production.yml` - production hardening overlay

Test profile services in `compose.yml`:

- `telegram-bot-test` -> runs `python -m pytest tests -q` in the bot development image
- `web-assistant-test` -> runs `python -m pytest tests -q` in the web development image

Current internal routing:

- `caddy` -> `web-assistant:5000`
- `web-assistant` runs Flask via `python app.py` in Docker
- `web-assistant` exposes `/health` for container health checks

Caddy state:

- `caddy-data` volume stores ACME certificates and account state
- `caddy-config` volume stores runtime config data

## Network Baseline

- Use one Docker bridge network for internal service communication.
- Expose only Caddy ports to the public network.
- Keep application containers private by default.

Current edge port mapping:

- Dev default: `8080 -> caddy:80`, optional `8443 -> caddy:443`
- Production default: `${CADDY_HTTP_PORT:-80} -> caddy:80`, `${CADDY_HTTPS_PORT:-443} -> caddy:443`

## Security Baseline

- Force HTTP to HTTPS redirects at Caddy edge.
- Enable HSTS and standard security headers.
- Enforce request-size limits for website endpoints.
- Keep secrets in env/secret providers, not in images.
- Run application containers as non-root users in production overlay.
- Use `read_only`, `tmpfs`, `no-new-privileges`, and `cap_drop: [ALL]` in production, while allowing `NET_BIND_SERVICE` for Caddy.

## Deployment Checklist

| Check | Status to confirm |
|-------|-------------------|
| DNS `A`/`AAAA` record points to VPS | Required |
| `CADDY_SITE_HOST` configured | Required |
| Ports `80` and `443` open on VPS/firewall | Required |
| TLS certificates issued by Caddy | Required |
| Bot token available in runtime env | Required |
| OpenAI API key available for web assistant | Required |
| PostgreSQL credentials injected securely | Required |
| Logs visible from all containers | Required |

## Operational Notes

- `telegram-bot` can run in polling mode to avoid inbound webhook exposure.
- Keep restart policy enabled for bot and web services.
- Both services write leads into PostgreSQL table `leads` and append events into `lead_events`.
- Health checks are configured for postgres, bot, web-assistant, and caddy.
- Production helper scripts are available in `deploy/scripts/`.
- `deploy/scripts/health-check.sh` validates container health, HTTP `/health`, HTTPS `/health`, and the HTTP->HTTPS redirect path.

## Commands

- Development: `docker compose --env-file .env -f compose.yml -f compose.override.yml up --build -d`
- Production: `docker compose --env-file .env -f compose.yml -f compose.production.yml up -d`
- Validate production config: `docker compose --env-file .env -f compose.yml -f compose.production.yml config`
- Validate compose + Caddy config: `./deploy/scripts/validate-config.sh`
- Run tests: `docker compose --profile test run --rm telegram-bot-test && docker compose --profile test run --rm web-assistant-test`

## See Also

- [Getting Started](getting-started.md) - setup path before rollout
- [Configuration](configuration.md) - env vars and secret policy
- [Testing](testing.md) - Docker test workflow and smoke checks
