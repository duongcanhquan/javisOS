#!/usr/bin/env bash
# Dựng lại container tenant bị mất (prune) từ volume/não còn giữ. Không xóa ổ.
set -euo pipefail

DIR="${JAVIS_DIR:-}"
if [ -z "$DIR" ]; then
  if [ -d "$HOME/javis-os" ]; then DIR="$HOME/javis-os"
  elif [ -d /root/javis-os ]; then DIR=/root/javis-os
  else DIR="$HOME/javis-os"
  fi
fi

echo "=== DISK / VERSION ==="
date -u
df -h / | head -2
docker exec javis-manager cat /app/VERSION 2>/dev/null || echo missing

echo "=== HOT-PATCH org_docker + org_coord (restore + trần tay) ==="
PATCHED=0
if [ -f "$DIR/server/org_docker.py" ]; then
  docker cp "$DIR/server/org_docker.py" javis-manager:/app/server/org_docker.py
  PATCHED=1
fi
if [ -f "$DIR/server/org_coord.py" ]; then
  docker cp "$DIR/server/org_coord.py" javis-manager:/app/server/org_coord.py
  PATCHED=1
fi
if [ "$PATCHED" = 1 ]; then
  docker restart javis-manager
  for i in $(seq 1 40); do
    curl -fsS -m 3 http://127.0.0.1:7778/health >/dev/null 2>&1 && break
    sleep 2
  done
  sleep 3
fi

echo "=== Pull image nếu thiếu ==="
IMG=$(docker inspect javis-manager --format '{{.Config.Image}}' 2>/dev/null || echo ghcr.io/duongcanhquan/javisos:latest)
docker pull "$IMG" || true

echo "=== RESTORE mọi tenant thiếu container ==="
# Bắt buộc -i: không có stdin thì python nhận EOF, thoát 0, không làm gì (lỗi lần trước).
docker exec -i javis-manager python - <<'PY'
import sys
sys.path.insert(0, "/app/server")
import org_tenants as ot, org_docker as od

assert hasattr(od, "restore_tenant_container"), "thiếu restore_tenant_container trên manager"
ts = ot.load().get("tenants") or []
print("tenants_in_registry", len(ts), flush=True)
ok = fail = skip = 0
for t in ts:
    if t.get("protected") or t.get("deleted_at"):
        skip += 1
        continue
    slug = str(t.get("slug") or "").strip()
    if not slug:
        skip += 1
        continue
    cname = str(t.get("container") or f"javis-{slug}")
    exists = bool(od.inspect_name(cname))
    st = od.container_status(cname) if exists else "missing"
    print("before", slug, st, "exists", exists, flush=True)
    if exists:
        skip += 1
        continue
    try:
        # Chỉ tạo container, không start hết (tránh đầy RAM). Admin/user bật khi cần.
        od.restore_tenant_container(slug, start_after=False)
        print("restored", slug, od.container_status(cname), flush=True)
        ok += 1
    except Exception as e:
        print("FAIL", slug, type(e).__name__, e, flush=True)
        fail += 1
try:
    od.sync_park()
    print("sync_park ok", flush=True)
except Exception as e:
    print("park", e, flush=True)
print("SUMMARY restored", ok, "fail", fail, "skip", skip, flush=True)
PY

docker ps -a --format 'table {{.Names}}\t{{.Status}}' | grep -E '^javis-|NAMES' || true

echo "=== Coord + thử start ==="
docker exec -i javis-manager python - <<'PY'
import sys
sys.path.insert(0, "/app/server")
import org_coord as oc, org_docker as od
c = oc.coord()
print(
    "host_ram_mb", c.get("host_ram_mb"),
    "suggest", c.get("suggest"),
    "max_running", c.get("max_running"),
    "effective", oc.effective_max(),
    "AUTO_CAP", oc.AUTO_CAP,
    flush=True,
)
# Giữ trần tay 16 nếu đang thấp hơn (admin đã muốn 16)
if int(c.get("max_running") or 0) < 16:
    oc.put_coord(max_running=16)
    print("raised_max_running_to", oc.coord().get("max_running"), "effective", oc.effective_max(), flush=True)
slug = "thuha"
try:
    od.start_with_capacity(slug)
    print("START_OK", slug, od.container_status("javis-"+slug), flush=True)
except Exception as e:
    print("START_FAIL", type(e).__name__, e, flush=True)
    try:
        od.start_with_capacity("bach")
        print("START_OK bach", od.container_status("javis-bach"), flush=True)
    except Exception as e2:
        print("START_FAIL bach", type(e2).__name__, e2, flush=True)
print("people_running", len(od.people_running()), [t.get("slug") for t in od.people_running()], flush=True)
PY

echo RESTORE_TENANTS_DONE
