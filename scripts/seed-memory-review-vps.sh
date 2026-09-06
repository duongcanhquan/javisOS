#!/usr/bin/env bash
# Seed nhắc "Học nhớ tối" - nhắc ghi Memory đúng cách, chống quá tải.
# Idempotent theo label.
set -euo pipefail

CONTAINER="${JAVIS_CONTAINER:-javis}"
PORT="${JAVIS_PORT:-7777}"
LABEL="${MEMORY_REVIEW_LABEL:-Học nhớ tối}"
CRON="${MEMORY_REVIEW_CRON:-0 21 * * 1-6}"
BRAIN="${MEMORY_REVIEW_BRAIN:-brain}"
MUC_QUYEN="${MEMORY_REVIEW_MUC_QUYEN:-suggest}"
ALLOW_NO_CHANNEL="${MEMORY_REVIEW_ALLOW_NO_CHANNEL:-false}"
CHAT_ID="${MEMORY_REVIEW_CHAT_ID:-all}"

PROMPT=$(cat <<'EOF'
Nhiệm vụ: nhắc chủ + tự rà Memory (không viết ồ ạt).

1) Đọc memory/MEMORY.md (hoặc Memory/MEMORY.md). Đếm khoảng số dòng index.
2) Đọc học nhật ký hôm nay nếu có (trang Tự học / learn log trong brain nếu tìm được).
3) Trả tin NHẮN NGẮN (Telegram/Zalo), tiếng Việt:

### Học nhớ · <dd/mm>

**Cần ghi vào não hôm nay?** (chỉ fact BỀN)
- Liệt kê 0-5 ứng viên từ chat/ngày: loại user|preference|business|decision. Bỏ qua chuyện nhất thời.
- Nếu không có gì đáng nhớ: nói rõ "Hôm nay không cần ghi fact mới."

**Cách ghi đúng (nhắc chủ / Javis)**
- Fact: 1 file memory/facts/<slug>.md + 1 dòng MEMORY.md. Trùng nội dung → cập nhật/supersede, không nhân bản.
- Wiki: chỉ khái niệm/framework tái dùng (không nhét preference vào wiki).
- Không viết >5 fact/lần; không quét-nâng-cấp hàng loạt.

**Quá tải?**
- Nếu MEMORY.md trông dày (>120 dòng index): đề nghị Chủ nhật mở trang Tự học → bật Curator / gộp fact trùng tay.
- Nếu hôm nay chat dài mà chưa "Học ngay": nhắc bấm Học ngay trên trang Tự học (hoặc nói "học từ hội thoại").

Chỉ ĐỌC + đề xuất. Không tạo hàng loạt file trừ khi chủ đã bảo "ghi nhớ X" trong ngày và chưa có file. Kết quả đẩy về kênh đã cấu hình.
EOF
)

echo "==> container: $CONTAINER"
if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  echo "ERROR: container '$CONTAINER' không chạy."
  exit 1
fi

echo "==> seed nhắc: $LABEL (cron $CRON, muc=$MUC_QUYEN, brain=$BRAIN, chat=$CHAT_ID)"
docker exec -i -u javis \
  -e "JAVIS_PORT=$PORT" \
  -e "MR_LABEL=$LABEL" \
  -e "MR_CRON=$CRON" \
  -e "MR_BRAIN=$BRAIN" \
  -e "MR_MUC=$MUC_QUYEN" \
  -e "MR_ALLOW=$ALLOW_NO_CHANNEL" \
  -e "MR_CHAT=$CHAT_ID" \
  -e "MR_PROMPT=$PROMPT" \
  "$CONTAINER" python - <<'PY'
import json, os, urllib.error, urllib.parse, urllib.request

port = os.environ.get("JAVIS_PORT", "7777")
base = f"http://127.0.0.1:{port}"
label = os.environ["MR_LABEL"]
cron = os.environ["MR_CRON"]
brain = os.environ["MR_BRAIN"]
muc = os.environ["MR_MUC"]
chat = os.environ.get("MR_CHAT") or "all"
allow = (os.environ.get("MR_ALLOW") or "").lower() in ("1", "true", "yes")
prompt = os.environ["MR_PROMPT"]


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
        "id": rid, "brain": brain, "text": prompt, "label": label,
        "mode": "task", "cron": cron, "muc_quyen": muc, "chat_id": chat,
    }, form=True)
    print("updated:", json.dumps(upd, ensure_ascii=False))
    if not upd.get("ok"):
        raise SystemExit(1)
    print(f"OK: cap nhat '{label}' id={rid}")
else:
    payload = {
        "text": prompt, "label": label, "mode": "task", "cron": cron,
        "brain": brain, "muc_quyen": muc, "created_by": "seed-memory-review",
        "allow_no_channel": allow, "chat_id": chat,
    }
    created = call("POST", "/reminders", payload)
    print("created:", json.dumps(created, ensure_ascii=False))
    if created.get("ok"):
        print(f"OK: tao '{label}' id={created.get('id')} ke {created.get('due_human')}")
        if created.get("canh_bao"):
            print("CANH_BAO:", created["canh_bao"])
    elif created.get("can_force"):
        print("NEED_CHANNEL:", created.get("error"))
        raise SystemExit(2)
    else:
        print("ERROR:", created.get("error") or created)
        raise SystemExit(1)
PY

echo "==> XONG. Nhin viec dinh ky: $LABEL (21:00 T2-T7)."
