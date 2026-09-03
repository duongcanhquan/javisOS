#!/usr/bin/env bash
set -euo pipefail
CNAME=javis
echo "=== flags ==="
docker exec -u root -w /app "$CNAME" python - <<'PY'
import json, sys
sys.path.insert(0, "/app/server")
import config as cfgmod
st = cfgmod.read_settings()
tg, zl = st.get("telegram") or {}, st.get("zalo_bot") or {}
print("telegram.enabled", tg.get("enabled"), "token", bool(tg.get("token")), "chat_id", tg.get("chat_id"))
print("zalo_bot.enabled", zl.get("enabled"), "token", bool(zl.get("token")), "chat_id", zl.get("chat_id"))
print("main", (st.get("model") or {}).get("main"))
try:
  import chatbot_store
  bots = chatbot_store.list_bots()
  print("chatbots_count", len(bots))
  for b in bots[:20]:
    print(" chatbot", b.get("id"), "enabled", b.get("enabled"), "channel", b.get("channel") or b.get("channels"), "name", b.get("name"))
except Exception as e:
  print("chatbots ERR", e)
PY
echo
echo "=== last 24h zalo/telegram log lines ==="
docker logs --since 24h "$CNAME" 2>&1 | grep -iE '\[zalo\]|\[telegram\]|\[chatbot' | tail -200 || true
echo
echo "=== errors/trace last 24h ==="
docker logs --since 24h "$CNAME" 2>&1 | grep -iE 'Traceback|ERROR|Exception|antigravity|agy |timeout|quota|Ineligible|failed to|conflict|409|whitelist|precheck|từ chối|bỏ qua' | tail -200 || true
echo
echo "=== count ==="
echo -n "zalo lines: "; docker logs --since 24h "$CNAME" 2>&1 | grep -c '\[zalo\]' || true
echo -n "telegram lines: "; docker logs --since 24h "$CNAME" 2>&1 | grep -c '\[telegram\]' || true
echo DONE
