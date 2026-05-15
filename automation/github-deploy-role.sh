#!/usr/bin/env bash
set -euo pipefail

required_vars=(
  TARGET_HOST
  SSH_PRIVATE_KEY
  SSH_PORT
  DEPLOY_ENVIRONMENT
  DEPLOY_ROLE
  IMAGE_TAG
  GHCR_OWNER
)

for var in "${required_vars[@]}"; do
  if [[ -z "${!var:-}" ]]; then
    echo "Missing required environment variable: $var"
    exit 2
  fi
done

mkdir -p ~/.ssh
printf '%s\n' "$SSH_PRIVATE_KEY" > ~/.ssh/deploy_key
chmod 600 ~/.ssh/deploy_key
ssh-keygen -y -f ~/.ssh/deploy_key >/dev/null

ssh_base=(
  ssh
  -o BatchMode=yes
  -o StrictHostKeyChecking=no
  -o ConnectTimeout=10
  -i ~/.ssh/deploy_key
  -p "$SSH_PORT"
  "ec2-user@$TARGET_HOST"
)

scp_base=(
  scp
  -o StrictHostKeyChecking=no
  -o ConnectTimeout=10
  -i ~/.ssh/deploy_key
  -P "$SSH_PORT"
)

"${ssh_base[@]}" 'echo auth-ok'

"${ssh_base[@]}" <<'REMOTE'
set -euo pipefail
mkdir -p /home/ec2-user/aws-hybrid/{release,automation}

if ! command -v docker >/dev/null 2>&1; then
  echo "Installing Docker..."
  if command -v dnf >/dev/null 2>&1; then
    sudo dnf -y install docker
  elif command -v yum >/dev/null 2>&1; then
    sudo yum -y install docker
  elif command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -y
    sudo apt-get install -y docker.io
  else
    echo "Unsupported package manager. Cannot install Docker."
    exit 1
  fi
fi

sudo systemctl enable --now docker
sudo groupadd -f docker || true
sudo usermod -aG docker ec2-user || true

if ! docker compose version >/dev/null 2>&1 && ! command -v docker-compose >/dev/null 2>&1; then
  echo "Installing Docker Compose..."
  if command -v dnf >/dev/null 2>&1; then
    sudo dnf -y install docker-compose-plugin || true
  elif command -v yum >/dev/null 2>&1; then
    sudo yum -y install docker-compose-plugin || sudo yum -y install docker-compose || true
  elif command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -y
    sudo apt-get install -y docker-compose-plugin || sudo apt-get install -y docker-compose || true
  fi

  if ! docker compose version >/dev/null 2>&1 && ! command -v docker-compose >/dev/null 2>&1; then
    sudo curl -fsSL "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
  fi
fi

docker --version
if docker compose version >/dev/null 2>&1; then
  docker compose version
else
  docker-compose --version
fi
REMOTE

"${scp_base[@]}" -r release/ "ec2-user@$TARGET_HOST:/home/ec2-user/aws-hybrid/"
"${scp_base[@]}" -r automation/ "ec2-user@$TARGET_HOST:/home/ec2-user/aws-hybrid/"

printf -v remote_ghcr_username '%q' "${GHCR_USERNAME:-}"
printf -v remote_ghcr_token '%q' "${GHCR_TOKEN:-}"
printf -v remote_ghcr_owner '%q' "$GHCR_OWNER"
printf -v remote_min_free_mb '%q' "${MIN_DOCKER_FREE_MB:-12288}"
printf -v remote_environment '%q' "$DEPLOY_ENVIRONMENT"
printf -v remote_image_tag '%q' "$IMAGE_TAG"
printf -v remote_role '%q' "$DEPLOY_ROLE"

"${ssh_base[@]}" \
  "cd /home/ec2-user/aws-hybrid && chmod +x automation/app-release-deploy.sh && GHCR_USERNAME=$remote_ghcr_username GHCR_TOKEN=$remote_ghcr_token GHCR_OWNER=$remote_ghcr_owner MIN_DOCKER_FREE_MB=$remote_min_free_mb ./automation/app-release-deploy.sh $remote_environment $remote_image_tag $remote_role"

rm -f ~/.ssh/deploy_key
