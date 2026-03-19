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
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
error_exit() { log_error "$1"; exit 1; }

dc() { docker compose -f "${COMPOSE_FILE}" -f "${COMPOSE_PROD}" "$@"; }

command -v docker >/dev/null 2>&1 || error_exit "Docker is not installed"
docker compose version >/dev/null 2>&1 || error_exit "Docker Compose v2 is not installed"
docker info >/dev/null 2>&1 || error_exit "Docker daemon is not running"

[ -f "${COMPOSE_FILE}" ] || error_exit "compose.yml not found"
[ -f "${COMPOSE_PROD}" ] || error_exit "compose.production.yml not found"
[ -f "${ENV_FILE}" ] || error_exit ".env not found. Copy .env.example and fill values first."

set -a
source "${ENV_FILE}"
set +a

VERSION="${VERSION:-$(date +%Y%m%d-%H%M%S)}"
export VERSION

log_info "Validating compose configuration"
dc config -q || error_exit "Invalid compose configuration"

log_info "Pulling images"
dc pull || log_warning "Some images could not be pulled; continuing"

log_info "Starting services"
dc up -d --remove-orphans || error_exit "Failed to start services"

MAX_WAIT=120
WAIT=0
SERVICES=(postgres telegram-bot web-assistant caddy)

log_info "Waiting for service health"
while [ ${WAIT} -lt ${MAX_WAIT} ]; do
  ALL_HEALTHY=true
  for svc in "${SERVICES[@]}"; do
    log_info "Checking ${svc} readiness"
    health="$(dc ps --format '{{.Service}} {{.Health}}' | awk -v name="$svc" '$1==name {print $2}')"
    if [ -n "${health}" ] && [ "${health}" != "healthy" ]; then
      ALL_HEALTHY=false
    fi
  done

  if [ "${ALL_HEALTHY}" = true ]; then
    log_success "All services are healthy"
    break
  fi

  sleep 2
  WAIT=$((WAIT + 2))
done

[ ${WAIT} -ge ${MAX_WAIT} ] && error_exit "Services did not become healthy in time"

log_success "Deployment completed"
dc ps
