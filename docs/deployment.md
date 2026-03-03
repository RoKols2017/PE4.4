[← Configuration](configuration.md) · [Back to README](../README.md)

# Deployment

## Runtime Topology

Expected container set:

- `nginx` (public edge, HTTPS termination)
- `web-assistant` (Flask internal HTTP app)
- `telegram-bot` (outbound integration worker)

Optional component:

- `certbot` or external certificate manager

## Network Baseline

- Use one Docker bridge network for internal service communication.
- Expose only nginx ports to the public network.
- Keep application containers private by default.

## Security Baseline

- Force HTTP to HTTPS redirects at nginx edge.
- Enable HSTS and standard security headers.
- Enforce request-size limits for website endpoints.
- Keep secrets in env/secret providers, not in images.

## Deployment Checklist

| Check | Status to confirm |
|-------|-------------------|
| TLS certificates configured | Required |
| `NGINX_SERVER_NAME` configured | Required |
| Bot token available in runtime env | Required |
| Google Sheets credentials injected securely | Required |
| Logs visible from all containers | Required |

## Operational Notes

- `telegram-bot` can run in polling mode to avoid inbound webhook exposure.
- Keep restart policy enabled for bot and web services.
- Both services write leads into a shared Google Sheets table `Leads`.
- Add health checks for Flask and bot containers as next hardening step.

## See Also

- [Getting Started](getting-started.md) - setup path before rollout
- [Architecture](architecture.md) - component responsibilities
- [Configuration](configuration.md) - env vars and secret policy
