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

# Luôn hot-patch khi có file nguồn (mỗi lần chạy có thể có vá mới).
if [ -n "$PATCH_SRC" ] && [ -f "$PATCH_SRC" ]; then
  echo "patching from $PATCH_SRC"
  docker cp "$PATCH_SRC" javis-manager:/app/server/org_docker.py
  docker restart javis-manager
  for i in $(seq 1 40); do
    if curl -fsS -m 3 http://127.0.0.1:7778/health >/dev/null 2>&1; then
      echo "manager health ok after patch"
      break
    fi
    sleep 2
  done
  sleep 3
else
  echo "WARN: không có org_docker.py để patch - dùng code trong image"
fi

docker exec javis-manager python -c '
import sys
sys.path.insert(0,"/app/server")
import org_docker as od
for n in ("container_serving_ready","publish_tenant_route","_ensure_lock","_health_status"):
    assert hasattr(od, n), n
# marker vá last-active khi start
src = open("/app/server/org_docker.py", encoding="utf-8").read()
assert "org-last-active" in src.split("def start(",1)[-1].split("def stop(",1)[0]
print("helpers_ok_after_patch")
'

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

echo "=== CHẨN ĐOÁN START thô (thuha) ==="
docker exec javis-manager python -c '
import sys, json
sys.path.insert(0, "/app/server")
import org_tenants as ot, org_docker as od
from urllib.parse import quote

slug = "thuha"
cname = "javis-" + slug
data = od.inspect_name(cname)
st = (data.get("State") or {}) if data else {}
print("inspect_before", json.dumps({
    "status": od.container_status(cname),
    "Running": st.get("Running"),
    "ExitCode": st.get("ExitCode"),
    "Error": (st.get("Error") or "")[:200],
    "OOMKilled": st.get("OOMKilled"),
    "FinishedAt": st.get("FinishedAt"),
}, ensure_ascii=False))
cfg = (data.get("Config") or {}) if data else {}
labels = cfg.get("Labels") or {}
print("caddy_label", (labels.get("caddy") or "")[:80])
print("image", (cfg.get("Image") or "")[:80])
hc = (data.get("HostConfig") or {}) if data else {}
print("memory", hc.get("Memory"), "network", hc.get("NetworkMode"))
binds = hc.get("Binds") or []
print("binds_n", len(binds), "binds", binds[:6])

# start thô qua Docker API
od.invalidate_status_cache()
r = od._docker_api("POST", "/containers/%s/start" % quote(cname), timeout=60.0)
print("raw_start_http", r.status_code, (r.text or "")[:300])
od.invalidate_status_cache(cname)
data2 = od.inspect_name(cname)
st2 = (data2.get("State") or {}) if data2 else {}
print("inspect_after_raw", json.dumps({
    "status": od.container_status(cname),
    "Running": st2.get("Running"),
    "ExitCode": st2.get("ExitCode"),
    "Error": (st2.get("Error") or "")[:200],
    "OOMKilled": st2.get("OOMKilled"),
    "Status": st2.get("Status"),
}, ensure_ascii=False))
if st2.get("Running"):
    print("RAW_START_OK")
else:
    # logs nếu chết ngay
    try:
        lr = od._docker_api("GET", "/containers/%s/logs?stdout=1&stderr=1&tail=40" % quote(cname), timeout=20.0)
        print("logs_http", lr.status_code)
        print("logs_tail", (lr.text or "")[-1500:])
    except Exception as e:
        print("logs_err", e)
'

echo "=== THỬ WAKE 1 MÁY MẪU (thuha) ==="
docker exec javis-manager python -c '
import sys, re, time
sys.path.insert(0, "/app/server")
import org_tenants as ot, org_docker as od
from urllib.parse import quote

slug = "thuha"
rec = ot.get(slug)
print("rec", bool(rec), "paused", bool((rec or {}).get("paused")))
cname = "javis-" + slug
print("status_before", od.container_status(cname))
print("serving_before", od.container_serving_ready(cname))
print("last_active_file", od.read_last_active(cname, rec, force=True))

try:
    print("start_with_capacity...")
    od.start_with_capacity(slug)
    print("start_with_capacity_ok", od.container_status(cname))
    print("last_active_after_start", od.read_last_active(cname, ot.get(slug), force=True), "now", int(time.time()))
except Exception as e:
    print("start_with_capacity_err", type(e).__name__, e)

try:
    r = od.ensure_tenant_ready(slug, wait_sec=150)
    print("ensure", {k: r.get(k) for k in ("ok", "status", "slug", "container")})
    if not r.get("ok"):
        html = (r.get("html") or "")
        m = re.search(r"<p[^>]*>(.*?)</p>", html, re.I | re.S)
        body = re.sub(r"<[^>]+>", "", m.group(1) if m else html)
        print("ensure_body", body.replace("\n", " ")[:400])
except Exception as e:
    print("ensure_err", type(e).__name__, e)

print("status_after", od.container_status(cname))
print("serving_after", od.container_serving_ready(cname))
print("health_inside", od._health_inside(cname))
try:
    lr = od._docker_api("GET", "/containers/%s/logs?stdout=1&stderr=1&tail=60" % quote(cname), timeout=20.0)
    print("tenant_logs", (lr.text or "")[-2000:])
except Exception as e:
    print("tenant_logs_err", e)
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
    print("WAKE_FAIL sample still", st, "exit_hint_check_logs")
'

echo "=== PARK SAU ==="
docker inspect javis-park --format 'Running={{.State.Running}} Health={{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} hosts={{index .Config.Labels "javis.org.park.hosts"}}' 2>/dev/null || echo NO_PARK
echo
echo "=== MANAGER LOG (wake/start) ==="
docker logs javis-manager --since 15m 2>&1 | grep -iE 'org |wake|start|park|ensure|RAM|coord|error|FAIL|NameError' | tail -50 || true

echo FIX_TENANT_WAKE_DONE
