#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${FRAUDGUARD_DIR:-/opt/fraudguard}"
CORE_REPO="${FRAUDGUARD_CORE_REPO:-Gusma-crypto/backend-fraudguardai}"
CORE_REF="${FRAUDGUARD_CORE_REF:-main}"
AGENT_RAW="${FRAUDGUARD_AGENT_RAW:-https://raw.githubusercontent.com/Gusma-crypto/fraudguard-ai/main/deploy/vps}"
CORE_RAW="https://raw.githubusercontent.com/${CORE_REPO}/${CORE_REF}/deploy/vps"

if [ -z "${GITHUB_TOKEN:-}" ]; then
    echo "GITHUB_TOKEN is required to download private Core configuration." >&2
    exit 2
fi
mkdir -p "$APP_DIR"
chmod 700 "$APP_DIR"

curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 \
    -H "Authorization: Bearer $GITHUB_TOKEN" "$CORE_RAW/compose.yml" -o "$APP_DIR/compose.yml"
curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 \
    -H "Authorization: Bearer $GITHUB_TOKEN" "$CORE_RAW/Caddyfile" -o "$APP_DIR/Caddyfile"
curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 \
    "$AGENT_RAW/update-restart.sh" -o "$APP_DIR/update-restart.sh"
curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 \
    "$AGENT_RAW/deploy.sh" -o "$APP_DIR/deploy.sh"
if [ ! -f "$APP_DIR/.env.production" ]; then
    curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 \
        "$AGENT_RAW/.env.example" -o "$APP_DIR/.env.production"
    chmod 600 "$APP_DIR/.env.production"
fi

# Verify private Core config exists without storing the token or cloning the repository.
curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 \
    -H "Authorization: Bearer $GITHUB_TOKEN" "$CORE_RAW/.env.example" >/dev/null
chmod 700 "$APP_DIR/update-restart.sh"
chmod 700 "$APP_DIR/deploy.sh"
echo "Configuration installed at $APP_DIR. Edit .env.production, then run update-restart.sh."
