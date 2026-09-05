#!/usr/bin/env bash
# Ép tổng kết sáng chạy SÁNG NAY trên VPS.
# 1) Bắn một bản one-shot trong ~1 phút (chat_id=zalo → chỉ Zalo).
# 2) Giữ nhắc cron 8h hàng ngày; lần kế đặt = ngày mai 8:00 (tránh gửi trùng 8h sáng nay).
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

docker exec -i -u javis \
  -e "JAVIS_PORT=$PORT" \
  -e "MORNING_LABEL=$LABEL" \
  -e "MORNING_BRAIN=$BRAIN" \
  "$CONTAINER" python - <<'PY'
import json, os, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

port = os.environ.get("JAVIS_PORT", "7777")
base = f"http://127.0.0.1:{port}"
label = os.environ["MORNING_LABEL"]
brain = os.environ["MORNING_BRAIN"]
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
    raise SystemExit(
        f"ERROR: chưa có nhắc '{label}'. Chạy scripts/seed-morning-brief-vps.sh trước."
    )

rid = rem["id"]
text = rem.get("text") or ""
print("found_daily:", rid, "due=", rem.get("due_human"), "cron=", rem.get("cron"))

# 1) One-shot gửi trong ~1 phút (sáng nay ngay)
one = call("POST", "/reminders", {
    "text": text,
    "label": f"{label} (chạy ngay sáng nay)",
    "mode": "task",
    "brain": brain,
    "muc_quyen": rem.get("muc_quyen") or "suggest",
    "chat_id": "zalo",
    "delay_min": 1,
    "created_by": "force-morning-brief-today",
    "allow_no_channel": True,
})
print("oneshot:", json.dumps(one, ensure_ascii=False))
if not one.get("ok"):
    # Thử lại với allow nếu thiếu kênh đã báo can_force
    if one.get("can_force"):
        one = call("POST", "/reminders", {
            "text": text,
            "label": f"{label} (chạy ngay sáng nay)",
            "mode": "task",
            "brain": brain,
            "muc_quyen": rem.get("muc_quyen") or "suggest",
            "chat_id": "zalo",
            "delay_min": 1,
            "created_by": "force-morning-brief-today",
            "allow_no_channel": True,
        })
        print("oneshot_retry:", json.dumps(one, ensure_ascii=False))
    if not one.get("ok"):
        raise SystemExit(f"ERROR oneshot: {one}")

# 2) Nhắc cron hàng ngày: giữ cron, đẩy due sang 8:00 ngày mai (tránh trùng với one-shot)
upd = call("POST", "/reminders/update", {
    "id": rid,
    "brain": brain,
    "cron": "0 8 * * *",
    "chat_id": "zalo",
    "mode": "task",
}, form=True)
print("daily_cron_refresh:", json.dumps(upd, ensure_ascii=False))

# Nếu cron_next vẫn ra hôm nay 8h (vì chưa tới 8h), ghi đè due_at = ngày mai 8:00 qua due_at
# (update với due_at sẽ XOÁ cron - nên ghi thẳng file trong brain).
due_after = (upd.get("reminder") or {}).get("due_at") or 0
if due_after and due_after < tomorrow_8.timestamp():
    import sys
    sys.path.insert(0, "/app/server")
    # Ghi đè due trong kho nhắc, GIỮ cron
    try:
        from pathlib import Path
        brains = os.environ.get("BRAINS_DIR", "/brains")
        # brain id "brain" → Brain Default
        root = Path(brains) / ("Brain Default" if brain in ("brain", "") else brain)
        path = root / "Javis" / "reminders.json"
        if not path.exists():
            # thử tên đúng như label brain
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
                r["chat_id"] = "zalo"
                print("patched_due_tomorrow_8:", datetime.fromtimestamp(r["due_at"], vn).isoformat())
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except Exception as e:
        print("WARN: không patch được due ngày mai:", type(e).__name__, e)

print(f"OK: bản sáng nay sẽ gửi trong ~1 phút (id={one.get('id')}, due={one.get('due_human')}).")
print("    Lịch 8h hàng ngày giữ nguyên; lần kế = 8:00 ngày mai.")
PY
