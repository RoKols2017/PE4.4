#!/usr/bin/env bash

set -euo pipefail

BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }

log_info "No stateful database container detected in this stack."
log_info "Backup script is intentionally a no-op (Google Sheets is the data store)."
log_success "Backup check completed"
