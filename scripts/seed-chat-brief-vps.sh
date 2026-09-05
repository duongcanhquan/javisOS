#!/usr/bin/env bash
# Seed nhắc hẹn "Tổng kết Chat 18h" trên VPS (container Javis).
# Idempotent: đã có cùng label thì cập nhật text/cron/muc_quyen, không tạo trùng.
set -euo pipefail

CONTAINER="${JAVIS_CONTAINER:-javis}"
PORT="${JAVIS_PORT:-7777}"
LABEL="${CHAT_BRIEF_LABEL:-Tổng kết Chat 18h}"
CRON="${CHAT_BRIEF_CRON:-0 18 * * *}"
BRAIN="${CHAT_BRIEF_BRAIN:-brain}"
MUC_QUYEN="${CHAT_BRIEF_MUC_QUYEN:-suggest}"
ALLOW_NO_CHANNEL="${CHAT_BRIEF_ALLOW_NO_CHANNEL:-false}"

PROMPT=$(cat <<'EOF'
Làm đúng skill tong-ket-chat-ngay. Báo cáo Google Chat HÔM NAY (giờ VN):

1) Tóm tắt các space/DM đáng chú ý: hôm nay trao đổi chủ yếu về gì.
2) Ai NHẮC TỚI chủ (mention, reply, giao việc trực tiếp) - ghi rõ người, space, nội dung ngắn.
3) Việc CẦN PHẢN HỒI hoặc theo dõi từ Chat.

Chỉ ĐỌC qua Google Chat MCP, không gửi tin. Thiếu kết nối Google Chat thì nói thẳng ở đầu báo cáo, không bịa. Viết ngắn như tin nhắn Zalo, tiếng Việt, theo khuôn skill tong-ket-chat-ngay.
EOF
)

echo "==> container: $CONTAINER"
if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  echo "ERROR: container '$CONTAINER' không chạy. Bật Javis trước: docker compose up -d"
  exit 1
fi

echo "==> seed nhắc hẹn: $LABEL (cron $CRON, muc_quyen=$MUC_QUYEN, brain=$BRAIN)"
docker exec -i -u javis \
  -e "JAVIS_PORT=$PORT" \
  -e "CHAT_LABEL=$LABEL" \
  -e "CHAT_CRON=$CRON" \
  -e "CHAT_BRAIN=$BRAIN" \
  -e "CHAT_MUC=$MUC_QUYEN" \
  -e "CHAT_ALLOW=$ALLOW_NO_CHANNEL" \
  -e "CHAT_PROMPT=$PROMPT" \
  "$CONTAINER" python - <<'PY'
import json, os, urllib.error, urllib.parse, urllib.request

port = os.environ.get("JAVIS_PORT", "7777")
base = f"http://127.0.0.1:{port}"
label = os.environ["CHAT_LABEL"]
cron = os.environ["CHAT_CRON"]
brain = os.environ["CHAT_BRAIN"]
muc = os.environ["CHAT_MUC"]
allow = os.environ.get("CHAT_ALLOW", "false").lower() in ("1", "true", "yes")
prompt = os.environ["CHAT_PROMPT"]


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
        "chat_id": "zalo",
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
        "muc_quyen": muc,
        "chat_id": "zalo",
        "brain": brain,
    }
    if allow:
        payload["allow_no_channel"] = "true"
    created = call("POST", "/reminders", payload, form=True)
    print("created:", json.dumps(created, ensure_ascii=False))
    if not created.get("ok"):
        if created.get("can_force"):
            payload["allow_no_channel"] = "true"
            created = call("POST", "/reminders", payload, form=True)
            print("retry:", json.dumps(created, ensure_ascii=False))
        if not created.get("ok"):
            raise SystemExit(1)
    print(f"OK: da tao nhac '{label}'")
PY

echo "    Can da dau Google Chat (Ket noi -> Google -> Google Chat, tai khoan Workspace)."
echo "    Thu trong chat: 'tong ket chat hom nay' hoac doi nhac 18h."
