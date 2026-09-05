#!/usr/bin/env bash
# Deploy Javis on Ubuntu: PULL image GHCR (không --build trên VPS).
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

# Gỡ Ollama host TRƯỚC pull (giải phóng đĩa/RAM, tránh treo `ollama rm` sau deploy).
if [ -f "$ROOT/scripts/uninstall-ollama-vps.sh" ]; then
  echo "==> Gỡ Ollama host (trước pull)"
  chmod +x "$ROOT/scripts/uninstall-ollama-vps.sh"
  JAVIS_OLLAMA_HOST_ONLY=1 timeout 120 bash "$ROOT/scripts/uninstall-ollama-vps.sh" \
    || echo "WARN: uninstall-ollama host skipped"
fi

echo "==> git fetch"
git fetch --all --prune
# WANT_SHA = commit đã publish image; đừng reset lên origin/main mới hơn image.
if [ -n "${WANT_SHA:-}" ]; then
  git fetch origin "$WANT_SHA" 2>/dev/null || true
  git reset --hard "$WANT_SHA"
else
  git reset --hard origin/main 2>/dev/null || true
  git pull --ff-only origin main || true
fi

# Pixelle: ÉP tắt TRƯỚC compose up. .env cũ còn =true vẫn không được kéo 2 container nặng.
if grep -q '^JAVIS_ENABLE_PIXELLE=' "$ENV_FILE" 2>/dev/null; then
  sed -i.bak 's/^JAVIS_ENABLE_PIXELLE=.*/JAVIS_ENABLE_PIXELLE=false/' "$ENV_FILE" && rm -f "$ENV_FILE.bak"
else
  printf '\nJAVIS_ENABLE_PIXELLE=false\n' >> "$ENV_FILE"
fi
echo "==> Pixelle tắt (ép JAVIS_ENABLE_PIXELLE=false trước up)"

# Image GHCR của CHÍNH repo này (fork), không kéo nhầm upstream blogminhquy.
if [ -z "${JAVIS_IMAGE:-}" ]; then
  origin=$(git remote get-url origin 2>/dev/null || true)
  slug=${origin%.git}
  slug=${slug#https://github.com/}
  slug=${slug#http://github.com/}
  slug=${slug#git@github.com:}
  slug=${slug#ssh://git@github.com/}
  slug=$(printf '%s' "$slug" | tr '[:upper:]' '[:lower:]')
  if [[ "$slug" == */* ]]; then
    JAVIS_IMAGE="ghcr.io/${slug}:latest"
  else
    JAVIS_IMAGE="ghcr.io/duongcanhquan/javisos:latest"
  fi
fi
export JAVIS_IMAGE
echo "==> image $JAVIS_IMAGE"

COMPOSE_FILES=(
  -f docker-compose.yml
  --profile tunnel
)

if [ -n "${GHCR_TOKEN:-}" ]; then
  echo "==> docker login ghcr.io"
  echo "$GHCR_TOKEN" | docker login ghcr.io -u "${GHCR_USER:-github}" --password-stdin \
    || echo "WARN: docker login GHCR thất bại (image public thì pull vẫn được)"
fi

echo "==> dọn container cũ / orphan (tránh Conflict tên sau recreate thất bại)"
docker compose "${COMPOSE_FILES[@]}" down --remove-orphans 2>/dev/null || true
for _name in "${JAVIS_NAME:-javis}" javis-pixelle-api javis-pixelle-web "${JAVIS_NAME:-javis}-tunnel"; do
  docker rm -f "$_name" 2>/dev/null || true
done

echo "==> pull $JAVIS_IMAGE"
ok_pull=0
for i in $(seq 1 18); do
  if docker compose "${COMPOSE_FILES[@]}" pull; then
    ok_pull=1
    break
  fi
  echo "pull chưa sẵn sàng ($i/18) - chờ 10s"
  sleep 10
done
if [ "$ok_pull" != 1 ]; then
  echo "ERROR: không pull được $JAVIS_IMAGE"
  echo "Không build tại chỗ (tránh image sai / Conflict). Chờ workflow Docker publish xanh rồi deploy lại."
  exit 1
fi

echo "==> up (pull image, không --build, Cloudflare tunnel)"
docker compose \
  "${COMPOSE_FILES[@]}" \
  up -d --no-build --remove-orphans

echo "==> health"
ok_health=0
for i in $(seq 1 20); do
  if curl -fsS -m 5 http://127.0.0.1:7777/health; then
    echo
    ok_health=1
    break
  fi
  echo "waiting health... ($i)"
  sleep 4
done
if [ "$ok_health" != "1" ]; then
  echo "HEALTH_FAIL"
  docker compose "${COMPOSE_FILES[@]}" logs javis --tail 80 || true
  exit 1
fi

echo
echo "==> tunnel URL (if any)"
docker compose logs tunnel 2>&1 | grep -i trycloudflare | tail -n 3 || true

if [ -f "$ROOT/scripts/seed-morning-brief-vps.sh" ]; then
  echo "==> seed morning brief reminder"
  chmod +x "$ROOT/scripts/seed-morning-brief-vps.sh"
  bash "$ROOT/scripts/seed-morning-brief-vps.sh" || echo "WARN: seed-morning-brief skipped"
fi

if [ -f "$ROOT/scripts/seed-chat-brief-vps.sh" ]; then
  echo "==> seed chat brief reminder"
  chmod +x "$ROOT/scripts/seed-chat-brief-vps.sh"
  bash "$ROOT/scripts/seed-chat-brief-vps.sh" || echo "WARN: seed-chat-brief skipped"
fi

# Ép tổng kết sáng: chỉ khi FORCE_MORNING_BRIEF_TODAY=1 (không mặc định mỗi deploy).
if [ "${FORCE_MORNING_BRIEF_TODAY:-0}" = "1" ] && [ -f "$ROOT/scripts/force-morning-brief-today-vps.sh" ]; then
  echo "==> force morning brief today (send soon)"
  chmod +x "$ROOT/scripts/force-morning-brief-today-vps.sh"
  bash "$ROOT/scripts/force-morning-brief-today-vps.sh" || echo "WARN: force-morning-brief-today skipped"
fi

if [ -f "$ROOT/scripts/optimize-vps.sh" ]; then
  echo "==> optimize VPS (routing cloud + health)"
  chmod +x "$ROOT/scripts/optimize-vps.sh"
  bash "$ROOT/scripts/optimize-vps.sh" || echo "WARN: optimize-vps skipped"
fi

# Optimize từng gọi `compose stop` kèm docker-compose.yml và tắt nhầm javis.
CNAME="${JAVIS_NAME:-javis}"
if ! docker ps --format '{{.Names}}' | grep -qx "$CNAME"; then
  echo "==> javis không chạy sau optimize - up lại"
  docker compose "${COMPOSE_FILES[@]}" up -d --no-build --remove-orphans
fi
echo "==> health (sau optimize)"
ok_health=0
for i in $(seq 1 20); do
  if curl -fsS -m 5 http://127.0.0.1:7777/health; then
    echo
    ok_health=1
    break
  fi
  echo "waiting health... ($i)"
  sleep 4
done
if [ "$ok_health" != "1" ]; then
  echo "HEALTH_FAIL sau optimize"
  docker compose "${COMPOSE_FILES[@]}" logs javis --tail 80 || true
  docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}' || true
  exit 1
fi

echo "==> done"
