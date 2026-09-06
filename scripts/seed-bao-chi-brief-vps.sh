#!/usr/bin/env bash
# Seed nhắc hẹn "Tổng hợp báo chí 8h" (danh mục giáo dục) trên VPS.
# Idempotent: cùng label thì cập nhật text/cron, không tạo trùng.
set -euo pipefail

CONTAINER="${JAVIS_CONTAINER:-javis}"
PORT="${JAVIS_PORT:-7777}"
LABEL="${BAO_CHI_BRIEF_LABEL:-Tổng hợp báo chí 8h}"
CRON="${BAO_CHI_BRIEF_CRON:-0 8 * * *}"
BRAIN="${BAO_CHI_BRIEF_BRAIN:-brain}"
MUC_QUYEN="${BAO_CHI_BRIEF_MUC_QUYEN:-suggest}"
ALLOW_NO_CHANNEL="${BAO_CHI_BRIEF_ALLOW_NO_CHANNEL:-false}"
CHAT_ID="${BAO_CHI_BRIEF_CHAT_ID:-all}"

PROMPT=$(cat <<'EOF'
Chạy workflow brief-bao-chi-sang / skill tong-hop-bao-chi với danh mục CỐ ĐỊNH: giao-duc.

1) Đọc Javis/bao-chi-cau-hinh.md - chỉ khối ## Danh mục: giao-duc.
2) Cửa sổ giờ VN: 00:00 HÔM QUA → 08:00 HÔM NAY.
3) Chạy fetch_rss.py --config Javis/bao-chi-cau-hinh.md --category giao-duc --limit 10.
4) Viết báo cáo theo khuôn skill:
   - Phần Tóm tắt (bullet)
   - Phần Tin mới: MỖI bài phải có đủ 3 dòng bắt buộc:
     · Báo: tên tờ (VnExpress, Tuổi Trẻ…) từ source_name
     · Xuất bản: giờ từ published_human
     · Link: URL bài đầy đủ (bấm được)
     · Tóm tắt 1 câu
   Không gộp mơ hồ. Không bịa. Không trộn RSS tài chính/BĐS.

Chỉ ĐỌC RSS và tóm tắt. Kết quả do hệ thống nhắc đẩy về kênh. Tiếng Việt, ngắn như tin nhắn.
EOF
)

echo "==> container: $CONTAINER"
if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  echo "ERROR: container '$CONTAINER' không chạy. Bật Javis trước: docker compose up -d"
  exit 1
fi

echo "==> đảm bảo Javis/bao-chi-cau-hinh.md (đa danh mục) trong các brain"
docker exec -i -u javis "$CONTAINER" python - <<'PY'
from pathlib import Path
import os

brains_root = Path(os.environ.get("BRAINS_DIR", "/brains"))
sample = """---
type: note
title: Cấu hình báo chí theo danh mục RSS
updated: 2026-09-06
---

# Cấu hình báo chí theo danh mục

Skill `tong-hop-bao-chi` đọc file này: mỗi danh mục có RSS riêng.

## Danh mục mặc định

giao-duc

## Danh mục: giao-duc

### Nhãn

Giáo dục cao đẳng - đại học

### RSS

- https://vnexpress.net/rss/giao-duc.rss
- https://tuoitre.vn/rss/giao-duc.rss
- https://thanhnien.vn/rss/giao-duc.rss
- https://vietnamnet.vn/rss/giao-duc.rss

### Từ khóa

đại học, cao đẳng, tuyển sinh, sinh viên, giảng viên, học phí, ĐH, CĐ, Bộ GDĐT, Bộ Giáo dục, university, college, đào tạo

## Danh mục: tai-chinh

### Nhãn

Tài chính - kinh doanh

### RSS

- https://vnexpress.net/rss/kinh-doanh.rss
- https://tuoitre.vn/rss/kinh-doanh.rss
- https://thanhnien.vn/rss/kinh-doanh.rss
- https://vietnamnet.vn/rss/kinh-doanh.rss

### Từ khóa

chứng khoán, ngân hàng, lãi suất, tỷ giá, lạm phát, tài chính, kinh doanh, đầu tư, VN-Index, trái phiếu

## Danh mục: bat-dong-san

### Nhãn

Bất động sản

### RSS

- https://vnexpress.net/rss/bat-dong-san.rss
- https://tuoitre.vn/rss/bat-dong-san.rss
- https://thanhnien.vn/rss/bat-dong-san.rss
- https://vietnamnet.vn/rss/bat-dong-san.rss

### Từ khóa

bất động sản, nhà đất, chung cư, dự án, quy hoạch, giá nhà, đất nền, BĐS, căn hộ, sổ đỏ

## Ghi chú

- Workflow 8h = danh mục `giao-duc`.
- Gọi tay: «tổng hợp báo chí tài chính» → `tai-chinh`.
"""
written = 0
upgraded = 0
if not brains_root.is_dir():
    print(f"WARN: khong thay brains_root={brains_root}")
else:
    for brain in sorted(brains_root.iterdir()):
        if not brain.is_dir() or brain.name.startswith("."):
            continue
        dest = brain / "Javis" / "bao-chi-cau-hinh.md"
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            dest.write_text(sample, encoding="utf-8")
            written += 1
            print(f"wrote {dest}")
        elif "Danh mục:" not in dest.read_text(encoding="utf-8"):
            dest.write_text(sample, encoding="utf-8")
            upgraded += 1
            print(f"upgraded {dest}")
    print(f"ok: newly={written} upgraded={upgraded}")
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
        print("-> Dau Telegram/Zalo roi chay lai, hoac BAO_CHI_BRIEF_ALLOW_NO_CHANNEL=true")
        raise SystemExit(2)
    else:
        print("ERROR:", created.get("error") or created)
        raise SystemExit(1)

print("notify:", json.dumps(notify, ensure_ascii=False))
print("muc_quyen:", muc, "| chat_id:", chat, "| category: giao-duc")
PY

echo ""
echo "==> XONG. Brief 8h = danh muc giao-duc."
echo "    Sua RSS: Javis/bao-chi-cau-hinh.md"
echo "    Goi tay: tong hop bao chi tai-chinh / bat-dong-san"
echo "    Workflow: /run brief-bao-chi-sang"
