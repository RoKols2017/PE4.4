[← Configuration](configuration.md) · [Back to README](../README.md)

# Deployment

## Runtime Topology

Expected container set:

- `postgres` (primary relational storage)
- `nginx` (public edge, HTTPS termination)
- `web-assistant` (Flask internal HTTP app)
- `telegram-bot` (outbound integration worker)

Compose files:

- `compose.yml` - base config (shared)
- `compose.override.yml` - development overrides (auto-merged for local)
- `compose.production.yml` - production hardening overlay

Current internal routing:

- `nginx` -> `web-assistant:5000`
- `web-assistant` runs Flask via `python app.py` in Docker
- `web-assistant` exposes `/health` for container health checks

Optional component:

- `certbot` or external certificate manager

## Network Baseline

- Use one Docker bridge network for internal service communication.
- Expose only nginx ports to the public network.
- Keep application containers private by default.

Current edge port mapping:

- Dev default: `8080 -> nginx:8080`
- Production default: `${NGINX_HTTP_PORT:-80} -> nginx:8080`

## Security Baseline

- Force HTTP to HTTPS redirects at nginx edge.
- Enable HSTS and standard security headers.
- Enforce request-size limits for website endpoints.
- Keep secrets in env/secret providers, not in images.
- Run application containers as non-root users in production overlay.
- Use `read_only`, `tmpfs`, `no-new-privileges`, and `cap_drop: [ALL]` in production.

## Deployment Checklist

| Check | Status to confirm |
|-------|-------------------|
| TLS certificates configured | Required |
| `NGINX_SERVER_NAME` configured | Required |
| Bot token available in runtime env | Required |
| OpenAI API key available for web assistant | Required |
| PostgreSQL credentials injected securely | Required |
| Logs visible from all containers | Required |

## Operational Notes

- `telegram-bot` can run in polling mode to avoid inbound webhook exposure.
- Keep restart policy enabled for bot and web services.
- Both services write leads into PostgreSQL table `leads` and append events into `lead_events`.
- Health checks are configured for postgres, bot, web-assistant, and nginx.
- Production helper scripts are available in `deploy/scripts/`.

## Commands

- Development: `docker compose --env-file .env -f compose.yml -f compose.override.yml up --build -d`
- Production: `docker compose --env-file .env -f compose.yml -f compose.production.yml up -d`
- Validate production config: `docker compose --env-file .env -f compose.yml -f compose.production.yml config`

## See Also

- [Getting Started](getting-started.md) - setup path before rollout
- [Architecture](architecture.md) - component responsibilities
- [Configuration](configuration.md) - env vars and secret policy
