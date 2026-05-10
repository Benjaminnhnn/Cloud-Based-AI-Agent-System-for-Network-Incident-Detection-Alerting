#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${ENV_FILE:-${PROJECT_ROOT}/.env.deploy}"

if [[ -f "${ENV_FILE}" ]]; then
  set -a
  # shellcheck disable=SC1090
  . "${ENV_FILE}"
  set +a
fi

IMAGE_NAME="${AI_AGENT_IMAGE_NAME:-ghcr.io/${GHCR_OWNER:-your-org}/aws-hybrid-ai-agent}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
IMAGE="${AI_AGENT_IMAGE:-${IMAGE_NAME}:${IMAGE_TAG}}"
FIRST_IMAGE_PART="${IMAGE%%/*}"

if [[ -n "${AI_AGENT_REGISTRY:-}" ]]; then
  REGISTRY="${AI_AGENT_REGISTRY}"
elif [[ "${FIRST_IMAGE_PART}" == *.* || "${FIRST_IMAGE_PART}" == *:* || "${FIRST_IMAGE_PART}" == "localhost" ]]; then
  REGISTRY="${FIRST_IMAGE_PART}"
else
  REGISTRY="docker.io"
fi

if [[ "${IMAGE}" == ghcr.io/your-org/* ]]; then
  echo "ERROR: set GHCR_OWNER or AI_AGENT_IMAGE before pushing."
  echo "Example:"
  echo "  GHCR_OWNER=my-github-user IMAGE_TAG=v1 ./automation/build-push-ai-agent-image.sh"
  echo "  AI_AGENT_IMAGE=ghcr.io/my-github-user/aws-hybrid-ai-agent:v1 ./automation/build-push-ai-agent-image.sh"
  exit 1
fi

echo "Building AI Agent image: ${IMAGE}"
docker build -t "${IMAGE}" "${PROJECT_ROOT}/agent_src"

if [[ -n "${AI_AGENT_REGISTRY_USERNAME:-}" && -n "${AI_AGENT_REGISTRY_PASSWORD:-}" ]]; then
  echo "Logging in to registry: ${REGISTRY}"
  printf '%s' "${AI_AGENT_REGISTRY_PASSWORD}" | docker login "${REGISTRY}" -u "${AI_AGENT_REGISTRY_USERNAME}" --password-stdin
fi

echo "Pushing AI Agent image: ${IMAGE}"
docker push "${IMAGE}"

echo "Done."
echo "Deploy with:"
echo "  ansible-playbook -i ansible/inventory.ini ansible/playbooks/deploy-ai-agent.yml"
