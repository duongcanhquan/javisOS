#!/usr/bin/env bash
# Seed nhắc hẹn "Tổng kết sáng 8h" trên VPS (container Javis).
# Idempotent: đã có cùng label thì cập nhật text/cron/muc_quyen, không tạo trùng.
set -euo pipefail

CONTAINER="${JAVIS_CONTAINER:-javis}"
PORT="${JAVIS_PORT:-7777}"
LABEL="${MORNING_BRIEF_LABEL:-Tổng kết sáng 8h}"
CRON="${MORNING_BRIEF_CRON:-0 8 * * *}"
BRAIN="${MORNING_BRIEF_BRAIN:-brain}"
# Chỉ đọc email/lịch rồi báo - không cần toàn quyền.
MUC_QUYEN="${MORNING_BRIEF_MUC_QUYEN:-suggest}"
ALLOW_NO_CHANNEL="${MORNING_BRIEF_ALLOW_NO_CHANNEL:-false}"

PROMPT=$(cat <<'EOF'
Làm đúng skill tong-ket-sang. Báo cáo tổng kết sáng (giờ VN):

1) Đọc email công việc NGÀY HÔM QUA (Gmail / Google Workspace). Tóm tắt thư đáng chú ý, ai gửi, cần phản hồi gì.
2) Việc CẦN LÀM và việc ĐÃ XỬ LÝ (từ email + lịch + Tasks/Kanban nếu có).
3) Lịch làm việc HÔM NAY (Google Calendar) - giờ + tên sự kiện.
4) Lịch NGÀY MAI để nhắc trước - cuộc họp/việc cần chuẩn bị từ hôm nay.

Chỉ ĐỌC, không gửi mail, không sửa/xoá sự kiện. Thiếu Gmail hoặc Lịch thì nói thẳng thiếu gì ở đúng mục, không bịa. Viết ngắn như tin nhắn Telegram, tiếng Việt, theo khuôn skill tong-ket-sang.
EOF
)

echo "==> container: $CONTAINER"
if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  echo "ERROR: container '$CONTAINER' không chạy. Bật Javis trước: docker compose up -d"
  exit 1
fi

echo "==> seed nhắc hẹn: $LABEL (cron $CRON, muc_quyen=$MUC_QUYEN, brain=$BRAIN)"
docker exec -u javis \
  -e "JAVIS_PORT=$PORT" \
  -e "MORNING_LABEL=$LABEL" \
  -e "MORNING_CRON=$CRON" \
  -e "MORNING_BRAIN=$BRAIN" \
  -e "MORNING_MUC=$MUC_QUYEN" \
  -e "MORNING_ALLOW=$ALLOW_NO_CHANNEL" \
  -e "MORNING_PROMPT=$PROMPT" \
  "$CONTAINER" python - <<'PY'
import json, os, urllib.error, urllib.parse, urllib.request

port = os.environ.get("JAVIS_PORT", "7777")
base = f"http://127.0.0.1:{port}"
label = os.environ["MORNING_LABEL"]
cron = os.environ["MORNING_CRON"]
brain = os.environ["MORNING_BRAIN"]
muc = os.environ["MORNING_MUC"]
allow = os.environ.get("MORNING_ALLOW", "false").lower() in ("1", "true", "yes")
prompt = os.environ["MORNING_PROMPT"]


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
notify = listed.get("notify") or {}
existing = next((r for r in pending if (r.get("label") or "") == label), None)

if existing:
    rid = existing["id"]
    upd = call("POST", "/reminders/update", {
        "id": rid,
        "brain": brain,
        "text": prompt,
        "label": label,
        "mode": "task",
        "cron": cron,
        "muc_quyen": muc,
    }, form=True)
    print("updated:", json.dumps(upd, ensure_ascii=False))
    if not upd.get("ok"):
        raise SystemExit(1)
    print(f"OK: da cap nhat nhac '{label}' id={rid}")
else:
    payload = {
        "text": prompt,
        "label": label,
        "mode": "task",
        "cron": cron,
        "brain": brain,
        "muc_quyen": muc,
        "created_by": "seed-morning-brief",
        "allow_no_channel": allow,
    }
    created = call("POST", "/reminders", payload)
    print("created:", json.dumps(created, ensure_ascii=False))
    if created.get("ok"):
        print(f"OK: da tao nhac '{label}' id={created.get('id')} "
              f"lan chay ke {created.get('due_human') or created.get('due_at')}")
        if created.get("canh_bao"):
            print("CANH_BAO:", created["canh_bao"])
    elif created.get("can_force"):
        print("NEED_CHANNEL:", created.get("error"))
        print("-> Dau Telegram (trang Kenh) roi chay lai script.")
        print("-> Hoac: MORNING_BRIEF_ALLOW_NO_CHANNEL=true bash scripts/seed-morning-brief-vps.sh")
        print("  (viec van chay nhung khong ai nhan bao cao).")
        raise SystemExit(2)
    else:
        print("ERROR:", created.get("error") or created)
        raise SystemExit(1)

print("notify:", json.dumps(notify, ensure_ascii=False))
print("muc_quyen:", muc, "(suggest = chi doc email/lich roi bao)")
PY

echo ""
echo "==> XONG seed Tong ket sang 8h."
echo "    Xem / sua / tat: trang Viec dinh ky tren dashboard."
echo "    Can da dau Gmail + Google Calendar (Ket noi) va Telegram (Kenh) de nhan bao cao."
