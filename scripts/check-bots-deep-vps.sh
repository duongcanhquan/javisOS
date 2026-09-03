#!/usr/bin/env bash
set -euo pipefail
CNAME=javis
# chờ health ổn
for i in 1 2 3 4 5 6 7 8 9 10 11 12; do
  if curl -fsS -m 4 http://127.0.0.1:7777/health >/dev/null 2>&1; then break; fi
  sleep 5
done
echo "=== flags ==="
docker exec -u root -w /app "$CNAME" python - <<'PY'
import json, sys, os
sys.path.insert(0, "/app/server")
import config as cfgmod
st = cfgmod.read_settings()
tg, zl = st.get("telegram") or {}, st.get("zalo_bot") or {}
print("telegram.enabled=", tg.get("enabled"), "token=", bool(tg.get("token")), "chat_id=", repr(tg.get("chat_id")))
print("zalo_bot.enabled=", zl.get("enabled"), "token=", bool(zl.get("token")), "chat_id=", repr(zl.get("chat_id")))
print("main=", (st.get("model") or {}).get("main"))
# settings path
print("settings_path=", getattr(cfgmod, "SETTINGS_PATH", None) or getattr(cfgmod, "settings_path", None))
for p in ("/data/settings.json", "/data/javis-settings.json", "/data/config/settings.json"):
  if os.path.exists(p):
    print("exists", p, "size", os.path.getsize(p))
try:
  import chatbot_store
  bots = chatbot_store.list_bots()
  print("chatbots=", len(bots))
  for b in bots[:30]:
    print(" ", b.get("id"), "en=", b.get("enabled"), "ch=", b.get("channel") or b.get("channels"), "name=", b.get("name"))
except Exception as e:
  print("chatbots ERR", e)
# parse zalo whitelist
from telegram_bot import parse_chat_ids
print("zalo whitelist parsed=", parse_chat_ids(zl.get("chat_id")))
PY
echo
echo "=== zalo/telegram log 48h ==="
docker logs --since 48h "$CNAME" 2>&1 | grep -iE '\[zalo\]|\[telegram\]|\[chatbot' | tail -120 || true
echo
echo "=== engine/errors 12h ==="
docker logs --since 12h "$CNAME" 2>&1 | grep -iE 'Traceback|\[zalo\].*err|\[telegram\].*err|antigravity|agy |timeout|quota|conflict|409|failed|Exception' | grep -vi 'remotion-icon|UnicodeDecode' | tail -120 || true
echo
echo "=== counts 48h ==="
echo -n "zalo: "; docker logs --since 48h "$CNAME" 2>&1 | grep -c '\[zalo\]' || true
echo -n "telegram: "; docker logs --since 48h "$CNAME" 2>&1 | grep -c '\[telegram\]' || true
echo DONE_DEEP
