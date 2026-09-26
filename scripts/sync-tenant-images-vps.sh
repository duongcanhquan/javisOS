#!/usr/bin/env bash
# Đồng bộ image mới lên mọi máy người (giữ volume). Chạy trên VPS sau deploy
# khi manager đã pull latest - apply_public_hosts gắn lại nếu digest lệch.
set -euo pipefail

IMG="${JAVIS_IMAGE:-ghcr.io/duongcanhquan/javisos:latest}"
echo "==> pull $IMG"
docker pull "$IMG" || echo "WARN: pull thất bại (có thể đã có local)"

echo "==> recreate Javis gốc nếu đang chạy (manager)"
if docker inspect javis-manager >/dev/null 2>&1; then
  MGR_DIR="${JAVIS_MANAGER_DIR:-/root/javis-manager}"
  if [ -d "$MGR_DIR" ] && [ -f "$MGR_DIR/docker-compose.yml" ]; then
    (
      cd "$MGR_DIR"
      export COMPOSE_PROJECT_NAME=javis-manager
      export JAVIS_IMAGE="$IMG"
      MGR_FILES=(-f docker-compose.yml)
      [ -f docker-compose.multi.yml ] && MGR_FILES+=(-f docker-compose.multi.yml)
      [ -f docker-compose.manager.yml ] && MGR_FILES+=(-f docker-compose.manager.yml)
      docker compose "${MGR_FILES[@]}" pull javis || true
      docker compose "${MGR_FILES[@]}" up -d --no-build --force-recreate javis
    )
    for i in $(seq 1 40); do
      if curl -fsS -m 3 http://127.0.0.1:7778/health >/dev/null 2>&1; then
        echo "manager health ok"
        break
      fi
      sleep 2
    done
  else
    echo "WARN: thiếu $MGR_DIR - bỏ recreate compose manager"
  fi
else
  echo "WARN: không có container javis-manager"
fi

echo "==> apply_public_hosts mọi tenant (gắn image mới, giữ volume)"
docker exec -i javis-manager python - <<'PY'
import sys
sys.path.insert(0, "/app/server")
import org_tenants as ot
import org_docker as od

ts = (ot.load().get("tenants") or [])
print("tenants", len(ts))
ok = fail = skip = 0
for t in ts:
    if t.get("deleted_at"):
        skip += 1
        continue
    if t.get("protected"):
        print("skip protected", t.get("slug"))
        skip += 1
        continue
    slug = str(t.get("slug") or "").strip()
    if not slug:
        skip += 1
        continue
    cname = str(t.get("container") or f"javis-{slug}")
    try:
        before = od.image_short(cname) if od.inspect_name(cname) else "(missing)"
        od.apply_public_hosts(slug)
        after = od.image_short(cname) if od.inspect_name(cname) else "(missing)"
        st = od.container_status(cname)
        print(f"ok {slug} {before} -> {after} status={st}")
        ok += 1
    except Exception as e:
        print(f"FAIL {slug}: {e}")
        fail += 1
print(f"done ok={ok} fail={fail} skip={skip}")
if fail:
    sys.exit(1)
PY

echo "==> verify prompt-help.js + VERSION trên mọi container javis-*"
miss=0
while read -r name; do
  [ -n "$name" ] || continue
  ver=$(docker exec "$name" cat /app/VERSION 2>/dev/null | tr -d ' \n\r' || echo missing)
  if docker exec "$name" test -f /app/dashboard/prompt-help.js 2>/dev/null; then
    echo "OK  $name VERSION=$ver prompt-help.js"
  else
    echo "MISS $name VERSION=$ver thiếu prompt-help.js"
    miss=$((miss + 1))
  fi
done < <(docker ps --format '{{.Names}}' | grep -E '^javis-' | grep -vE 'proxy|park|pixelle' | sort)

if [ "$miss" != 0 ]; then
  echo "ERROR: $miss máy thiếu prompt-help.js"
  exit 1
fi
echo "OK mọi máy có nút ? prompt-help (0.56.42+)"
