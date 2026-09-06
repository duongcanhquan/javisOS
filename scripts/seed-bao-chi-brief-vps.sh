#!/usr/bin/env bash
# Seed nhắc hẹn "Tổng hợp báo chí 8h" trên VPS (container Javis).
# Idempotent: cùng label thì cập nhật text/cron, không tạo trùng.
set -euo pipefail

CONTAINER="${JAVIS_CONTAINER:-javis}"
PORT="${JAVIS_PORT:-7777}"
LABEL="${BAO_CHI_BRIEF_LABEL:-Tổng hợp báo chí 8h}"
CRON="${BAO_CHI_BRIEF_CRON:-0 8 * * *}"
BRAIN="${BAO_CHI_BRIEF_BRAIN:-brain}"
# Chỉ đọc RSS + tóm tắt; kết quả do hệ thống nhắc đẩy về kênh.
MUC_QUYEN="${BAO_CHI_BRIEF_MUC_QUYEN:-suggest}"
ALLOW_NO_CHANNEL="${BAO_CHI_BRIEF_ALLOW_NO_CHANNEL:-false}"
# all = Telegram + Zalo (nếu đã đấu); zalo / telegram = một kênh.
CHAT_ID="${BAO_CHI_BRIEF_CHAT_ID:-all}"

PROMPT=$(cat <<'EOF'
Làm đúng skill tong-hop-bao-chi (và agent tong-hop-bao-chi nếu cần).

1) Đọc Javis/bao-chi-cau-hinh.md (RSS + chủ đề mặc định + từ khóa). Thiếu file thì tạo từ mẫu skill references/cau-hinh-mau.md rồi ghi chú để chủ sửa nguồn.
2) Cửa sổ giờ VN: 00:00 HÔM QUA → 08:00 HÔM NAY.
3) Chủ đề: dùng chủ đề mặc định trong cấu hình (giáo dục cao đẳng - đại học nếu chưa đổi).
4) Chạy scripts/fetch_rss.py với --config Javis/bao-chi-cau-hinh.md --limit 10 (hoặc WebFetch RSS nếu không có Bash).
5) Viết báo cáo theo khuôn skill: tóm tắt theo chủ đề + tối đa 10 bài mới nhất, MỖI bài có link markdown gốc. Không bịa bài/link.

Chỉ ĐỌC RSS và tóm tắt. Không gửi tin tay sang người khác - kết quả brief sẽ được hệ thống đẩy về kênh đã cấu hình. Tiếng Việt, ngắn như tin nhắn.
EOF
)

echo "==> container: $CONTAINER"
if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  echo "ERROR: container '$CONTAINER' không chạy. Bật Javis trước: docker compose up -d"
  exit 1
fi

# Đảm bảo mỗi brain có file cấu hình (không ghi đè nếu đã có).
echo "==> đảm bảo Javis/bao-chi-cau-hinh.md trong các brain"
docker exec -i -u javis "$CONTAINER" python - <<'PY'
from pathlib import Path
import os

brains_root = Path(os.environ.get("BRAINS_DIR", "/brains"))
sample = """---
type: note
title: Cấu hình tổng hợp báo chí
updated: 2026-09-06
---

# Cấu hình tổng hợp báo chí

Skill `tong-hop-bao-chi` đọc file này mỗi lần chạy brief sáng hoặc khi bạn gọi tay.

## Nguồn RSS

- https://vnexpress.net/rss/giao-duc.rss
- https://tuoitre.vn/rss/giao-duc.rss
- https://thanhnien.vn/rss/giao-duc.rss
- https://vietnamnet.vn/rss/giao-duc.rss

## Chủ đề mặc định

Giáo dục cao đẳng - đại học

## Từ khóa

đại học, cao đẳng, tuyển sinh, sinh viên, giảng viên, học phí, ĐH, CĐ, Bộ GDĐT, Bộ Giáo dục, university, college, đào tạo

## Ghi chú

- Thêm `- https://...` để bổ sung báo.
- Đổi chủ đề / từ khóa cho brief 8h sáng.
- Gọi tay: «tổng hợp báo chí chủ đề bất động sản» (không cần sửa file).
"""
written = 0
if not brains_root.is_dir():
    print(f"WARN: khong thay brains_root={brains_root}")
else:
    for brain in sorted(brains_root.iterdir()):
        if not brain.is_dir() or brain.name.startswith("."):
            continue
        dest = brain / "Javis" / "bao-chi-cau-hinh.md"
        if dest.exists():
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(sample, encoding="utf-8")
        written += 1
        print(f"wrote {dest}")
    print(f"ok: brains_root={brains_root} newly_written={written}")
PY

echo "==> seed nhắc: $LABEL (cron $CRON, muc=$MUC_QUYEN, brain=$BRAIN, chat=$CHAT_ID)"
docker exec -i -u javis \
  -e "JAVIS_PORT=$PORT" \
  -e "BC_LABEL=$LABEL" \
  -e "BC_CRON=$CRON" \
  -e "BC_BRAIN=$BRAIN" \
  -e "BC_MUC=$MUC_QUYEN" \
  -e "BC_ALLOW=$ALLOW_NO_CHANNEL" \
  -e "BC_CHAT=$CHAT_ID" \
  -e "BC_PROMPT=$PROMPT" \
  "$CONTAINER" python - <<'PY'
import json, os, urllib.error, urllib.parse, urllib.request

port = os.environ.get("JAVIS_PORT", "7777")
base = f"http://127.0.0.1:{port}"
label = os.environ["BC_LABEL"]
cron = os.environ["BC_CRON"]
brain = os.environ["BC_BRAIN"]
muc = os.environ["BC_MUC"]
chat = os.environ.get("BC_CHAT") or "all"
allow = (os.environ.get("BC_ALLOW") or "").lower() in ("1", "true", "yes")
prompt = os.environ["BC_PROMPT"]


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
        "created_by": "seed-bao-chi-brief",
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
        print("-> Hoac: BAO_CHI_BRIEF_ALLOW_NO_CHANNEL=true bash scripts/seed-bao-chi-brief-vps.sh")
        raise SystemExit(2)
    else:
        print("ERROR:", created.get("error") or created)
        raise SystemExit(1)

print("notify:", json.dumps(notify, ensure_ascii=False))
print("muc_quyen:", muc)
print("chat_id:", chat)
PY

echo ""
echo "==> XONG seed Tong hop bao chi 8h."
echo "    Xem / sua / tat: trang Viec dinh ky tren dashboard."
echo "    Sua RSS / chu de: Javis/bao-chi-cau-hinh.md trong brain."
echo "    Goi tay: /tong-hop-bao-chi <chu de> hoac /run brief-bao-chi-sang <chu de>."
