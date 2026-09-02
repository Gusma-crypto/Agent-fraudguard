#!/usr/bin/env bash
set -Eeuo pipefail
APP_DIR="${FRAUDGUARD_DIR:-/opt/fraudguard}"
exec "$APP_DIR/deploy.sh"
