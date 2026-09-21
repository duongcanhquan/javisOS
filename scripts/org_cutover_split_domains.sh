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

# VPS tối giản thường không có dig. getent/python3 luôn có.
quan_ip=""
if command -v getent >/dev/null 2>&1; then
  quan_ip=$(getent ahostsv4 "$QUAN_DOMAIN" 2>/dev/null | awk '{print $1; exit}')
fi
if [ -z "$quan_ip" ]; then
  quan_ip=$(python3 -c "import socket,sys; print(socket.getaddrinfo(sys.argv[1],80,socket.AF_INET)[0][4][0])" "$QUAN_DOMAIN")
fi
quan_ip=$(printf '%s' "$quan_ip" | tr -d '[:space:]')
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
