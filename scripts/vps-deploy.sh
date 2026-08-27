#!/usr/bin/env bash
# Deploy Javis on Ubuntu from the git checkout (build from source).
# Keeps Docker volumes (admin, brains, Claude auth) via COMPOSE_PROJECT_NAME=javis.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-javis}"

echo "==> git pull"
git fetch --all --prune
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
