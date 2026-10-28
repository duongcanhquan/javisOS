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

# Bắt buộc -i (không thì Python nhận EOF, không in settings)
docker exec -i "$C" python - <<'PY'
import json, urllib.request, os, subprocess
from pathlib import Path

def get(url):
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            body = r.read()
            return r.status, len(body), body[:80]
    except Exception as e:
        return None, 0, repr(e)

print("health", get("http://127.0.0.1:7777/health"), flush=True)
for path in ("/static/style.css", "/static/console.js", "/static/icons.js", "/static/login.css", "/"):
    st, n, _ = get("http://127.0.0.1:7777" + path)
    print("GET", path, "status", st, "bytes", n, flush=True)

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
    m = s.get("model") if isinstance(s.get("model"), dict) else {}
    def scrub(block):
        if not isinstance(block, dict):
            return block
        out = {}
        for k, v in block.items():
            lk = k.lower()
            if any(x in lk for x in ("key", "token", "password", "secret")):
                out[k] = ("set" if str(v or "").strip() else "empty")
            else:
                out[k] = v
        return out
    print("model.main", scrub(m.get("main") or {}), flush=True)
    print("model.auxiliary", scrub(m.get("auxiliary") or {}), flush=True)
    print("model.telegram", scrub(m.get("telegram") or {}), flush=True)
    for k in sorted(m.keys()):
        if "key" in k.lower() or k.endswith("_endpoint"):
            val = m.get(k)
            print("model_field", k, ("set" if str(val or "").strip() else "empty"), flush=True)
    # CLI engines
    for p in (
        Path("/home/javis/.claude"),
        Path("/home/javis/.codex"),
        Path("/data/home/.antigravity"),
        Path("/data/home/.local/bin"),
        Path("/data/home/.config"),
    ):
        n = len(list(p.iterdir())) if p.is_dir() else 0
        print("path", p, "exists", p.exists(), "entries", n, flush=True)
    for bin_name in ("claude", "codex", "agy", "grok"):
        try:
            r = subprocess.run(["sh", "-c", f"command -v {bin_name} || true"], capture_output=True, text=True, timeout=5)
            print("bin", bin_name, (r.stdout or "").strip() or "MISSING", flush=True)
        except Exception as e:
            print("bin", bin_name, "err", e, flush=True)
PY

echo "=== INSTALL agy/grok nếu thiếu (model đang gắn antigravity-cli) ==="
docker exec -u javis "$C" sh -c '
set +e
mkdir -p /data/home/.local/bin /data/home/.cli-auto-install /data/home/.antigravity
# đảm bảo symlink ~/.local
if [ ! -L /home/javis/.local ]; then
  mkdir -p /data/home/.local
  ln -sfn /data/home/.local /home/javis/.local 2>/dev/null || true
fi
export PATH="/data/home/.local/bin:/home/javis/.local/bin:$PATH"
if ! command -v agy >/dev/null 2>&1 && [ ! -x /home/javis/.local/bin/agy ]; then
  echo "installing agy..."
  curl -fsSL https://antigravity.google/cli/install.sh | bash 2>&1 | tail -30
fi
if ! command -v grok >/dev/null 2>&1 && [ ! -x /home/javis/.local/bin/grok ]; then
  echo "installing grok..."
  curl -fsSL https://x.ai/cli/install.sh | bash 2>&1 | tail -20 || true
fi
command -v agy || ls -la /home/javis/.local/bin/agy /data/home/.local/bin/agy 2>/dev/null || echo AGY_STILL_MISSING
command -v grok || ls -la /home/javis/.local/bin/grok 2>/dev/null || echo GROK_MISSING_OK
ls -la /data/home/.cli-auto-install/ 2>/dev/null | head -20
tail -30 /data/home/.cli-auto-install/install.log 2>/dev/null || true
' || echo "install_step_err"

# Nếu vẫn thiếu agy nhưng có openrouter_key: gợi ý chuyển MAIN tạm (không tự đổi trừ khi user muốn)
docker exec -i "$C" python - <<'PY'
import json
from pathlib import Path
sp = Path("/data/state/settings.json")
s = json.loads(sp.read_text(encoding="utf-8")) if sp.is_file() else {}
m = s.get("model") if isinstance(s.get("model"), dict) else {}
main = m.get("main") if isinstance(m.get("main"), dict) else {}
or_key = bool(str(m.get("openrouter_key") or "").strip())
print("main_provider", main.get("provider"), "main_model", main.get("model"), flush=True)
print("openrouter_key", "set" if or_key else "empty", flush=True)
print("antigravity_dir_entries", len(list(Path("/data/home/.antigravity").iterdir())) if Path("/data/home/.antigravity").is_dir() else 0, flush=True)
# agy login state
for p in Path("/data/home").rglob("*"):
    if p.is_file() and ("antigravity" in str(p).lower() or "agy" in p.name.lower()) and p.stat().st_size < 200000:
        if any(x in p.name.lower() for x in ("auth", "token", "cred", "session", "config")):
            print("agy_related_file", p, "bytes", p.stat().st_size, flush=True)
print("MODEL_DIAG_DONE", flush=True)
PY

echo "=== VERIFY agy binary + auth trong process Javis ==="
docker exec -u javis "$C" sh -c '
export PATH="/home/javis/.local/bin:/data/home/.local/bin:$PATH"
ls -la /home/javis/.local/bin/agy /data/home/.local/bin/agy 2>/dev/null
file /home/javis/.local/bin/agy /data/home/.local/bin/agy 2>/dev/null
agy --version 2>&1 | head -5 || /home/javis/.local/bin/agy --version 2>&1 | head -5 || echo AGY_VERSION_FAIL
'
docker exec -i "$C" python - <<'PY'
import sys
sys.path.insert(0, "/app/server")
import antigravity_cli as ag
print("find_agy", ag.find_antigravity_cli(), flush=True)
try:
    st = ag.auth_status_nen()
    print("auth_status_nen", {k: st.get(k) for k in ("connected", "email", "error", "reason") if k in st or True}, flush=True)
    print("auth_raw_keys", sorted(st.keys()), flush=True)
    for k in ("connected", "email", "account", "error", "message", "detail"):
        if k in st:
            print("auth", k, st.get(k), flush=True)
except Exception as e:
    print("auth_err", type(e).__name__, e, flush=True)
try:
    ms = ag.list_models()
    print("models_count", len(ms) if isinstance(ms, list) else type(ms), flush=True)
    if isinstance(ms, list):
        print("models_sample", [str(x)[:80] for x in ms[:8]], flush=True)
except Exception as e:
    print("models_err", type(e).__name__, e, flush=True)
print("AGY_AUTH_DONE", flush=True)
try:
    st2 = ag.auth_status(bo_qua_cache=True)
    print("auth_forced", st2, flush=True)
except Exception as e:
    print("auth_forced_err", e, flush=True)
PY

echo "=== HEAL env FORCE_FILE trên bach (agy lưu token ra file) ==="
docker exec -i javis-manager python - <<'PY'
import sys
sys.path.insert(0, "/app/server")
import org_docker as od
try:
    od.apply_public_hosts("bach")
    print("apply_public_hosts ok", flush=True)
except Exception as e:
    print("apply_public_hosts", type(e).__name__, e, flush=True)
data = od.inspect_name("javis-bach") or {}
env = (data.get("Config") or {}).get("Env") or []
print("FORCE_FILE", any(str(e).startswith("GEMINI_FORCE_FILE_STORAGE=") for e in env), flush=True)
print("TERMINAL_REMOTE", any(str(e).startswith("JAVIS_TERMINAL_REMOTE=") for e in env), flush=True)
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
