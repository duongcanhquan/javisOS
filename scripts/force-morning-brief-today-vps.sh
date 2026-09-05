#!/usr/bin/env bash
# Ép nhắc "Tổng kết sáng 8h" chạy SÁNG NAY (không để nhảy sang mai).
# - Nếu chưa tới 8:00 VN: đặt due = 8:00 hôm nay.
# - Nếu đã qua 8:00 VN: bắn trong ~1 phút (vẫn giữ cron mỗi ngày 8h cho các ngày sau).
set -euo pipefail

CONTAINER="${JAVIS_CONTAINER:-javis}"
PORT="${JAVIS_PORT:-7777}"
LABEL="${MORNING_BRIEF_LABEL:-Tổng kết sáng 8h}"
BRAIN="${MORNING_BRIEF_BRAIN:-brain}"

echo "==> container: $CONTAINER"
if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  echo "ERROR: container '$CONTAINER' không chạy."
  exit 1
fi

docker exec -u javis \
  -e "JAVIS_PORT=$PORT" \
  -e "MORNING_LABEL=$LABEL" \
  -e "MORNING_BRAIN=$BRAIN" \
  "$CONTAINER" python - <<'PY'
import json, os, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

port = os.environ.get("JAVIS_PORT", "7777")
base = f"http://127.0.0.1:{port}"
label = os.environ["MORNING_LABEL"]
brain = os.environ["MORNING_BRAIN"]
vn = ZoneInfo("Asia/Ho_Chi_Minh")
now = datetime.now(vn)
today_8 = now.replace(hour=8, minute=0, second=0, microsecond=0)


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
    raise SystemExit(
        f"ERROR: chưa có nhắc '{label}'. Chạy scripts/seed-morning-brief-vps.sh trước."
    )

rid = rem["id"]
print("found:", rid, "due_human=", rem.get("due_human"), "cron=", rem.get("cron"))

if now < today_8:
    # Còn trước 8h hôm nay → ép lại cron để due = 8:00 sáng nay
    upd = call("POST", "/reminders/update", {
        "id": rid,
        "brain": brain,
        "cron": "0 8 * * *",
        "chat_id": "all",
        "mode": "task",
    }, form=True)
    print("updated_cron:", json.dumps(upd, ensure_ascii=False))
    if not upd.get("ok"):
        raise SystemExit(1)
    due_h = (upd.get("reminder") or {}).get("due_human") or "?"
    print(f"OK: sẽ gửi LÚC 8:00 SÁNG NAY ({due_h}), không phải sáng mai.")
else:
    # Đã qua 8h → tạo bản một lần chạy ngay (~1 phút), giữ cron ngày mai
    text = rem.get("text") or ""
    one = call("POST", "/reminders", {
        "text": text,
        "label": f"{label} (chạy ngay sáng nay)",
        "mode": "task",
        "brain": brain,
        "muc_quyen": rem.get("muc_quyen") or "suggest",
        "chat_id": "all",
        "delay_min": 1,
        "created_by": "force-morning-brief-today",
        "allow_no_channel": True,
    })
    print("oneshot:", json.dumps(one, ensure_ascii=False))
    if not one.get("ok"):
        raise SystemExit(f"ERROR oneshot: {one}")
    # Bảo đảm lịch hàng ngày vẫn còn (cron về lần kế = ngày mai 8h)
    upd = call("POST", "/reminders/update", {
        "id": rid,
        "brain": brain,
        "cron": "0 8 * * *",
        "chat_id": "all",
    }, form=True)
    print("daily_refresh:", json.dumps(upd, ensure_ascii=False))
    print(f"OK: sẽ gửi trong ~1 phút (id={one.get('id')}). Từ ngày mai vẫn 8:00 mỗi sáng.")
PY
