#!/usr/bin/env bash
# Chẩn đoán + vá wake tenant: hot-patch org_docker nếu thiếu helper, sync park, thử bật 1 máy mẫu.
set -euo pipefail

DIR="${JAVIS_DIR:-}"
if [ -z "$DIR" ]; then
  if [ -d "$HOME/javis-os" ]; then DIR="$HOME/javis-os"
  elif [ -d /root/javis-os ]; then DIR=/root/javis-os
  else DIR="$(pwd)"
  fi
fi

echo "=== HOST / VERSION ==="
date -u
free -m | head -2
docker exec javis-manager cat /app/VERSION 2>/dev/null || echo missing

echo "=== HOT-PATCH org_docker (nếu thiếu helper wake) ==="
PATCH_SRC=""
if [ -f "$DIR/server/org_docker.py" ]; then
  PATCH_SRC="$DIR/server/org_docker.py"
elif [ -f /tmp/javis-fix-wake/server/org_docker.py ]; then
  PATCH_SRC=/tmp/javis-fix-wake/server/org_docker.py
elif [ -f /tmp/javis-fix-wake/org_docker.py ]; then
  PATCH_SRC=/tmp/javis-fix-wake/org_docker.py
fi

need_patch=0
if ! docker exec javis-manager python -c '
import sys
sys.path.insert(0,"/app/server")
import org_docker as od
for n in ("container_serving_ready","publish_tenant_route","_ensure_lock","_health_status"):
    if not hasattr(od, n):
        raise SystemExit(2)
print("helpers_ok")
' 2>/dev/null; then
  need_patch=1
fi

if [ "$need_patch" = "1" ]; then
  if [ -z "$PATCH_SRC" ] || [ ! -f "$PATCH_SRC" ]; then
    echo "FAIL: thiếu helper wake trên manager và không có file patch"
    exit 1
  fi
  echo "patching from $PATCH_SRC"
  docker cp "$PATCH_SRC" javis-manager:/app/server/org_docker.py
  # Reload: restart process trong container (compose restart)
  docker restart javis-manager
  for i in $(seq 1 40); do
    if curl -fsS -m 3 http://127.0.0.1:7778/health >/dev/null 2>&1; then
      echo "manager health ok after patch"
      break
    fi
    sleep 2
  done
  sleep 3
  docker exec javis-manager python -c '
import sys
sys.path.insert(0,"/app/server")
import org_docker as od
for n in ("container_serving_ready","publish_tenant_route","_ensure_lock","_health_status"):
    assert hasattr(od, n), n
print("helpers_ok_after_patch")
'
else
  echo "helpers already present"
fi

echo "=== CONTAINERS ==="
docker ps -a --format 'table {{.Names}}\t{{.Status}}' | grep -E '^javis-|NAMES' || true

echo "=== PARK TRƯỚC ==="
docker inspect javis-park --format 'Running={{.State.Running}} Status={{.State.Status}} Health={{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' 2>/dev/null || echo NO_PARK

echo "=== MANAGER HEALTH ==="
curl -fsS -m 5 http://127.0.0.1:7778/health && echo || echo MANAGER_HEALTH_FAIL

echo "=== COORD + REGISTRY ==="
docker exec javis-manager python -c '
import sys
sys.path.insert(0, "/app/server")
import org_tenants as ot, org_coord as oc, org_docker as od
c = oc.coord()
print("idle", c.get("idle_minutes"), "max", c.get("max_running"), "eff", oc.effective_max(), "avail", c.get("host_avail_mb"))
ts = ot.load().get("tenants") or []
print("tenants", len(ts))
run = od.people_running()
print("running", len(run), [t.get("slug") for t in run])
for t in ts:
    if t.get("protected") or t.get("deleted_at"):
        continue
    slug = t.get("slug")
    cname = t.get("container") or ("javis-" + str(slug))
    st = od.container_status(cname)
    print("st", slug, st, "paused", bool(t.get("paused")), "domain", ot.tenant_domain(slug))
'

echo "=== SYNC PARK (tắt unhealthy) ==="
docker exec javis-manager python -c '
import sys
sys.path.insert(0, "/app/server")
import org_docker as od
od.sync_park()
print("sync_park ok")
print("park_status", od.container_status("javis-park"))
data = od.inspect_name("javis-park")
st = (data.get("State") or {}) if data else {}
h = st.get("Health") if isinstance(st.get("Health"), dict) else {}
print("park_health", h.get("Status") or "none", "running", bool(st.get("Running")))
labels = ((data.get("Config") or {}).get("Labels") or {}) if data else {}
hosts = (labels.get("javis.org.park.hosts") or "")[:200]
print("park_hosts", hosts)
'

echo "=== THỬ WAKE 1 MÁY MẪU (thuha) ==="
docker exec javis-manager python -c '
import sys
sys.path.insert(0, "/app/server")
import org_tenants as ot, org_docker as od

slug = "thuha"
rec = ot.get(slug)
print("rec", bool(rec), "paused", bool((rec or {}).get("paused")))
cname = "javis-" + slug
print("status_before", od.container_status(cname))
print("serving_before", od.container_serving_ready(cname))

try:
    r = od.ensure_tenant_ready(slug, wait_sec=90)
    print("ensure", {k: r.get(k) for k in ("ok", "status", "slug", "container")})
    if not r.get("ok"):
        html = (r.get("html") or "")[:240]
        print("ensure_html", html.replace("\n", " "))
except Exception as e:
    print("ensure_err", type(e).__name__, e)

print("status_after", od.container_status(cname))
print("serving_after", od.container_serving_ready(cname))
import urllib.request
try:
    with urllib.request.urlopen("http://%s:7777/health" % cname, timeout=5) as resp:
        print("tenant_health", resp.status, resp.read()[:80])
except Exception as e:
    print("tenant_health_err", type(e).__name__, e)

st = od.container_status(cname)
if st == "running" and od.container_serving_ready(cname):
    print("WAKE_OK sample tenant serving")
else:
    print("WAKE_FAIL sample still", st)
'

echo "=== PARK SAU ==="
docker inspect javis-park --format 'Running={{.State.Running}} Health={{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} hosts={{index .Config.Labels "javis.org.park.hosts"}}' 2>/dev/null || echo NO_PARK
echo
echo "=== MANAGER LOG (wake/start) ==="
docker logs javis-manager --since 15m 2>&1 | grep -iE 'org |wake|start|park|ensure|RAM|coord|error|FAIL|NameError' | tail -50 || true

echo FIX_TENANT_WAKE_DONE
