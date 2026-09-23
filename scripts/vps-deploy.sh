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
# Sau org-split, máy cá nhân tên javis-quan chứ không còn javis.
if [ -z "${JAVIS_NAME:-}" ]; then
  _jn=$(grep -E '^JAVIS_NAME=' "$ENV_FILE" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d ' "')
  if [ -n "$_jn" ]; then export JAVIS_NAME="$_jn"; fi
fi
# Bản cá nhân không được giữ domain gốc - Caddy sẽ lái javis.vietmycollege.com vào não quan.
if ! grep -qE '^JAVIS_ORG_MANAGER=(true|1|yes|on)$' "$ENV_FILE" 2>/dev/null; then
  if grep -qE '^DOMAIN_NAME=javis\.vietmycollege\.com$' "$ENV_FILE" 2>/dev/null; then
    echo "==> tách domain bản cá nhân → javis-quan.vietmycollege.com (không đụng volume)"
    sed -i.bak 's/^DOMAIN_NAME=.*/DOMAIN_NAME=javis-quan.vietmycollege.com/' "$ENV_FILE" && rm -f "$ENV_FILE.bak"
  fi
  if grep -qE '^JAVIS_ORG_HOST_PREFIX=' "$ENV_FILE"; then
    sed -i 's/^JAVIS_ORG_HOST_PREFIX=.*/JAVIS_ORG_HOST_PREFIX=vmos/' "$ENV_FILE"
  else
    echo 'JAVIS_ORG_HOST_PREFIX=vmos' >> "$ENV_FILE"
  fi
  if grep -qE '^WORKSPACE_NAME=' "$ENV_FILE"; then
    sed -i 's/^WORKSPACE_NAME=.*/WORKSPACE_NAME=VietMy OS/' "$ENV_FILE"
  else
    echo 'WORKSPACE_NAME=VietMy OS' >> "$ENV_FILE"
  fi
  _want_dom='vmos-quan.vietmycollege.com'
  if grep -qE '^DOMAIN_NAME=.*(javis-quan|vmos-quan)\.vietmycollege\.com' "$ENV_FILE" 2>/dev/null; then
    if ! grep -qE "^DOMAIN_NAME=${_want_dom}$" "$ENV_FILE"; then
      echo "==> domain công khai bản cá nhân → vmos-quan.vietmycollege.com"
      sed -i "s|^DOMAIN_NAME=.*|DOMAIN_NAME=${_want_dom}|" "$ENV_FILE"
    fi
  fi
fi
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
# Tránh kéo nhầm fork cũ (blogminhquy → hay kẹt 0.55.56).
if grep -qiE 'blogminhquy/javis' "$ENV_FILE" 2>/dev/null; then
  echo "==> Sửa JAVIS_IMAGE trong .env: bỏ blogminhquy → duongcanhquan/javisos"
  if grep -qE '^JAVIS_IMAGE=' "$ENV_FILE"; then
    sed -i.bak 's|^JAVIS_IMAGE=.*|JAVIS_IMAGE=ghcr.io/duongcanhquan/javisos:latest|' "$ENV_FILE" && rm -f "$ENV_FILE.bak"
  else
    echo 'JAVIS_IMAGE=ghcr.io/duongcanhquan/javisos:latest' >> "$ENV_FILE"
  fi
fi

# Quyền gọi Docker từ user javis (10001): GID của docker.sock, không mặc định 998.
if [ -S /var/run/docker.sock ]; then
  _dg=$(stat -c '%g' /var/run/docker.sock 2>/dev/null || echo 998)
  echo "==> DOCKER_GID=${_dg}"
  if grep -qE '^DOCKER_GID=' "$ENV_FILE"; then
    sed -i "s/^DOCKER_GID=.*/DOCKER_GID=${_dg}/" "$ENV_FILE"
  else
    echo "DOCKER_GID=${_dg}" >> "$ENV_FILE"
  fi
  export DOCKER_GID="${_dg}"
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
# Caddy HTTPS trong project CHỈ khi CHƯA có proxy ngoài.
# Có javis-proxy thì dùng multi.yml (nhãn domain), không bật javis-caddy (tránh tranh 443).
if docker ps --format '{{.Names}}' | grep -qx javis-proxy; then
  if [ -f "$ROOT/docker-compose.multi.yml" ]; then
    COMPOSE_UP+=(-f docker-compose.multi.yml)
    echo "==> proxy ngoài (javis-proxy) + docker-compose.multi.yml"
  fi
elif [ -f "$ROOT/docker-compose.https.yml" ]; then
  if docker ps -a --format '{{.Names}}' | grep -qx "${JAVIS_NAME:-javis}-caddy" \
    || docker ps -a --format '{{.Names}}' | grep -qx javis-caddy \
    || docker volume ls -q | grep -qE 'caddy-data|caddy_data'; then
    COMPOSE_UP+=(-f docker-compose.https.yml)
    echo "==> giữ Caddy HTTPS (docker-compose.https.yml)"
  fi
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
UP_SERVICES=(javis)
if printf '%s ' "${COMPOSE_UP[@]}" | grep -q 'docker-compose.https.yml'; then
  UP_SERVICES+=(caddy)
fi
if ! docker compose "${COMPOSE_UP[@]}" up -d --no-build --remove-orphans "${UP_SERVICES[@]}"; then
  echo "WARN: up lỗi - gỡ container kẹt rồi up lại"
  docker rm -f "${JAVIS_NAME:-javis}" 2>/dev/null || true
  docker compose "${COMPOSE_UP[@]}" up -d --no-build --remove-orphans "${UP_SERVICES[@]}"
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
# Sau org-split máy cá nhân tên javis-quan, không còn container tên javis.
export JAVIS_CONTAINER="${JAVIS_CONTAINER:-${JAVIS_NAME:-javis}}"
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
if [ -f "$ROOT/scripts/patch-moonshine-wasm-threads.sh" ]; then
  echo "==> patch Moonshine WASM pthread pool (max 2)"
  chmod +x "$ROOT/scripts/patch-moonshine-wasm-threads.sh"
  bash "$ROOT/scripts/patch-moonshine-wasm-threads.sh" || echo "WARN: moonshine pthread patch skipped"
fi
if [ -d /root/javis-data/dashboard-vendor ]; then
  echo "==> restore dashboard CDN vendor"
  docker exec -u root "${JAVIS_CONTAINER}" mkdir -p /app/dashboard/vendor
  for d in mermaid turndown fonts; do
    if [ -d "/root/javis-data/dashboard-vendor/$d" ]; then
      docker cp "/root/javis-data/dashboard-vendor/$d" "${JAVIS_CONTAINER}:/app/dashboard/vendor/" || true
    fi
  done
  docker exec -u root "${JAVIS_CONTAINER}" chmod -R a+rX /app/dashboard/vendor/mermaid /app/dashboard/vendor/turndown /app/dashboard/vendor/fonts 2>/dev/null || true
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
  if [ -f "$ROOT/scripts/seed-github-trending-vps.sh" ]; then
    chmod +x "$ROOT/scripts/seed-github-trending-vps.sh"
    bash "$ROOT/scripts/seed-github-trending-vps.sh" || echo "WARN: seed-github-trending skipped"
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

# Javis gốc (tổ chức) nằm thư mục khác. Cùng image, không --remove-orphans, không đụng volume quan.
MGR_DIR="${JAVIS_MANAGER_DIR:-/root/javis-manager}"
if [ -f "$ENV_FILE" ] && grep -qE '^JAVIS_ORG_MANAGER=(true|1|yes|on)$' "$ENV_FILE"; then
  echo "==> đang deploy ngay Javis gốc - không lặp $MGR_DIR"
elif [ -d "$MGR_DIR" ] && [ -f "$MGR_DIR/docker-compose.yml" ]; then
  echo "==> cập nhật Javis gốc ($MGR_DIR), không đụng volume javis_javis-*"
  mkdir -p "$MGR_DIR"
  cp -f "$ROOT/docker-compose.yml" "$MGR_DIR/"
  if [ -f "$ROOT/docker-compose.multi.yml" ]; then
    cp -f "$ROOT/docker-compose.multi.yml" "$MGR_DIR/"
  fi
  # Gắn docker CLI + socket để nút Đồng bộ skill chạy trong container, không cần SSH.
  if [ -f "$ROOT/docker-compose.manager.yml" ]; then
    cp -f "$ROOT/docker-compose.manager.yml" "$MGR_DIR/"
  fi
  touch "$MGR_DIR/.env"
  chmod 600 "$MGR_DIR/.env"
  _mgr_set() {
    local k=$1 v=$2
    if grep -qE "^${k}=" "$MGR_DIR/.env"; then
      sed -i "s|^${k}=.*|${k}=${v}|" "$MGR_DIR/.env"
    else
      printf '%s=%s\n' "$k" "$v" >> "$MGR_DIR/.env"
    fi
  }
  _mgr_set JAVIS_ORG_MANAGER true
  _mgr_set JAVIS_ROLE manager
  _mgr_set JAVIS_ORG_TENANT false
  _mgr_set JAVIS_NAME javis-manager
  _mgr_set DOMAIN_NAME javis.vietmycollege.com
  _mgr_set JAVIS_HOST_PORT 7778
  _mgr_set JAVIS_BIND 127.0.0.1
  _mgr_set JAVIS_ORG_HOST_PREFIX vmos
  if [ -n "${DOCKER_GID:-}" ]; then
    _mgr_set DOCKER_GID "$DOCKER_GID"
  fi
  (
    cd "$MGR_DIR"
    unset JAVIS_NAME JAVIS_HOST_PORT DOMAIN_NAME JAVIS_ORG_MANAGER JAVIS_ORG_TENANT JAVIS_ORG_HOST_PREFIX
    export COMPOSE_PROJECT_NAME=javis-manager
    export JAVIS_IMAGE
    MGR_FILES=(-f docker-compose.yml)
    if [ -f docker-compose.multi.yml ]; then
      MGR_FILES+=(-f docker-compose.multi.yml)
    fi
    if [ -f docker-compose.manager.yml ]; then
      MGR_FILES+=(-f docker-compose.manager.yml)
    fi
    docker compose "${MGR_FILES[@]}" pull javis || echo "WARN: pull Javis gốc thất bại"
    docker compose "${MGR_FILES[@]}" up -d --no-build --force-recreate javis
  )
  echo "==> health Javis gốc (:7778)"
  _mgr_ok=0
  for i in $(seq 1 30); do
    if curl -fsS -m 3 http://127.0.0.1:7778/health >/dev/null; then
      curl -fsS -m 3 http://127.0.0.1:7778/health || true
      echo
      _mgr_ok=1
      break
    fi
    echo "waiting Javis gốc... ($i)"
    sleep 2
  done
  if [ "$_mgr_ok" != 1 ]; then
    echo "WARN: Javis gốc chưa trả /health sau recreate - thử https://javis.vietmycollege.com"
  fi
else
  echo "==> không có $MGR_DIR - bỏ cập nhật Javis gốc"
fi

echo "==> done"
