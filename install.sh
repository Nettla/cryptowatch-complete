#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${CRYPTOWATCH_INSTALL_DIR:-$HOME/cryptowatch-complete-managed}"
INSTALL_PORT="${CRYPTOWATCH_INSTALL_PORT:-8096}"
COMPOSE_PROJECT="${CRYPTOWATCH_PROJECT:-cryptowatch-complete-managed}"

echo "=== CryptoWatch Complete Installer ==="

if [[ ! "$INSTALL_PORT" =~ ^[1-9][0-9]{0,4}$ ]] ||
   (( 10#$INSTALL_PORT > 65535 )); then
    echo "ERROR: Invalid port."
    exit 1
fi

case "$INSTALL_DIR" in
    "$HOME"/cryptowatch-complete-*) ;;
    *)
        echo "ERROR: Installation directory must be under HOME and start with cryptowatch-complete-."
        exit 1
        ;;
esac

INSTALL_NAME="${INSTALL_DIR#"$HOME"/}"

if [[ ! "$INSTALL_NAME" =~ ^cryptowatch-complete-[a-zA-Z0-9_-]+$ ]]; then
    echo "ERROR: Invalid installation directory."
    exit 1
fi

if [[ ! "$COMPOSE_PROJECT" =~ ^cryptowatch-complete-[a-z0-9_-]+$ ]]; then
    echo "ERROR: Invalid Compose project name."
    exit 1
fi

if [[ -e "$INSTALL_DIR" || -L "$INSTALL_DIR" ]]; then
    echo "ERROR: Installation directory already exists."
    exit 1
fi

for tool in docker ansible-playbook ss curl python3; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "ERROR: Missing tool: $tool"
        exit 1
    fi
done

if ! docker compose version >/dev/null 2>&1; then
    echo "ERROR: Docker Compose is unavailable."
    exit 1
fi

if [[ ! -f "$PROJECT_ROOT/ansible/deploy.yml" ]]; then
    echo "ERROR: Ansible playbook is missing."
    exit 1
fi

if [[ ! -f "$PROJECT_ROOT/.env.example" ]]; then
    echo "ERROR: .env.example is missing."
    exit 1
fi

DOCKER_BECOME=false
DOCKER_CMD=(docker)

if docker info >/dev/null 2>&1; then
    echo "Docker access: direct"
else
    echo "Docker requires sudo authentication."
    sudo -v
    if ! sudo -n docker info >/dev/null 2>&1; then
        echo "ERROR: Docker access unavailable."
        exit 1
    fi
    DOCKER_BECOME=true
    DOCKER_CMD=(sudo -n docker)
    echo "Docker access: sudo"
fi

if [[ -n "$(ss -H -ltn "( sport = :$INSTALL_PORT )")" ]]; then
    echo "ERROR: Port $INSTALL_PORT is already occupied."
    exit 1
fi

EXISTING="$("${DOCKER_CMD[@]}" ps -a \
    --filter "label=com.docker.compose.project=$COMPOSE_PROJECT" \
    --format '{{.ID}}')"

if [[ -n "$EXISTING" ]]; then
    echo "ERROR: Compose project already has containers."
    exit 1
fi

if "${DOCKER_CMD[@]}" volume inspect \
    "${COMPOSE_PROJECT}_postgres_data" >/dev/null 2>&1; then
    echo "ERROR: Database volume already exists."
    exit 1
fi

echo "Directory: $INSTALL_DIR"
echo "Port: $INSTALL_PORT"
echo "Compose project: $COMPOSE_PROJECT"

ansible-playbook \
    -i 'localhost,' \
    -c local \
    "$PROJECT_ROOT/ansible/deploy.yml" \
    -e "cryptowatch_directory=$INSTALL_DIR" \
    -e "cryptowatch_port=$INSTALL_PORT" \
    -e "cryptowatch_project=$COMPOSE_PROJECT" \
    -e "cryptowatch_docker_become=$DOCKER_BECOME"

echo "=== Health check ==="

HEALTH_OK=0

for attempt in $(seq 1 30); do
    if curl -fsS --max-time 3 \
        "http://127.0.0.1:$INSTALL_PORT/health" \
        >/dev/null 2>&1; then
        HEALTH_OK=1
        break
    fi
    sleep 2
done

if [[ "$HEALTH_OK" -ne 1 ]]; then
    echo "ERROR: API health check failed."
    exit 1
fi

echo "INSTALLATION SUCCESSFUL"
echo "Dashboard: http://127.0.0.1:$INSTALL_PORT"
