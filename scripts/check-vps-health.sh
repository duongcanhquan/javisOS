#!/usr/bin/env bash
# Kiểm tra sức khoẻ Javis trên VPS (chạy trên host, gọi vào container).
set -euo pipefail

CNAME="${JAVIS_NAME:-javis}"
if ! docker ps --format '{{.Names}}' | grep -qx "$CNAME"; then
  CNAME=$(docker ps --format '{{.Names}}' | grep -E 'javis' | head -1 || true)
fi

echo "=== HOST ==="
hostname
date -Is
echo
echo "=== DOCKER ==="
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}' || true
echo "container=$CNAME"
echo
echo "=== /health ==="
ok_health=0
for i in 1 2 3 4 5 6 7 8 9 10; do
  if curl -fsS -m 5 http://127.0.0.1:7777/health >/tmp/javis-health.json 2>/dev/null; then
    cat /tmp/javis-health.json; echo
    ok_health=1
    break
  fi
  echo "waiting health... ($i)"
  sleep 3
done
if [ "$ok_health" != "1" ]; then
  echo "HEALTH_FAIL"
fi
echo

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [ -d "$ROOT/.git" ]; then
  echo "=== VERSION ==="
  echo "dir=$ROOT"
  git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || true
  git -C "$ROOT" log -1 --oneline 2>/dev/null || true
  grep -E '^(GEMINI_FORCE_FILE_STORAGE|JAVIS_ENABLE_USER_PLUGINS)=' "$ROOT/.env" 2>/dev/null || true
  echo
fi

if [ -z "$CNAME" ]; then
  echo "ERROR: không thấy container javis"
  exit 1
fi

echo "=== ANTIGRAVITY ==="
docker exec -u javis "$CNAME" bash -lc '
  export PATH="$HOME/.local/bin:$PATH"
  command -v agy || { echo "agy missing"; exit 0; }
  echo "GEMINI_FORCE_FILE_STORAGE=${GEMINI_FORCE_FILE_STORAGE:-unset}"
  ls -ld ~/.gemini ~/.antigravity 2>/dev/null || true
  agy models 2>&1 | head -20
' || echo "AGY_CHECK_FAIL"
echo

echo "=== CONNECT / PROVIDERS / MCP (trong container, bypass login) ==="
TMP_PY="$(mktemp /tmp/javis-check-XXXXXX.py)"
cat > "$TMP_PY" <<'PY'
import json, os, sys
sys.path.insert(0, "/app/server")
os.chdir("/app")

# 1) Health snapshot kết nối MCP
try:
    import connect_health
    snap = connect_health.snapshot()
    engines = getattr(connect_health, "_engines", {})
    if not snap:
        print("== connect_health.snapshot: (empty - chưa quét hoặc chưa có kết nối bật)")
    else:
        print("== connect_health.snapshot")
        for cid, rec in snap.items():
            print(f"  {cid}: ok={rec.get('ok')} tools={rec.get('tools')} kind={rec.get('kind')} {rec.get('message') or ''}")
    print("== engines")
    if not engines:
        print("  (empty)")
    else:
        for name, rec in engines.items():
            print(f"  {name}: ok={rec.get('ok')} {rec.get('message') or ''} src={rec.get('source')}")
    print()
except Exception as e:
    print("connect_health ERR", type(e).__name__, e)

# 2) Danh sách MCP đã cấu hình
try:
    import mcp_store
    rows = mcp_store.resolved(enabled_only=False)
    print(f"== mcp_store ({len(rows)} connections)")
    for c in rows:
        print(f"  id={c.get('id')} enabled={c.get('enabled')} label={c.get('label') or c.get('name')} transport={c.get('transport')}")
    print()
except Exception as e:
    print("mcp_store ERR", type(e).__name__, e)

# 3) Provider / models (nội bộ)
try:
    import config as cfgmod
    import main as m
    cfg = cfgmod.read_settings()
    if hasattr(m, "_providers_view"):
        rows = m._providers_view(cfg)
        print(f"== providers ({len(rows) if isinstance(rows, list) else '?'})")
        for p in (rows if isinstance(rows, list) else []):
            if not isinstance(p, dict):
                continue
            print(
                f"  {p.get('id')}: connected={p.get('connected')} cli={p.get('cli_found')} "
                f"models={len(p.get('models') or [])} "
                f"{(p.get('auth_error') or p.get('error') or '')[:100]}"
            )
        print()
    else:
        st = cfg.get("model") or {}
        print("== model settings (fallback)")
        print(json.dumps({
            "main": st.get("main"),
            "has_openrouter": bool(st.get("openrouter_key")),
            "has_anthropic": bool(st.get("anthropic_api_key")),
            "has_openai": bool(st.get("openai_api_key")),
            "has_gemini": bool(st.get("gemini_api_key")),
            "has_deepseek": bool(st.get("deepseek_api_key") or st.get("deepseek_key")),
            "has_groq": bool(st.get("groq_api_key")),
        }, ensure_ascii=False))
        print()
except Exception as e:
    print("providers ERR", type(e).__name__, e)

# 4) Antigravity + Claude auth status modules
try:
    import antigravity_cli
    print("== antigravity_cli.auth_status")
    print(json.dumps(antigravity_cli.auth_status(bo_qua_cache=True), ensure_ascii=False))
    print()
except Exception as e:
    print("antigravity auth ERR", type(e).__name__, e)

try:
    import claude_cli
    if hasattr(claude_cli, "auth_status"):
        print("== claude_cli.auth_status")
        print(json.dumps(claude_cli.auth_status(), ensure_ascii=False, default=str)[:800])
        print()
except Exception as e:
    print("claude auth ERR", type(e).__name__, e)

# 5) Ép quét health các kết nối đang bật (có thể mất vài chục giây)
try:
    import asyncio, connect_health
    print("== sweeping enabled connections now...")
    n = asyncio.run(connect_health.sweep())
    print(f"checked={n}")
    for cid, rec in connect_health.snapshot().items():
        mark = "OK" if rec.get("ok") else "FAIL"
        print(f"  [{mark}] {cid}: tools={rec.get('tools')} kind={rec.get('kind')} {rec.get('message') or ''}")
except Exception as e:
    print("sweep ERR", type(e).__name__, e)
PY
docker cp "$TMP_PY" "$CNAME:/tmp/javis-check.py"
docker exec "$CNAME" python /tmp/javis-check.py || echo "CONNECT_API_FAIL"
rm -f "$TMP_PY"
docker exec "$CNAME" rm -f /tmp/javis-check.py 2>/dev/null || true

echo
echo "=== DONE ==="
