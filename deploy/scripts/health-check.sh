#!/usr/bin/env bash

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
COMPOSE_FILE="${PROJECT_ROOT}/compose.yml"
COMPOSE_PROD="${PROJECT_ROOT}/compose.production.yml"
ENV_FILE="${PROJECT_ROOT}/.env"

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[FAIL]${NC} $1"; }

dc() { docker compose -f "${COMPOSE_FILE}" -f "${COMPOSE_PROD}" "$@"; }

if [ -f "${ENV_FILE}" ]; then
  set -a
  source "${ENV_FILE}"
  set +a
fi

CADDY_SITE_HOST="${CADDY_SITE_HOST:-localhost}"
CADDY_HTTP_PORT="${CADDY_HTTP_PORT:-80}"
CADDY_HTTPS_PORT="${CADDY_HTTPS_PORT:-443}"
FAILED=0

log_info "Container health status"
while IFS= read -r line; do
  svc="$(echo "${line}" | awk '{print $1}')"
  state="$(echo "${line}" | awk '{print $2}')"
  health="$(echo "${line}" | awk '{print $3}')"

  if [ "${state}" != "running" ]; then
    log_error "${svc}: ${state}"
    FAILED=1
    continue
  fi

  if [ -z "${health}" ] || [ "${health}" = "healthy" ] || [ "${health}" = "(healthy)" ]; then
    log_success "${svc}: running ${health}"
  else
    log_error "${svc}: ${health}"
    FAILED=1
  fi
done < <(dc ps --format '{{.Service}} {{.State}} {{.Health}}')

log_info "Edge HTTP health check"
if curl -fsS -H "Host: ${CADDY_SITE_HOST}" "http://127.0.0.1:${CADDY_HTTP_PORT}/health" >/dev/null; then
  log_success "caddy HTTP /health reachable"
else
  log_warning "caddy HTTP /health not reachable on :${CADDY_HTTP_PORT}"
  FAILED=1
fi

log_info "Edge HTTPS health check"
TLS_ARGS=(--resolve "${CADDY_SITE_HOST}:${CADDY_HTTPS_PORT}:127.0.0.1")
if [ "${CADDY_SITE_HOST}" = "localhost" ]; then
  log_warning "Using insecure local TLS check for localhost certificate trust"
  TLS_ARGS+=(-k)
fi

if curl -fsS "${TLS_ARGS[@]}" "https://${CADDY_SITE_HOST}:${CADDY_HTTPS_PORT}/health" >/dev/null; then
  log_success "caddy HTTPS /health reachable"
else
  log_warning "caddy HTTPS /health not reachable for ${CADDY_SITE_HOST}:${CADDY_HTTPS_PORT}"
  FAILED=1
fi

log_info "HTTP to HTTPS redirect check"
redirect_target="$(curl -sSI -H "Host: ${CADDY_SITE_HOST}" "http://127.0.0.1:${CADDY_HTTP_PORT}/" | awk -F': ' 'tolower($1)=="location" {print $2}' | tr -d '\r')"
expected_prefix="https://${CADDY_SITE_HOST}"
if [[ "${redirect_target}" == ${expected_prefix}* ]]; then
  log_success "caddy redirects HTTP traffic to HTTPS"
else
  log_warning "HTTP redirect target is unexpected: ${redirect_target:-<empty>}"
  FAILED=1
fi

if [ ${FAILED} -eq 0 ]; then
  log_success "Health check passed"
  exit 0
fi

log_error "Health check failed"
exit 1
