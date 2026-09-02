#!/bin/sh
set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
COMPOSE_FILE="$PROJECT_ROOT/Docker/compose.yml"
ENV_FILE=${ENV_FILE:-"$PROJECT_ROOT/.env"}
ACTION=${1:-deploy}
DEPLOY_STARTED=0
case "$ENV_FILE" in
    /*) ;;
    *) ENV_FILE="$PROJECT_ROOT/$ENV_FILE" ;;
esac
export AGENT_ENV_FILE="$ENV_FILE"

log() { printf '%s\n' "[fraudguard-agent] $*"; }
fail() { printf '%s\n' "[fraudguard-agent] ERROR: $*" >&2; exit 1; }
compose() { docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"; }

usage() {
    cat <<'EOF'
Usage: ./deploy.sh [deploy|update|restart|status|logs|stop|check]

  deploy   Build and start the current source (default).
  update   Pull origin with fast-forward only, then build and deploy.
  restart  Restart the Agent and wait for Core-backed readiness.
  status   Show container status.
  logs     Follow Agent logs.
  stop     Stop the Agent container.
  check    Validate Docker, environment, and Compose configuration only.
EOF
}

ensure_network() {
    if ! docker network inspect fraudguard-network >/dev/null 2>&1; then
        log "Creating shared Docker network fraudguard-network"
        docker network create fraudguard-network >/dev/null
    fi
}

update_source() {
    git -C "$PROJECT_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1 \
        || fail "update requires a Git working tree."
    if [ -n "$(git -C "$PROJECT_ROOT" status --porcelain --untracked-files=no)" ]; then
        fail "Tracked files have local changes. Commit or stash them before update."
    fi
    git -C "$PROJECT_ROOT" remote get-url origin >/dev/null 2>&1 \
        || fail "Git remote origin is not configured."
    log "Updating source with git pull --ff-only"
    git -C "$PROJECT_ROOT" pull --ff-only
}

wait_ready() {
    attempt=1
    max_attempts=${READINESS_ATTEMPTS:-30}
    log "Waiting for Agent and Core readiness"
    while [ "$attempt" -le "$max_attempts" ]; do
        if compose exec -T agent python -c \
            'import json,urllib.request; data=json.load(urllib.request.urlopen("http://127.0.0.1:3000/ready", timeout=3)); raise SystemExit(0 if data.get("status") == "ready" else 1)' \
            >/dev/null 2>&1; then
            compose ps
            log "Agent is ready at http://127.0.0.1:${AGENT_PORT:-3000}"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done
    return 1
}

show_failure_logs() {
    exit_code=$?
    trap - EXIT INT TERM
    if [ "$exit_code" -ne 0 ] && [ "$DEPLOY_STARTED" -eq 1 ]; then
        printf '%s\n' "[fraudguard-agent] Deployment failed. Recent logs:" >&2
        compose logs --no-color --tail=100 agent >&2 || true
    fi
    exit "$exit_code"
}

trap show_failure_logs EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

case "$ACTION" in
    -h|--help|help) usage; trap - EXIT INT TERM; exit 0 ;;
    deploy|update|restart|status|logs|stop|check) ;;
    *) usage >&2; fail "Unknown action: $ACTION" ;;
esac

command -v docker >/dev/null 2>&1 || fail "Docker is not installed or not in PATH."
docker compose version >/dev/null 2>&1 || fail "Docker Compose v2 is not available."
[ -f "$COMPOSE_FILE" ] || fail "Compose file not found: $COMPOSE_FILE"
[ -f "$ENV_FILE" ] || fail "Environment file not found: $ENV_FILE. Run: cp .env.example .env"

if [ "$ACTION" = "update" ]; then update_source; fi

log "Validating Compose configuration"
compose config --quiet

case "$ACTION" in
    check)
        log "Configuration is valid."
        ;;
    status)
        compose ps
        ;;
    logs)
        compose logs -f --tail=200 agent
        ;;
    stop)
        compose down --remove-orphans
        log "Agent container stopped."
        ;;
    restart)
        ensure_network
        DEPLOY_STARTED=1
        compose restart agent
        wait_ready || fail "Agent did not become ready after restart. Check Core connectivity."
        ;;
    deploy|update)
        ensure_network
        DEPLOY_STARTED=1
        if [ "${NO_CACHE:-0}" = "1" ]; then
            compose build --pull --no-cache agent
        else
            compose build --pull agent
        fi
        log "Starting Agent"
        compose up -d --remove-orphans agent
        wait_ready || fail "Agent did not become ready. Deploy Core first and verify the Core API key."
        ;;
esac

trap - EXIT INT TERM
