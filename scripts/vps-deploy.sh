#!/usr/bin/env bash
# Deploy Javis on Ubuntu: PULL image GHCR (không --build trên VPS).
# Hot path MỎNG: login → pull javis → up → health. Seed/optimize chỉ khi bật cờ.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-javis}"

# Plugin user + Antigravity file storage (idempotent, rẻ).
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
# Pixelle tắt trước up (tránh kéo 2 container nặng).
if grep -q '^JAVIS_ENABLE_PIXELLE=' "$ENV_FILE" 2>/dev/null; then
  sed -i.bak 's/^JAVIS_ENABLE_PIXELLE=.*/JAVIS_ENABLE_PIXELLE=false/' "$ENV_FILE" && rm -f "$ENV_FILE.bak"
else
  printf '\nJAVIS_ENABLE_PIXELLE=false\n' >> "$ENV_FILE"
fi

# Git: bỏ qua nếu deploy-vps.yml đã reset đúng WANT_SHA (tránh fetch 2 lần).
if [ "${JAVIS_SKIP_GIT:-0}" = "1" ]; then
  echo "==> git: bỏ qua (đã reset ở workflow)"
else
  echo "==> git fetch"
  git fetch --all --prune
  if [ -n "${WANT_SHA:-}" ]; then
    git fetch origin "$WANT_SHA" 2>/dev/null || true
    git reset --hard "$WANT_SHA"
  else
    git reset --hard origin/main 2>/dev/null || true
    git pull --ff-only origin main || true
  fi
fi

# Image GHCR của CHÍNH repo này.
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

# Chỉ javis (+ tunnel nếu đang dùng profile). Không pull watchtower mỗi lần.
COMPOSE_BASE=(-f docker-compose.yml)
COMPOSE_UP=("${COMPOSE_BASE[@]}")
if docker ps --format '{{.Names}}' | grep -qx "${JAVIS_NAME:-javis}-tunnel"; then
  COMPOSE_UP+=(--profile tunnel)
fi

if [ -n "${GHCR_TOKEN:-}" ]; then
  echo "==> docker login ghcr.io"
  echo "$GHCR_TOKEN" | docker login ghcr.io -u "${GHCR_USER:-github}" --password-stdin \
    || echo "WARN: docker login GHCR thất bại (image public thì pull vẫn được)"
fi

echo "==> gỡ Pixelle (nếu còn), giữ javis chạy khi pull"
docker rm -f javis-pixelle-api javis-pixelle-web 2>/dev/null || true

# Pull ĐÚNG service javis (không kéo cloudflared/watchtower mỗi deploy).
echo "==> pull javis ($JAVIS_IMAGE)"
ok_pull=0
for i in $(seq 1 12); do
  if docker compose "${COMPOSE_BASE[@]}" pull javis; then
    ok_pull=1
    break
  fi
  echo "pull chưa sẵn sàng ($i/12) - chờ 5s"
  sleep 5
done
if [ "$ok_pull" != 1 ]; then
  echo "ERROR: không pull được $JAVIS_IMAGE"
  echo "Không build tại chỗ. Chờ workflow Docker publish xanh rồi deploy lại."
  exit 1
fi

echo "==> up (image mới, không --build)"
if ! docker compose "${COMPOSE_UP[@]}" up -d --no-build --remove-orphans javis; then
  echo "WARN: up lỗi - gỡ container kẹt rồi up lại"
  docker rm -f "${JAVIS_NAME:-javis}" 2>/dev/null || true
  docker compose "${COMPOSE_UP[@]}" up -d --no-build --remove-orphans javis
fi
# Giữ tunnel nếu trước đó đang chạy.
if docker ps -a --format '{{.Names}}' | grep -qx "${JAVIS_NAME:-javis}-tunnel"; then
  docker compose "${COMPOSE_BASE[@]}" --profile tunnel up -d --no-build --remove-orphans tunnel \
    || echo "WARN: tunnel up skipped"
fi

echo "==> health"
ok_health=0
# Startup có thể >1 phút (system sync skills/binary). Đợi dài hơn trước khi báo HEALTH_FAIL.
sleep 8
for i in $(seq 1 45); do
  if curl -fsS -m 3 http://127.0.0.1:7777/health >/dev/null; then
    curl -fsS -m 3 http://127.0.0.1:7777/health || true
    echo
    ok_health=1
    break
  fi
  echo "waiting health... ($i)"
  sleep 3
done
if [ "$ok_health" != "1" ]; then
  echo "HEALTH_FAIL"
  docker compose "${COMPOSE_BASE[@]}" logs javis --tail 80 || true
  exit 1
fi

# Model Moonshine + vendor CDN đã persist trên host → copy lại vào container (nhanh, không tải lại).
if [ -f "$ROOT/scripts/fetch-moonshine-models.sh" ]; then
  echo "==> restore Moonshine models (copy-only)"
  chmod +x "$ROOT/scripts/fetch-moonshine-models.sh"
  if ! bash "$ROOT/scripts/fetch-moonshine-models.sh" --copy-only; then
    echo "ERROR: Moonshine models không vào được container — STT họp sẽ 404."
    exit 1
  fi
else
  echo "WARN: thiếu scripts/fetch-moonshine-models.sh"
fi
if [ -d /root/javis-data/dashboard-vendor ]; then
  echo "==> restore dashboard CDN vendor"
  docker exec -u root "${JAVIS_NAME:-javis}" mkdir -p /app/dashboard/vendor
  for d in mermaid turndown fonts; do
    if [ -d "/root/javis-data/dashboard-vendor/$d" ]; then
      docker cp "/root/javis-data/dashboard-vendor/$d" "${JAVIS_NAME:-javis}:/app/dashboard/vendor/" || true
    fi
  done
  docker exec -u root "${JAVIS_NAME:-javis}" chmod -R a+rX /app/dashboard/vendor/mermaid /app/dashboard/vendor/turndown /app/dashboard/vendor/fonts 2>/dev/null || true
fi

# Seed / optimize: TẮT mặc định (trước đây làm deploy chậm + prune image + health 2 lần).
# Bật khi cần: JAVIS_DEPLOY_EXTRAS=1 bash scripts/vps-deploy.sh
if [ "${JAVIS_DEPLOY_EXTRAS:-0}" = "1" ]; then
  echo "==> extras (seed brief + optimize) vì JAVIS_DEPLOY_EXTRAS=1"
  if [ -f "$ROOT/scripts/seed-morning-brief-vps.sh" ]; then
    chmod +x "$ROOT/scripts/seed-morning-brief-vps.sh"
    bash "$ROOT/scripts/seed-morning-brief-vps.sh" || echo "WARN: seed-morning-brief skipped"
  fi
  if [ -f "$ROOT/scripts/seed-chat-brief-vps.sh" ]; then
    chmod +x "$ROOT/scripts/seed-chat-brief-vps.sh"
    bash "$ROOT/scripts/seed-chat-brief-vps.sh" || echo "WARN: seed-chat-brief skipped"
  fi
  if [ -f "$ROOT/scripts/optimize-vps.sh" ]; then
    chmod +x "$ROOT/scripts/optimize-vps.sh"
    bash "$ROOT/scripts/optimize-vps.sh" || echo "WARN: optimize-vps skipped"
  fi
else
  echo "==> bỏ seed/optimize (hot path). Cần thì: workflow_dispatch seed-* hoặc JAVIS_DEPLOY_EXTRAS=1"
fi

if [ "${FORCE_MORNING_BRIEF_TODAY:-0}" = "1" ] && [ -f "$ROOT/scripts/force-morning-brief-today-vps.sh" ]; then
  echo "==> force morning brief today"
  chmod +x "$ROOT/scripts/force-morning-brief-today-vps.sh"
  bash "$ROOT/scripts/force-morning-brief-today-vps.sh" || echo "WARN: force-morning-brief-today skipped"
fi

echo "==> done"
