#!/usr/bin/env bash
# Phase split: bản cũ → javis-quan (volume external), manager trống trên domain gốc.
# Không xóa volume não. Cần DNS javis-quan đã trỏ đúng IP.
set -euo pipefail

ROOT="${JAVIS_DIR:-/root/javis}"
MGR="${JAVIS_MANAGER_DIR:-/root/javis-manager}"
QUAN_DOMAIN="${QUAN_DOMAIN:-javis-quan.vietmycollege.com}"
MGR_DOMAIN="${MGR_DOMAIN:-javis.vietmycollege.com}"
EXPECT_IP="${EXPECT_IP:-14.225.205.248}"
cd "$ROOT"

quan_ip=$(dig +short "$QUAN_DOMAIN" A | tail -1 | tr -d '[:space:]')
if [ "$quan_ip" != "$EXPECT_IP" ]; then
  echo "SPLIT_FAIL: DNS $QUAN_DOMAIN = '${quan_ip:-empty}' (cần $EXPECT_IP). Làm deploy/org/DNS.md trước."
  exit 1
fi

bash "$ROOT/scripts/org_cutover_preflight.sh"
if ! docker ps --format '{{.Names}}' | grep -qx javis-proxy; then
  echo "SPLIT_FAIL: chưa có javis-proxy (chạy org_cutover_to_proxy.sh trước)"
  exit 1
fi

echo "== domain bản cá nhân → $QUAN_DOMAIN =="
touch "$ROOT/.env"
sed -i.bak "s/^DOMAIN_NAME=.*/DOMAIN_NAME=${QUAN_DOMAIN}/" "$ROOT/.env" && rm -f "$ROOT/.env.bak"
if grep -q '^JAVIS_NAME=' "$ROOT/.env"; then
  sed -i.bak 's/^JAVIS_NAME=.*/JAVIS_NAME=javis-quan/' "$ROOT/.env" && rm -f "$ROOT/.env.bak"
else
  echo 'JAVIS_NAME=javis-quan' >> "$ROOT/.env"
fi

export COMPOSE_PROJECT_NAME=javis
docker compose -f docker-compose.yml -f docker-compose.multi.yml \
  -f deploy/org/docker-compose.tenant-external.yml \
  up -d --no-build --no-deps javis

echo "== wait HTTPS $QUAN_DOMAIN =="
ok=0
for i in $(seq 1 40); do
  if curl -fsS -m 8 -A Mozilla/5.0 "https://${QUAN_DOMAIN}/health" >/dev/null 2>&1; then
    ok=1
    curl -fsS -m 8 -A Mozilla/5.0 "https://${QUAN_DOMAIN}/health" || true
    echo
    break
  fi
  echo "waiting quan https ($i)"
  sleep 3
done
if [ "$ok" != 1 ]; then
  echo "SPLIT_FAIL: $QUAN_DOMAIN chưa healthy. Chưa dựng manager."
  exit 1
fi

echo "== manager trống $MGR_DOMAIN =="
mkdir -p "$MGR"
cp -f "$ROOT/docker-compose.yml" "$MGR/"
cp -f "$ROOT/docker-compose.multi.yml" "$MGR/"
if [ ! -f "$MGR/.env" ]; then
  cp -f "$ROOT/deploy/org/env.manager.example" "$MGR/.env"
  # Không để mật khẩu mẫu trên máy thật: nếu chưa sửa, tạo random.
  if grep -q 'doi-mat-khau-manh' "$MGR/.env"; then
    pw=$(head -c 18 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 20)
    sed -i "s/doi-mat-khau-manh/${pw}/" "$MGR/.env"
    echo "MANAGER_ADMIN_PASSWORD_SET (xem $MGR/.env, chmod 600)"
  fi
fi
chmod 600 "$MGR/.env"
# Image đang chạy trên bản quan.
img=$(docker inspect javis-quan --format '{{.Config.Image}}' 2>/dev/null \
  || docker inspect javis --format '{{.Config.Image}}')
if grep -q '^JAVIS_IMAGE=' "$MGR/.env"; then
  sed -i "s|^JAVIS_IMAGE=.*|JAVIS_IMAGE=${img}|" "$MGR/.env"
else
  echo "JAVIS_IMAGE=${img}" >> "$MGR/.env"
fi

export COMPOSE_PROJECT_NAME=javis-manager
cd "$MGR"
docker compose -f docker-compose.yml -f docker-compose.multi.yml up -d --no-build --no-deps javis

echo "== wait HTTPS $MGR_DOMAIN =="
okm=0
for i in $(seq 1 40); do
  if curl -fsS -m 8 -A Mozilla/5.0 "https://${MGR_DOMAIN}/health" >/dev/null 2>&1; then
    okm=1
    curl -fsS -m 8 -A Mozilla/5.0 "https://${MGR_DOMAIN}/health" || true
    echo
    break
  fi
  echo "waiting manager https ($i)"
  sleep 3
done
if [ "$okm" != 1 ]; then
  echo "SPLIT_WARN: manager chưa healthy, bản quan phải vẫn sống"
  curl -fsS -m 8 -A Mozilla/5.0 "https://${QUAN_DOMAIN}/health" || true
  echo
  exit 1
fi

echo "SPLIT_OK quan=$QUAN_DOMAIN manager=$MGR_DOMAIN"
docker ps --format '{{.Names}} {{.Status}}' | grep -E 'javis|proxy' || true
