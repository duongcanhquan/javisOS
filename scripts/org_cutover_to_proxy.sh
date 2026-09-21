#!/usr/bin/env bash
# Phase proxy: HTTPS qua javis-proxy, VẪN domain javis.vietmycollege.com, CÙNG volume.
# Không xóa volume. Không gỡ stack kèm volume. Rollback Caddy trong project nếu health đỏ.
set -euo pipefail

ROOT="${JAVIS_DIR:-/root/javis}"
DOMAIN="${KEEP_DOMAIN:-javis.vietmycollege.com}"
cd "$ROOT"

echo "== cutover to proxy; keep $DOMAIN ; dir $ROOT =="
bash "$ROOT/scripts/org_cutover_preflight.sh"

if [ ! -f "$ROOT/docker-compose.yml" ] || [ ! -f "$ROOT/docker-compose.multi.yml" ]; then
  echo "PROXY_FAIL: thiếu compose trong $ROOT"
  exit 1
fi

# .env: bind loopback + domain hiện tại. Không xoá secret.
touch "$ROOT/.env"
if grep -q '^JAVIS_BIND=' "$ROOT/.env"; then
  sed -i.bak 's/^JAVIS_BIND=.*/JAVIS_BIND=127.0.0.1/' "$ROOT/.env" && rm -f "$ROOT/.env.bak"
else
  echo 'JAVIS_BIND=127.0.0.1' >> "$ROOT/.env"
fi
if grep -q '^DOMAIN_NAME=' "$ROOT/.env"; then
  sed -i.bak "s/^DOMAIN_NAME=.*/DOMAIN_NAME=${DOMAIN}/" "$ROOT/.env" && rm -f "$ROOT/.env.bak"
else
  echo "DOMAIN_NAME=${DOMAIN}" >> "$ROOT/.env"
fi
if ! grep -q '^JAVIS_NAME=' "$ROOT/.env"; then
  echo 'JAVIS_NAME=javis' >> "$ROOT/.env"
fi

docker network create javis-web 2>/dev/null || true

PROXY_DIR="${JAVIS_PROXY_DIR:-/root/javis-proxy}"
mkdir -p "$PROXY_DIR"
cp -f "$ROOT/docker-compose.proxy.yml" "$PROXY_DIR/docker-compose.yml"

echo "== recreate javis with multi labels (volumes named, keep) =="
export COMPOSE_PROJECT_NAME=javis
docker compose -f docker-compose.yml -f docker-compose.multi.yml up -d --no-build --no-deps javis

echo "== stop in-project caddy (443) then start proxy =="
docker stop javis-caddy 2>/dev/null || true
docker rm javis-caddy 2>/dev/null || true
docker compose -f "$PROXY_DIR/docker-compose.yml" -p javis-proxy up -d

echo "== wait HTTPS $DOMAIN =="
ok=0
for i in $(seq 1 40); do
  if curl -fsS -m 8 -A Mozilla/5.0 "https://${DOMAIN}/health" >/dev/null 2>&1; then
    curl -fsS -m 8 -A Mozilla/5.0 "https://${DOMAIN}/health" || true
    echo
    ok=1
    break
  fi
  echo "waiting https ($i)"
  sleep 3
done

if [ "$ok" != 1 ]; then
  echo "PROXY_FAIL: rollback Caddy trong project"
  docker compose -p javis-proxy -f "$PROXY_DIR/docker-compose.yml" stop || true
  docker compose -f docker-compose.yml -f docker-compose.https.yml up -d --no-build caddy || true
  exit 1
fi

echo "PROXY_OK $DOMAIN"
