#!/usr/bin/env bash

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
COMPOSE_FILE="${PROJECT_ROOT}/compose.yml"
COMPOSE_OVERRIDE="${PROJECT_ROOT}/compose.override.yml"
COMPOSE_PROD="${PROJECT_ROOT}/compose.production.yml"
ENV_FILE="${PROJECT_ROOT}/.env"

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_error() { echo -e "${RED}[FAIL]${NC} $1"; }
error_exit() { log_error "$1"; exit 1; }

command -v docker >/dev/null 2>&1 || error_exit "Docker is not installed"
docker compose version >/dev/null 2>&1 || error_exit "Docker Compose v2 is not installed"

if [ -f "${ENV_FILE}" ]; then
  ENV_ARGS=(--env-file "${ENV_FILE}")
else
  ENV_ARGS=()
fi

log_info "Validating development compose stack"
docker compose "${ENV_ARGS[@]}" -f "${COMPOSE_FILE}" -f "${COMPOSE_OVERRIDE}" config -q
log_success "Development compose config is valid"

log_info "Validating production compose stack"
TELEGRAM_BOT_IMAGE="${TELEGRAM_BOT_IMAGE:-pe44-telegram-bot:validation}"
WEB_ASSISTANT_IMAGE="${WEB_ASSISTANT_IMAGE:-pe44-web-assistant:validation}"
export TELEGRAM_BOT_IMAGE WEB_ASSISTANT_IMAGE
docker compose "${ENV_ARGS[@]}" -f "${COMPOSE_FILE}" -f "${COMPOSE_PROD}" config -q
log_success "Production compose config is valid"

log_info "Validating Caddy configuration"
docker run --rm \
  -e CADDY_SITE_HOST="${CADDY_SITE_HOST:-localhost}" \
  -e CADDY_LOG_LEVEL="${CADDY_LOG_LEVEL:-INFO}" \
  -e MAX_REQUEST_SIZE="${MAX_REQUEST_SIZE:-1MB}" \
  -e CADDY_HTTPS_REDIRECT_SUFFIX="${CADDY_HTTPS_REDIRECT_SUFFIX:-}" \
  -v "${PROJECT_ROOT}/infra/caddy/Caddyfile:/etc/caddy/Caddyfile:ro" \
  caddy:2.10-alpine \
  caddy validate --config /etc/caddy/Caddyfile
log_success "Caddyfile is valid"
