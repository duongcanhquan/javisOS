#!/usr/bin/env bash
# Seed nhắc "GitHub Trending 20h" trên VPS (container Javis).
# Idempotent: đã có cùng label thì cập nhật text/cron/muc_quyen, không tạo trùng.
set -euo pipefail

CONTAINER="${JAVIS_CONTAINER:-javis}"
PORT="${JAVIS_PORT:-7777}"
LABEL="${GH_TRENDING_LABEL:-GitHub Trending 20h}"
CRON="${GH_TRENDING_CRON:-0 20 * * *}"
BRAIN="${GH_TRENDING_BRAIN:-brain}"
MUC_QUYEN="${GH_TRENDING_MUC_QUYEN:-suggest}"
ALLOW_NO_CHANNEL="${GH_TRENDING_ALLOW_NO_CHANNEL:-false}"
CHAT_ID="${GH_TRENDING_CHAT_ID:-all}"

PROMPT=$(cat <<'EOF'
Làm đúng skill bao-cao-github-trending. Báo cáo GitHub Trending HÔM NAY (giờ VN):

1) Chạy fetch_trending.py --since daily --limit 15. Không bịa repo nếu fetch lỗi.
2) Đọc references/javis-fit.md. Mỗi repo: làm gì, dùng để làm gì, Với Javis (Không / Chỉ xem / Có thể bổ sung), dạng bổ sung (skill / connector-MCP / plugin / không).
3) Tin nhắn ngắn (Telegram/Zalo): 8–15 dòng, KHÔNG bảng Markdown. 3 dòng Đáng để mắt + Không đưa vào Javis.
4) Lưu bảng đủ vào exports/github-trending/YYYY-MM-DD.md.

Chỉ ĐỌC web + GHI file báo cáo. Không clone, không cài skill/plugin, không khuyên pentest / leak prompt / tải khóa học. Kết quả gửi cả Telegram và Zalo nếu đã đấu (chat_id=all).
EOF
)

echo "==> container: $CONTAINER"
if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  echo "ERROR: container '$CONTAINER' không chạy. Bật Javis trước: docker compose up -d"
  exit 1
fi

echo "==> seed nhắc hẹn: $LABEL (cron $CRON, muc_quyen=$MUC_QUYEN, brain=$BRAIN, chat=$CHAT_ID)"
docker exec -i -u javis \
  -e "JAVIS_PORT=$PORT" \
  -e "GH_LABEL=$LABEL" \
  -e "GH_CRON=$CRON" \
  -e "GH_BRAIN=$BRAIN" \
  -e "GH_MUC=$MUC_QUYEN" \
  -e "GH_ALLOW=$ALLOW_NO_CHANNEL" \
  -e "GH_CHAT=$CHAT_ID" \
  -e "GH_PROMPT=$PROMPT" \
  "$CONTAINER" python - <<'PY'
import json, os, urllib.error, urllib.parse, urllib.request

port = os.environ.get("JAVIS_PORT", "7777")
base = f"http://127.0.0.1:{port}"
label = os.environ["GH_LABEL"]
cron = os.environ["GH_CRON"]
brain = os.environ["GH_BRAIN"]
muc = os.environ["GH_MUC"]
chat = os.environ.get("GH_CHAT", "all")
allow = os.environ.get("GH_ALLOW", "false").lower() in ("1", "true", "yes")
prompt = os.environ["GH_PROMPT"]


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
        "chat_id": chat,
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
        "created_by": "seed-github-trending",
        "allow_no_channel": allow,
        "chat_id": chat,
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
        print("-> Dau Telegram va/hoac Zalo (trang Kenh) roi chay lai script.")
        print("-> Hoac: GH_TRENDING_ALLOW_NO_CHANNEL=true bash scripts/seed-github-trending-vps.sh")
        raise SystemExit(2)
    else:
        print("ERROR:", created.get("error") or created)
        raise SystemExit(1)

print("notify:", json.dumps(notify, ensure_ascii=False))
print("muc_quyen:", muc, "(suggest = chi doc web + ghi file bao cao)")
print("chat_id:", chat, "(all = Telegram + Zalo neu da dau)")
PY

echo ""
echo "==> XONG seed GitHub Trending 20h."
echo "    Xem / sua / tat: trang Viec dinh ky tren dashboard."
echo "    Can da dau Telegram va/hoac Zalo (trang Kenh)."
