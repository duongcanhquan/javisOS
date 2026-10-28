#!/usr/bin/env bash
# Rà toàn bộ tenant trên VPS: Docker, health, CSS, agy/model, usercustomize hỏng.
# Có thể tự chữa nhẹ: tắt usercustomize đệ quy, vá main.py FileResponse, apply env FORCE_FILE.
set -euo pipefail

DIR="${JAVIS_DIR:-}"
if [ -z "$DIR" ]; then
  if [ -d "$HOME/javis-os" ]; then DIR="$HOME/javis-os"
  elif [ -d /root/javis-os ]; then DIR=/root/javis-os
  else DIR="$HOME/javis-os"
  fi
fi

echo "=== HOST ==="
date -u
df -h / | head -2
free -h | head -2 || true
docker system df 2>/dev/null | head -8 || true
echo "manager_version $(docker exec javis-manager cat /app/VERSION 2>/dev/null || echo missing)"

echo "=== HOT-PATCH manager org_docker/org_coord/main nếu có trong bundle ==="
PATCHED=0
for f in server/org_docker.py server/org_coord.py server/main.py VERSION; do
  if [ -f "$DIR/$f" ]; then
    case "$f" in
      server/*) docker cp "$DIR/$f" "javis-manager:/app/$f" && PATCHED=1 ;;
      VERSION) docker cp "$DIR/$f" javis-manager:/app/VERSION 2>/dev/null || true ;;
    esac
  fi
done
if [ "$PATCHED" = 1 ]; then
  docker restart javis-manager
  for i in $(seq 1 40); do
    curl -fsS -m 3 http://127.0.0.1:7778/health >/dev/null 2>&1 && break
    sleep 2
  done
  sleep 3
fi

echo "=== DISABLE usercustomize hỏng trên mọi volume tenant ==="
for vol in /var/lib/docker/volumes/javis-*_javis-data/_data; do
  [ -d "$vol" ] || continue
  slug=$(basename "$(dirname "$vol")" | sed 's/^javis-//;s/_javis-data$//')
  uc="$vol/home/.local/lib/python3.12/site-packages/usercustomize.py"
  if [ -f "$uc" ]; then
    # Chỉ đổi tên nếu file trông như bản StarkHub (có _custom_import) - tránh xóa bản lành nếu có
    if grep -q '_custom_import\|_quota_watcher\|StarkHub' "$uc" 2>/dev/null; then
      mv -f "$uc" "$uc.bad.$(date +%s)"
      find "$vol/home/.local" -name 'usercustomize*.pyc' -delete 2>/dev/null || true
      echo "disabled_usercustomize $slug"
    else
      echo "keep_usercustomize $slug (not starkhub signature)"
    fi
  fi
done

echo "=== HOT-PATCH main.py (FileResponse) vào mọi máy đang chạy ==="
if [ -f "$DIR/server/main.py" ]; then
  for name in $(docker ps --format '{{.Names}}' | grep -E '^javis-' | grep -Ev 'javis-proxy|javis-park' || true); do
    docker cp "$DIR/server/main.py" "$name:/app/server/main.py" 2>/dev/null && echo "patched_main $name" || echo "patch_fail $name"
    docker cp "$DIR/VERSION" "$name:/app/VERSION" 2>/dev/null || true
  done
  # restart tenants (không restart manager lần nữa nếu vừa restart)
  for name in $(docker ps --format '{{.Names}}' | grep -E '^javis-' | grep -Ev 'javis-proxy|javis-park|javis-manager' || true); do
    docker restart "$name" >/dev/null && echo "restarted $name" || true
  done
  echo "wait health after mass restart..."
  sleep 25
fi

echo "=== AUDIT + HEAL từng người ==="
docker exec -i javis-manager python - <<'PY'
import sys, time, urllib.request, json
sys.path.insert(0, "/app/server")
import org_tenants as ot, org_coord as oc, org_docker as od

def http(cname, path, timeout=6):
    try:
        with urllib.request.urlopen(f"http://{cname}:7777{path}", timeout=timeout) as r:
            return r.status, len(r.read())
    except Exception as e:
        return None, str(e)[:120]

ts = [t for t in (ot.load().get("tenants") or []) if not t.get("protected") and not ot.is_soft_deleted(t)]
print("tenants", len(ts), flush=True)
c = oc.coord()
print("coord", {k: c.get(k) for k in ("max_running","effective_max","suggest","idle_minutes","host_ram_mb","host_avail_mb")}, flush=True)

rows = []
for t in ts:
    slug = str(t.get("slug") or "").strip()
    cname = str(t.get("container") or f"javis-{slug}")
    paused = bool(t.get("paused"))
    exists = bool(od.inspect_name(cname))
    st = od.container_status(cname) if exists else "missing"
    row = {"slug": slug, "docker": st, "paused": paused, "exists": exists}

    if not exists:
        try:
            if hasattr(od, "restore_tenant_container"):
                od.restore_tenant_container(slug, start_after=False)
                row["restored"] = True
                st = od.container_status(cname)
                row["docker"] = st
                exists = True
        except Exception as e:
            row["restore_err"] = f"{type(e).__name__}: {e}"
            rows.append(row)
            print("ROW", json.dumps(row, ensure_ascii=False), flush=True)
            continue

    if exists and st == "running":
        # vá main.py nếu bundle có (FileResponse)
        # (cp từ host đã làm ở script shell nếu cần - ở đây chỉ probe)
        try:
            row["serving"] = bool(od.container_serving_ready(cname))
        except Exception as e:
            row["serving"] = False
            row["serving_err"] = str(e)[:80]
        hs, _ = http(cname, "/health")
        cs, cn = http(cname, "/static/style.css")
        row["health_http"] = hs
        row["css_http"] = cs
        row["css_bytes"] = cn if isinstance(cn, int) else 0
        # model settings + agy
        try:
            out = od._exec(cname, ["python", "-c",
                "import json,os,sys\n"
                "from pathlib import Path\n"
                "sys.path.insert(0,'/app/server')\n"
                "sp=Path('/data/state/settings.json')\n"
                "s=json.loads(sp.read_text()) if sp.is_file() else {}\n"
                "m=s.get('model') or {}\n"
                "main=m.get('main') or {}\n"
                "print('MAIN', main.get('provider'), main.get('model'))\n"
                "print('OR_KEY', 'set' if str(m.get('openrouter_key') or '').strip() else 'empty')\n"
                "try:\n"
                " import antigravity_cli as ag\n"
                " print('AGY', ag.find_antigravity_cli() or 'MISSING')\n"
                " st=ag.auth_status(bo_qua_cache=True)\n"
                " print('AUTH', st.get('connected'), st.get('method') or '')\n"
                " ms=ag.list_models()\n"
                " print('MODELS', len(ms) if isinstance(ms,list) else 0)\n"
                "except Exception as e:\n"
                " print('AGY_ERR', type(e).__name__, e)\n"
            ], timeout=90.0)
            row["model_probe"] = " | ".join([ln.strip() for ln in (out or "").splitlines() if ln.strip()][-6:])
        except Exception as e:
            row["model_probe"] = f"ERR {type(e).__name__}: {e}"

        # env heal
        try:
            od.apply_public_hosts(slug)
            row["env_healed"] = True
        except Exception as e:
            row["env_heal_err"] = f"{type(e).__name__}: {e}"[:100]

        # nếu css lỗi mà máy running - thử hot-patch main từ manager's copy đã vá? skip if no host file
    elif exists and st != "running":
        row["note"] = "stopped/parked"

    rows.append(row)
    print("ROW", json.dumps(row, ensure_ascii=False), flush=True)

# summary
bad_css = [r["slug"] for r in rows if r.get("docker")=="running" and r.get("css_http") != 200]
bad_health = [r["slug"] for r in rows if r.get("docker")=="running" and r.get("health_http") != 200]
missing = [r["slug"] for r in rows if not r.get("exists")]
stopped = [r["slug"] for r in rows if r.get("docker") in ("stopped","missing") or r.get("note")]
running = [r["slug"] for r in rows if r.get("docker")=="running"]
print("SUMMARY running", len(running), running, flush=True)
print("SUMMARY stopped", len(stopped), stopped, flush=True)
print("SUMMARY missing", missing, flush=True)
print("SUMMARY bad_css", bad_css, flush=True)
print("SUMMARY bad_health", bad_health, flush=True)
print("AUDIT_DONE", flush=True)
PY

echo "=== docker ps -a javis ==="
docker ps -a --format 'table {{.Names}}\t{{.Status}}' | grep -E '^javis-|NAMES' | sort || true
echo ORG_AUDIT_DONE
