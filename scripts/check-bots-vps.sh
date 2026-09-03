#!/usr/bin/env bash
# Kiểm tra bot Telegram + Zalo trên VPS (chạy trên host).
set -euo pipefail
CNAME="${JAVIS_NAME:-javis}"

echo "=== docker ==="
docker ps --format 'table {{.Names}}\t{{.Status}}' | head
echo
echo "=== health ==="
curl -fsS -m 8 http://127.0.0.1:7777/health || echo HEALTH_FAIL
echo
echo
echo "=== logs tg/zalo ==="
docker logs --tail 500 "$CNAME" 2>&1 | grep -iE 'telegram|zalo|bot |poll|webhook|whitelist|chat_id|unauthorized|conflict|409|429|Traceback|ERROR|Exception|ranh' | tail -200 || true
echo

cat > /tmp/javis_check_bots.py <<'PY'
import json, sys
sys.path.insert(0, "/app/server")
import config as cfgmod
st = cfgmod.read_settings()
tg = st.get("telegram") or {}
zl = st.get("zalo_bot") or {}
model = st.get("model") or {}
print("telegram:", json.dumps({
  "enabled": tg.get("enabled"),
  "has_token": bool(tg.get("token")),
  "chat_id": str(tg.get("chat_id") or "")[:200],
  "keys": sorted(tg.keys()),
  "error": str(tg.get("error") or tg.get("last_error") or "")[:300],
}, ensure_ascii=False))
print("zalo_bot:", json.dumps({
  "enabled": zl.get("enabled"),
  "has_token": bool(zl.get("token")),
  "chat_id": str(zl.get("chat_id") or "")[:200],
  "keys": sorted(zl.keys()),
  "error": str(zl.get("error") or zl.get("last_error") or "")[:300],
}, ensure_ascii=False))
print("main_model:", json.dumps(model.get("main"), ensure_ascii=False))

import main as m
for name in ("_TG_BOT", "_ZALO_BOT"):
    bot = getattr(m, name, None)
    if bot is None:
        print(name, "None")
        continue
    print(name, json.dumps({
        "status": getattr(bot, "status", None),
        "last_error": str(getattr(bot, "last_error", "") or "")[:300],
        "running": bool(getattr(bot, "running", None) or getattr(bot, "_task", None)),
        "task_done": (bot._task.done() if getattr(bot, "_task", None) else None),
        "whitelist": str(getattr(bot, "chat_ids", getattr(bot, "allowed", getattr(bot, "whitelist", ""))))[:200],
    }, ensure_ascii=False, default=str))

# Endpoint nội bộ
import urllib.request
for path in ("/telegram/status", "/zalo/status", "/zalo_bot/status"):
    try:
        with urllib.request.urlopen("http://127.0.0.1:7777"+path, timeout=10) as r:
            print(path, r.read().decode()[:500])
    except Exception as e:
        print(path, "ERR", type(e).__name__, e)

# API getMe kiểu nhẹ nếu có token
import urllib.request
tok = (tg.get("token") or "").strip()
if tok:
    try:
        with urllib.request.urlopen(f"https://api.telegram.org/bot{tok}/getMe", timeout=15) as r:
            print("telegram getMe:", r.read().decode()[:300])
        with urllib.request.urlopen(f"https://api.telegram.org/bot{tok}/getWebhookInfo", timeout=15) as r:
            print("telegram webhook:", r.read().decode()[:400])
    except Exception as e:
        print("telegram API ERR", type(e).__name__, e)

zt = (zl.get("token") or "").strip()
if zt:
    # Zalo official bot API vary; just show token length
    print("zalo token_len:", len(zt))
PY

docker cp /tmp/javis_check_bots.py "$CNAME:/tmp/javis_check_bots.py"
docker exec -u root "$CNAME" chmod 644 /tmp/javis_check_bots.py
echo "=== runtime ==="
docker exec -u root -w /app "$CNAME" python /tmp/javis_check_bots.py || true
docker exec -u root "$CNAME" rm -f /tmp/javis_check_bots.py || true
rm -f /tmp/javis_check_bots.py
echo DONE
