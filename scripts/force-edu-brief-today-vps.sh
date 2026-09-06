#!/usr/bin/env bash
# Ép "Báo cáo giáo dục CĐ-ĐH 8h" chạy NGAY trên VPS → Telegram (+ Zalo nếu chat_id=all).
# 1) Seed nhắc cron nếu chưa có.
# 2) One-shot delay ~1 phút với chat_id (mặc định all = Tele + Zalo).
# 3) Giữ cron 8h; đẩy due hàng ngày sang 8:00 ngày mai nếu cần.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONTAINER="${JAVIS_CONTAINER:-javis}"
PORT="${JAVIS_PORT:-7777}"
LABEL="${EDU_BRIEF_LABEL:-Báo cáo giáo dục CĐ-ĐH 8h}"
BRAIN="${EDU_BRIEF_BRAIN:-brain}"
# all = Telegram + Zalo; số telegram id = chỉ Telegram
CHAT_ID="${EDU_BRIEF_CHAT_ID:-all}"
MUC_QUYEN="${EDU_BRIEF_MUC_QUYEN:-suggest}"

echo "==> seed trước (idempotent)"
EDU_BRIEF_CHAT_ID="$CHAT_ID" EDU_BRIEF_MUC_QUYEN="$MUC_QUYEN" \
  EDU_BRIEF_ALLOW_NO_CHANNEL="${EDU_BRIEF_ALLOW_NO_CHANNEL:-true}" \
  bash "$ROOT/scripts/seed-edu-brief-vps.sh" || true

echo "==> container: $CONTAINER"
if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  CONTAINER=$(docker ps --format '{{.Names}}' | grep -E 'javis' | head -1 || true)
fi
if [ -z "${CONTAINER}" ]; then
  echo "ERROR: không thấy container javis."
  exit 1
fi

docker exec -i -u javis \
  -e "JAVIS_PORT=$PORT" \
  -e "EDU_LABEL=$LABEL" \
  -e "EDU_BRAIN=$BRAIN" \
  -e "EDU_CHAT=$CHAT_ID" \
  -e "EDU_MUC=$MUC_QUYEN" \
  "$CONTAINER" python - <<'PY'
import json, os, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

port = os.environ.get("JAVIS_PORT", "7777")
base = f"http://127.0.0.1:{port}"
label = os.environ["EDU_LABEL"]
brain = os.environ["EDU_BRAIN"]
chat_id = os.environ.get("EDU_CHAT", "all")
muc = os.environ.get("EDU_MUC", "suggest")
vn = ZoneInfo("Asia/Ho_Chi_Minh")
now = datetime.now(vn)
tomorrow_8 = (now + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)


def call(method, path, data=None, form=False):
    url = base + path
    if data is None:
        req = urllib.request.Request(url, method=method)
    elif form:
        body = urllib.parse.urlencode({k: str(v) for k, v in data.items()}).encode()
        req = urllib.request.Request(
            url, data=body, method=method,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    else:
        raw = json.dumps(data, ensure_ascii=False).encode()
        req = urllib.request.Request(
            url, data=raw, method=method,
            headers={"Content-Type": "application/json"},
        )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            return json.loads(body)
        except Exception:
            return {"ok": False, "error": f"HTTP {e.code}: {body[:400]}"}


listed = call("GET", f"/reminders?brain={urllib.parse.quote(brain)}")
pending = listed.get("pending") or []
rem = next((r for r in pending if (r.get("label") or "") == label), None)
print("now_vn:", now.isoformat())
print("pending_labels:", [r.get("label") for r in pending])

if not rem:
    raise SystemExit(f"ERROR: chưa có nhắc '{label}'. Seed thất bại?")

rid = rem["id"]
text = rem.get("text") or ""
print("found_daily:", rid, "due=", rem.get("due_human"), "cron=", rem.get("cron"), "chat=", rem.get("chat_id"))

one = call("POST", "/reminders", {
    "text": text,
    "label": f"{label} (chạy ngay)",
    "mode": "task",
    "brain": brain,
    "muc_quyen": rem.get("muc_quyen") or muc,
    "chat_id": chat_id,
    "delay_min": 1,
    "created_by": "force-edu-brief-today",
    "allow_no_channel": True,
})
print("oneshot:", json.dumps(one, ensure_ascii=False))
if not one.get("ok"):
    raise SystemExit(f"ERROR oneshot: {one}")

upd = call("POST", "/reminders/update", {
    "id": rid,
    "brain": brain,
    "cron": "0 8 * * *",
    "chat_id": chat_id,
    "mode": "task",
    "muc_quyen": rem.get("muc_quyen") or muc,
}, form=True)
print("daily_cron_refresh:", json.dumps(upd, ensure_ascii=False))

due_after = (upd.get("reminder") or {}).get("due_at") or 0
if due_after and due_after < tomorrow_8.timestamp():
    try:
        from pathlib import Path
        brains = os.environ.get("BRAINS_DIR", "/brains")
        root = Path(brains) / ("Brain Default" if brain in ("brain", "") else brain)
        path = root / "Javis" / "reminders.json"
        if not path.exists():
            for p in Path(brains).iterdir():
                cand = p / "Javis" / "reminders.json"
                if cand.exists():
                    data = json.loads(cand.read_text(encoding="utf-8"))
                    if any(r.get("id") == rid for r in data.get("reminders", [])):
                        path = cand
                        break
        data = json.loads(path.read_text(encoding="utf-8"))
        for r in data.get("reminders", []):
            if r.get("id") == rid and r.get("status") == "pending":
                r["due_at"] = tomorrow_8.timestamp()
                r["cron"] = "0 8 * * *"
                r["chat_id"] = chat_id
                print("patched_due_tomorrow_8:", datetime.fromtimestamp(r["due_at"], vn).isoformat())
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except Exception as e:
        print("WARN: không patch được due ngày mai:", type(e).__name__, e)

print(f"OK: bản chạy ngay sẽ gửi trong ~1 phút (id={one.get('id')}, due={one.get('due_human')}, chat_id={chat_id}).")
print("    Lịch 8h hàng ngày giữ nguyên; lần kế ~8:00 ngày mai.")
PY
