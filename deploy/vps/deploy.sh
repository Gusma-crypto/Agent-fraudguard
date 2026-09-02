#!/usr/bin/env bash
set -Eeuo pipefail
APP_DIR="${FRAUDGUARD_DIR:-/opt/fraudguard}"
CORE_REPO="${FRAUDGUARD_CORE_REPO:-Gusma-crypto/backend-fraudguardai}"
AGENT_REPO="${FRAUDGUARD_AGENT_REPO:-Gusma-crypto/fraudguard-ai}"
REF="${FRAUDGUARD_REF:-main}"
SOURCE_DIR="$APP_DIR/source"
if [ -z "${GITHUB_TOKEN:-}" ]; then
    echo "GITHUB_TOKEN is required to download the private Core source." >&2
    exit 2
fi
if [ ! -f "$APP_DIR/.env.production" ]; then
    echo "Missing $APP_DIR/.env.production. Run install.sh first." >&2
    exit 2
fi
cleanup() { rm -rf "$SOURCE_DIR"; }
trap cleanup EXIT
rm -rf "$SOURCE_DIR"
mkdir -p "$SOURCE_DIR"
git -c "http.extraheader=Authorization: Bearer $GITHUB_TOKEN" clone \
    --depth 1 --branch "$REF" "https://github.com/$CORE_REPO.git" "$SOURCE_DIR/core"
git clone --depth 1 --branch "$REF" \
    "https://github.com/$AGENT_REPO.git" "$SOURCE_DIR/agent"
cd "$APP_DIR"
docker compose --env-file .env.production -f compose.yml config --quiet
docker compose --env-file .env.production -f compose.yml up -d --build --remove-orphans
docker compose --env-file .env.production -f compose.yml restart
for attempt in $(seq 1 30); do
    if curl --fail --silent --show-error "https://${FRAUDGUARD_DOMAIN}/ready" >/dev/null; then
        docker compose --env-file .env.production -f compose.yml ps
        echo "FraudGuard Core, Agent, and Frontend are ready."
        exit 0
    fi
    sleep 5
done
echo "FraudGuard deployment did not become ready." >&2
docker compose --env-file .env.production -f compose.yml ps >&2 || true
exit 1
