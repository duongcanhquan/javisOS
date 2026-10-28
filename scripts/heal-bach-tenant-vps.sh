#!/usr/bin/env bash
# Chẩn đoán + chữa tenant bach: UI trắng (FileResponse 500) và model.
set -euo pipefail

DIR="${JAVIS_DIR:-}"
if [ -z "$DIR" ]; then
  if [ -d "$HOME/javis-os" ]; then DIR="$HOME/javis-os"
  elif [ -d /root/javis-os ]; then DIR=/root/javis-os
  else DIR="$HOME/javis-os"
  fi
fi

C=javis-bach
echo "=== BEFORE ==="
date -u
df -h / | head -2
docker ps -a --filter name="^/${C}$" --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}' || \
  docker ps -a --filter name="$C" --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'
docker inspect "$C" --format 'State={{.State.Status}} Exit={{.State.ExitCode}} Health={{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' 2>/dev/null || echo NO_CONTAINER

# Đảm bảo usercustomize hỏng không còn (RecursionError trước đó)
DATA_VOL="/var/lib/docker/volumes/javis-bach_javis-data/_data"
UC="$DATA_VOL/home/.local/lib/python3.12/site-packages/usercustomize.py"
if [ -f "$UC" ]; then
  echo "disable usercustomize again"
  mv -f "$UC" "$UC.bad.$(date +%s)" || true
  find "$DATA_VOL/home/.local" -name 'usercustomize*.pyc' -delete 2>/dev/null || true
fi

echo "=== HOT-PATCH main.py (FileResponse → Response) + VERSION ==="
if [ -f "$DIR/server/main.py" ]; then
  docker cp "$DIR/server/main.py" "$C:/app/server/main.py"
  echo "patched main.py"
fi
if [ -f "$DIR/VERSION" ]; then
  docker cp "$DIR/VERSION" "$C:/app/VERSION" || true
fi
# Cũng vá manager nếu cần đồng bộ
if [ -f "$DIR/server/main.py" ]; then
  docker cp "$DIR/server/main.py" javis-manager:/app/server/main.py 2>/dev/null || true
fi

echo "=== RESTART bach ==="
docker restart "$C"
for i in $(seq 1 40); do
  ST=$(docker inspect "$C" --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}' 2>/dev/null || echo missing)
  echo "t=$i $ST"
  echo "$ST" | grep -q 'running healthy' && break
  echo "$ST" | grep -Eq 'restarting|exited' && docker logs --tail 8 "$C" 2>&1 | tail -8
  sleep 3
done

echo "=== VERSION / static / health inside bach ==="
docker exec "$C" sh -c 'cat /app/VERSION 2>/dev/null; rg -n "FileResponse 500|Thay StaticFiles|read_bytes" /app/server/main.py 2>/dev/null | head -5 || grep -n "Thay StaticFiles\|read_bytes" /app/server/main.py | head -5' || true

docker exec "$C" python - <<'PY'
import json, urllib.request
from pathlib import Path

def get(url):
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            body = r.read()
            return r.status, len(body), body[:80]
    except Exception as e:
        return None, 0, repr(e)

print("health", get("http://127.0.0.1:7777/health"), flush=True)
for path in ("/static/style.css", "/static/console.js", "/static/icons.js", "/"):
    st, n, head = get("http://127.0.0.1:7777" + path)
    print("GET", path, "status", st, "bytes", n, flush=True)

# Settings model
sp = Path("/data/state/settings.json")
if not sp.is_file():
    sp = Path("/data/settings.json")
print("settings_path", sp, "exists", sp.is_file(), flush=True)
if sp.is_file():
    try:
        s = json.loads(sp.read_text(encoding="utf-8"))
    except Exception as e:
        print("settings_json_err", e, flush=True)
        s = {}
    m = s.get("model") or {}
    main = m.get("main") or {}
    aux = m.get("auxiliary") or {}
    def scrub(block):
        if not isinstance(block, dict):
            return block
        out = {k: ("***" if "key" in k.lower() or "token" in k.lower() or "password" in k.lower() else v)
               for k, v in block.items()}
        return out
    print("model.main", scrub(main), flush=True)
    print("model.auxiliary", scrub(aux), flush=True)
    print("providers_present", sorted([k for k in m.keys() if "key" in k.lower() or k in ("main","auxiliary","telegram","ollama_local_endpoint")]), flush=True)
    # Claude/Codex login dirs
    for p in (Path("/home/javis/.claude"), Path("/home/javis/.codex"), Path("/data/home/.antigravity"), Path("/data/home/.local/bin")):
        print("path", p, "exists", p.exists(), "entries", len(list(p.iterdir())) if p.is_dir() else 0, flush=True)
PY

echo "=== manager → bach health + asset ==="
docker exec -i javis-manager python - <<'PY'
import sys, urllib.request
sys.path.insert(0, "/app/server")
import org_docker as od
cname = "javis-bach"
print("docker_status", od.container_status(cname), flush=True)
print("serving_ready", od.container_serving_ready(cname), flush=True)
for path in ("/health", "/static/style.css", "/"):
    try:
        with urllib.request.urlopen(f"http://{cname}:7777{path}", timeout=8) as r:
            print("via_mgr", path, r.status, "len", len(r.read()), flush=True)
    except Exception as e:
        print("via_mgr_err", path, type(e).__name__, e, flush=True)
PY

echo "=== recent bach logs ==="
docker logs --tail 40 "$C" 2>&1 | tail -40 || true
echo BACH_UI_MODEL_PROBE_DONE
