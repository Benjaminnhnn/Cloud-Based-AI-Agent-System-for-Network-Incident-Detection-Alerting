#!/usr/bin/env bash
set -euo pipefail

ENVIRONMENT="${1:-}"
NEW_TAG="${2:-}"

if [[ -z "$ENVIRONMENT" || -z "$NEW_TAG" ]]; then
  echo "Usage: $0 <staging|production> <image-tag>"
  exit 2
fi

if [[ "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "production" ]]; then
  echo "Invalid environment: $ENVIRONMENT"
  exit 2
fi

case "$ENVIRONMENT" in
  staging)
    COMPOSE_FILE="release/docker-compose.staging.yml"
    ENV_FILE="release/.env.staging"
    AI_HEALTH_URL="http://127.0.0.1:18000/health"
    API_HEALTH_URL="http://127.0.0.1:18080/api/health"
    ;;
  production)
    COMPOSE_FILE="release/docker-compose.production.yml"
    ENV_FILE="release/.env.production"
    AI_HEALTH_URL="http://127.0.0.1:8000/health"
    API_HEALTH_URL="http://127.0.0.1:8080/api/health"
    ;;
esac

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "Compose file not found: $COMPOSE_FILE"
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Environment file not found: $ENV_FILE"
  echo "Creating from template..."

  if [[ ! -f "release/.env.example" ]]; then
    echo "Template file not found: release/.env.example"
    exit 1
  fi

  cp release/.env.example "$ENV_FILE"
  echo "Created $ENV_FILE from template. Please configure it with actual values."
  echo "Critical variables needed:"
  echo "  - GHCR_OWNER (GitHub org/username)"
  echo "  - GEMINI_API_KEY (Google Gemini API key)"
  echo "  - TELEGRAM_TOKEN (optional)"
  echo "  - TELEGRAM_CHAT_ID (optional)"
fi

if [[ -n "${GHCR_USERNAME:-}" && -n "${GHCR_TOKEN:-}" ]]; then
  echo "$GHCR_TOKEN" | docker login ghcr.io -u "$GHCR_USERNAME" --password-stdin
else
  echo "GHCR credentials not set in shell; assuming host already logged in"
fi

mkdir -p release/.state
STATE_FILE="release/.state/${ENVIRONMENT}.tag"
PREVIOUS_TAG=""

if [[ -f "$STATE_FILE" ]]; then
  PREVIOUS_TAG="$(cat "$STATE_FILE")"
fi

export GHCR_OWNER="${GHCR_OWNER:-your-org}"
export IMAGE_TAG="$NEW_TAG"

load_env_file() {
  # Export key=value pairs from env file for docker-compose fallback.
  local owner_backup="${GHCR_OWNER:-}"
  local tag_backup="${IMAGE_TAG:-}"

  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  set +a

  # Keep runtime deployment values authoritative over template defaults.
  if [[ -n "$owner_backup" ]]; then
    export GHCR_OWNER="$owner_backup"
  fi
  if [[ -n "$tag_backup" ]]; then
    export IMAGE_TAG="$tag_backup"
  fi
}

compose_cmd() {
  if docker compose version >/dev/null 2>&1; then
    docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
    return
  fi

  if command -v docker-compose >/dev/null 2>&1; then
    load_env_file
    docker-compose -f "$COMPOSE_FILE" "$@"
    return
  fi

  echo "No compose runtime found. Install Docker Compose plugin or docker-compose binary."
  exit 1
}

available_disk_mb() {
  df -Pm / | awk 'NR == 2 {print $4}'
}

ensure_docker_disk_space() {
  local min_free_mb="${MIN_DOCKER_FREE_MB:-6144}"
  local free_mb

  free_mb="$(available_disk_mb)"
  if [[ "$free_mb" -ge "$min_free_mb" ]]; then
    echo "Disk preflight OK: ${free_mb}MB free on /"
    return
  fi

  echo "Disk preflight warning: only ${free_mb}MB free on /; need at least ${min_free_mb}MB"
  echo "Pruning unused Docker images before pulling new release..."
  docker image prune -af

  free_mb="$(available_disk_mb)"
  if [[ "$free_mb" -lt "$min_free_mb" ]]; then
    echo "Still only ${free_mb}MB free after Docker image prune."
    echo "Increase the EC2 root volume or remove unused Docker data before deploying."
    exit 1
  fi

  echo "Disk preflight recovered: ${free_mb}MB free on /"
}

health_check() {
  local retries=18
  local wait_seconds=10

  for attempt in $(seq 1 "$retries"); do
    ai_ok=0
    api_ok=0

    if curl -fsS "$AI_HEALTH_URL" >/dev/null; then
      ai_ok=1
    fi

    if curl -fsS "$API_HEALTH_URL" >/dev/null; then
      api_ok=1
    fi

    if [[ "$ai_ok" -eq 1 && "$api_ok" -eq 1 ]]; then
      return 0
    fi

    echo "Health check attempt $attempt/$retries failed; retrying in ${wait_seconds}s"
    sleep "$wait_seconds"
  done

  return 1
}

echo "Deploying $ENVIRONMENT with tag $NEW_TAG"
ensure_docker_disk_space
compose_cmd pull
compose_cmd up -d --remove-orphans

if health_check; then
  echo "$NEW_TAG" > "$STATE_FILE"
  docker image prune -f >/dev/null || true
  echo "Deploy successful. Current tag: $NEW_TAG"
  exit 0
fi

echo "Health check failed for tag: $NEW_TAG"

if [[ -n "$PREVIOUS_TAG" && "$PREVIOUS_TAG" != "$NEW_TAG" ]]; then
  echo "Rolling back to previous tag: $PREVIOUS_TAG"
  export IMAGE_TAG="$PREVIOUS_TAG"
  compose_cmd pull
  compose_cmd up -d --remove-orphans

  if health_check; then
    echo "Rollback successful to tag: $PREVIOUS_TAG"
  else
    echo "Rollback failed. Manual intervention required."
  fi
else
  echo "No previous tag available for rollback."
fi

exit 1
