#!/usr/bin/env bash
# Deploy Javis on Ubuntu from the git checkout (build from source).
# Keeps Docker volumes (admin, brains, Claude auth) via COMPOSE_PROJECT_NAME=javis.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-javis}"

# Plugin user: bật trừ khi .env ghi rõ false (env chỉ đọc lúc container khởi động).
ENV_FILE="$ROOT/.env"
touch "$ENV_FILE"
if grep -q '^JAVIS_ENABLE_USER_PLUGINS=' "$ENV_FILE" 2>/dev/null; then
  sed -i.bak 's/^JAVIS_ENABLE_USER_PLUGINS=.*/JAVIS_ENABLE_USER_PLUGINS=true/' "$ENV_FILE" && rm -f "$ENV_FILE.bak"
else
  echo 'JAVIS_ENABLE_USER_PLUGINS=true' >> "$ENV_FILE"
fi

echo "==> git pull"
git fetch --all --prune
# VPS có thể còn diff local từ lần deploy trước → reset về origin/main trước khi pull.
git reset --hard origin/main 2>/dev/null || true
git pull --ff-only origin main

echo "==> build & up (with Cloudflare tunnel)"
docker compose \
  -f docker-compose.yml \
  -f docker-compose.build.yml \
  -f docker-compose.source.yml \
  --profile tunnel \
  up -d --build

echo "==> health"
sleep 5
curl -fsS http://127.0.0.1:7777/health || true
echo
echo "==> tunnel URL (if any)"
docker compose logs tunnel 2>&1 | grep -i trycloudflare | tail -n 3 || true
echo "==> done"
