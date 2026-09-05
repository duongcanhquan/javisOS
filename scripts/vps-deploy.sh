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
if grep -q '^GEMINI_FORCE_FILE_STORAGE=' "$ENV_FILE" 2>/dev/null; then
  sed -i.bak 's/^GEMINI_FORCE_FILE_STORAGE=.*/GEMINI_FORCE_FILE_STORAGE=true/' "$ENV_FILE" && rm -f "$ENV_FILE.bak"
else
  echo 'GEMINI_FORCE_FILE_STORAGE=true' >> "$ENV_FILE"
fi

echo "==> git pull"
git fetch --all --prune
# VPS có thể còn diff local từ lần deploy trước → reset về origin/main trước khi pull.
git reset --hard origin/main 2>/dev/null || true
git pull --ff-only origin main

# Pixelle đầy đủ (API :8000 + WebUI :8501) trừ khi .env tắt rõ.
ENABLE_PIXELLE=true
if [ -f "$ENV_FILE" ] && grep -q '^JAVIS_ENABLE_PIXELLE=false' "$ENV_FILE" 2>/dev/null; then
  ENABLE_PIXELLE=false
fi

COMPOSE_FILES=(
  -f docker-compose.yml
  -f docker-compose.build.yml
  -f docker-compose.source.yml
  --profile tunnel
)

if [ "$ENABLE_PIXELLE" = "true" ]; then
  echo "==> setup Pixelle"
  chmod +x scripts/setup-pixelle-vps.sh
  bash scripts/setup-pixelle-vps.sh
  # shellcheck disable=SC1091
  if [ -f "$ENV_FILE" ]; then
    # Xuất PIXELLE_DIR cho compose nếu setup vừa ghi.
    set -a
    # Chỉ nạp các dòng PIXELLE_ / RUNNINGHUB_ / JAVIS_ENABLE_PIXELLE an toàn.
    eval "$(grep -E '^(PIXELLE_|RUNNINGHUB_|JAVIS_ENABLE_PIXELLE=)' "$ENV_FILE" | sed 's/\r$//' || true)"
    set +a
  fi
  export PIXELLE_DIR="${PIXELLE_DIR:-$ROOT/vendor/Pixelle-Video}"
  COMPOSE_FILES+=(-f docker-compose.pixelle.yml --profile pixelle)
  echo "==> Pixelle profile ON (dir=$PIXELLE_DIR)"
else
  echo "==> Pixelle tắt (JAVIS_ENABLE_PIXELLE=false)"
fi

echo "==> build & up (with Cloudflare tunnel$([ "$ENABLE_PIXELLE" = true ] && echo ' + pixelle'))"
docker compose \
  "${COMPOSE_FILES[@]}" \
  up -d --build

echo "==> health"
ok_health=0
for i in 1 2 3 4 5 6 7 8 9 10; do
  if curl -fsS -m 5 http://127.0.0.1:7777/health; then
    echo
    ok_health=1
    break
  fi
  echo "waiting health... ($i)"
  sleep 3
done
if [ "$ok_health" != "1" ]; then
  echo "HEALTH_FAIL (container có thể vẫn đang khởi động)"
fi

if [ "$ENABLE_PIXELLE" = "true" ]; then
  echo "==> pixelle health"
  ok_px=0
  for i in $(seq 1 20); do
    if curl -fsS -m 5 http://127.0.0.1:8000/health; then
      echo
      ok_px=1
      break
    fi
    echo "waiting pixelle... ($i)"
    sleep 4
  done
  if [ "$ok_px" != "1" ]; then
    echo "PIXELLE_HEALTH_FAIL (xem: docker compose logs pixelle-api)"
  else
    echo "Pixelle API OK · WebUI http://127.0.0.1:${PIXELLE_WEB_PORT:-8501}"
  fi
fi
echo
echo "==> tunnel URL (if any)"
docker compose logs tunnel 2>&1 | grep -i trycloudflare | tail -n 3 || true

if [ -f "$ROOT/scripts/seed-morning-brief-vps.sh" ]; then
  echo "==> seed morning brief reminder"
  chmod +x "$ROOT/scripts/seed-morning-brief-vps.sh"
  bash "$ROOT/scripts/seed-morning-brief-vps.sh" || echo "WARN: seed-morning-brief skipped"
fi

if [ -f "$ROOT/scripts/force-morning-brief-today-vps.sh" ]; then
  echo "==> force morning brief today (send soon)"
  chmod +x "$ROOT/scripts/force-morning-brief-today-vps.sh"
  bash "$ROOT/scripts/force-morning-brief-today-vps.sh" || echo "WARN: force-morning-brief-today skipped"
fi

echo "==> done"
