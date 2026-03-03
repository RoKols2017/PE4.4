#!/usr/bin/env bash

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
COMPOSE_FILE="${PROJECT_ROOT}/compose.yml"
COMPOSE_PROD="${PROJECT_ROOT}/compose.production.yml"

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
error_exit() { log_error "$1"; exit 1; }

dc() { docker compose -f "${COMPOSE_FILE}" -f "${COMPOSE_PROD}" "$@"; }

TARGET_VERSION="${1:-}"
[ -n "${TARGET_VERSION}" ] || error_exit "Usage: ./deploy/scripts/rollback.sh <version>"

export VERSION="${TARGET_VERSION}"

log_info "Rolling back to VERSION=${VERSION}"
dc pull || true
dc up -d --force-recreate --no-deps telegram-bot web-assistant nginx || error_exit "Rollback failed"

"${SCRIPT_DIR}/health-check.sh" || error_exit "Health check failed after rollback"
log_success "Rollback completed"
