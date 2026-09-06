#!/usr/bin/env bash
# Seed nhắc hẹn "Báo cáo giáo dục CĐ-ĐH 8h" trên VPS (container Javis).
# Idempotent: cùng label thì cập nhật text/cron/chat_id, không tạo trùng.
# Gửi cả Telegram + Zalo (chat_id=all). Cần đã đấu kênh + Tavily (hoặc WebSearch).
set -euo pipefail

CONTAINER="${JAVIS_CONTAINER:-javis}"
PORT="${JAVIS_PORT:-7777}"
LABEL="${EDU_BRIEF_LABEL:-Báo cáo giáo dục CĐ-ĐH 8h}"
CRON="${EDU_BRIEF_CRON:-0 8 * * *}"
BRAIN="${EDU_BRIEF_BRAIN:-brain}"
# Chỉ đọc web + tóm tắt; không ghi hệ thống ngoài.
MUC_QUYEN="${EDU_BRIEF_MUC_QUYEN:-suggest}"
ALLOW_NO_CHANNEL="${EDU_BRIEF_ALLOW_NO_CHANNEL:-false}"
# all = Telegram + Zalo (mọi whitelist đã đấu)
CHAT_ID="${EDU_BRIEF_CHAT_ID:-all}"

PROMPT=$(cat <<'EOF'
Làm đúng skill bao-cao-giao-duc-sang (giờ VN).

Nhiệm vụ: điểm tin buổi sáng về giáo dục CAO ĐẲNG / ĐẠI HỌC Việt Nam.

1) Dùng Tavily (hoặc WebSearch) quét ~10 nguồn báo uy tín (Giáo dục & Thời đại, Vietnamnet, Dân trí, Tuổi Trẻ, Thanh Niên, VnExpress, Tiền Phong, Báo Chính phủ, moet.gov.vn, Người Lao Động…) lấy bài MỚI (ưu tiên 24–48h).
2) Chọn khoảng 10 bài đa nguồn: chính sách/thông tư, tuyển sinh–học phí, liên kết DN–thực tập–việc làm SV, kiểm định/xếp hạng nếu có.
3) Mỗi mục: tiêu đề ngắn + 1–2 câu ý chính + link URL gốc đọc được. Không bịa số liệu / tên văn bản.
4) Cuối: 1 câu "Nhịp chính hôm nay" + liệt kê nguồn đã quét.
5) Viết ngắn như tin nhắn Telegram/Zalo. Kết quả gửi về chat_id=all (Telegram và Zalo nếu đã đấu).

Thiếu Tavily/WebSearch thì nói thẳng không tra được web, không bịa tin.
EOF
)

echo "==> container: $CONTAINER"
if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  CONTAINER=$(docker ps --format '{{.Names}}' | grep -E 'javis' | head -1 || true)
fi
if [ -z "${CONTAINER}" ]; then
  echo "ERROR: không thấy container javis đang chạy."
  exit 1
fi
echo "==> dùng container: $CONTAINER"

echo "==> seed nhắc: $LABEL (cron $CRON, chat_id=$CHAT_ID, brain=$BRAIN)"
docker exec -i -u javis \
  -e "JAVIS_PORT=$PORT" \
  -e "EDU_LABEL=$LABEL" \
  -e "EDU_CRON=$CRON" \
  -e "EDU_BRAIN=$BRAIN" \
  -e "EDU_MUC=$MUC_QUYEN" \
  -e "EDU_ALLOW=$ALLOW_NO_CHANNEL" \
  -e "EDU_CHAT=$CHAT_ID" \
  -e "EDU_PROMPT=$PROMPT" \
  "$CONTAINER" python - <<'PY'
import json, os, urllib.error, urllib.parse, urllib.request

port = os.environ.get("JAVIS_PORT", "7777")
base = f"http://127.0.0.1:{port}"
label = os.environ["EDU_LABEL"]
cron = os.environ["EDU_CRON"]
brain = os.environ["EDU_BRAIN"]
muc = os.environ["EDU_MUC"]
allow = os.environ.get("EDU_ALLOW", "false").lower() in ("1", "true", "yes")
chat_id = os.environ.get("EDU_CHAT", "all")
prompt = os.environ["EDU_PROMPT"]


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

payload_common = {
    "text": prompt,
    "label": label,
    "mode": "task",
    "cron": cron,
    "muc_quyen": muc,
    "chat_id": chat_id,
}

if existing:
    rid = existing["id"]
    upd = call("POST", "/reminders/update", {
        "id": rid,
        "brain": brain,
        **payload_common,
    }, form=True)
    print("updated:", json.dumps(upd, ensure_ascii=False))
    if not upd.get("ok"):
        raise SystemExit(1)
    print(f"OK: da cap nhat nhac '{label}' id={rid}")
else:
    created = call("POST", "/reminders", {
        **payload_common,
        "brain": brain,
        "created_by": "seed-edu-brief",
        "allow_no_channel": allow,
    })
    print("created:", json.dumps(created, ensure_ascii=False))
    if created.get("ok"):
        print(f"OK: da tao nhac '{label}' id={created.get('id')} "
              f"lan chay ke {created.get('due_human') or created.get('due_at')}")
        if created.get("canh_bao"):
            print("CANH_BAO:", created["canh_bao"])
    elif created.get("can_force"):
        print("NEED_CHANNEL:", created.get("error"))
        print("-> Dau Telegram va Zalo (trang Kenh) roi chay lai script.")
        print("-> Hoac: EDU_BRIEF_ALLOW_NO_CHANNEL=true bash scripts/seed-edu-brief-vps.sh")
        raise SystemExit(2)
    else:
        print("ERROR:", created.get("error") or created)
        raise SystemExit(1)

print("notify:", json.dumps(notify, ensure_ascii=False))
print("chat_id:", chat_id, "(all = Telegram + Zalo)")
print("muc_quyen:", muc)
PY

# Ghi agent + skill mirror vào Brain Default (để chạy tay / Studio thấy)
echo "==> ghi agent + skill vào brain"
docker exec -i -u javis "$CONTAINER" python - <<'PY'
from pathlib import Path
import os, textwrap

root = Path(os.environ.get("BRAINS_DIR", "/brains")) / "Brain Default"
agents = root / "agents"
skills = root / "skills" / "bao-cao-giao-duc-sang"
workflows = root / "workflows"
for p in (agents, skills, workflows):
    p.mkdir(parents=True, exist_ok=True)

(agents / "bao-cao-giao-duc-sang.md").write_text(textwrap.dedent("""\
---
type: agent
name: Báo cáo giáo dục sáng
slug: bao-cao-giao-duc-sang
role: Điểm tin CĐ/ĐH Việt Nam mỗi sáng - chính sách, tuyển sinh, liên kết DN - kèm link báo.
group: Nội dung
skills:
- bao-cao-giao-duc-sang
- deep-research
model: ""
updated: "2026-09-06"
---

Bạn làm đúng skill **bao-cao-giao-duc-sang**.

Khi được giao brief hoặc nhắc 8h:
1. Tra web (Tavily ưu tiên) ~10 báo giáo dục Việt Nam.
2. Chọn ~10 bài mới về CĐ/ĐH (chính sách, tuyển sinh, DN/thực tập).
3. Mỗi bài: tiêu đề + 1–2 câu + URL gốc.
4. Kết thúc bằng nhịp chính hôm nay.

Không bịa. Thiếu tool web thì nói thẳng. Viết ngắn cho Telegram/Zalo.
"""), encoding="utf-8")

# Skill body: trỏ sang system skill nếu có; vẫn ghi SKILL ngắn để brain tự đủ
(skills / "SKILL.md").write_text(textwrap.dedent("""\
---
name: Báo cáo giáo dục sáng
description: "Tóm tắt ~10 bài báo mới về CĐ/ĐH Việt Nam (chính sách, tuyển sinh, liên kết DN) kèm link."
group: Nội dung
---

# Báo cáo giáo dục sáng

Làm theo skill hệ thống `bao-cao-giao-duc-sang` (đồng bộ từ app).

Tóm tắt ~10 bài mới CĐ/ĐH VN, kèm URL, gửi tin nhắn ngắn Telegram/Zalo.
Ưu tiên Tavily; đa nguồn; không bịa số liệu.
"""), encoding="utf-8")

(workflows / "bao-cao-giao-duc-sang.md").write_text(textwrap.dedent("""\
---
type: workflow
name: Báo cáo giáo dục sáng (CĐ/ĐH)
slug: bao-cao-giao-duc-sang
status: active
group: Nội dung
description: Một bước điểm tin ~10 bài báo CĐ/ĐH + link - dùng tay hoặc kèm nhắc 8h.
steps:
- agent: bao-cao-giao-duc-sang
  task: "Chạy skill bao-cao-giao-duc-sang cho brief: {{input}}. Nếu input trống: điểm tin sáng hôm nay (giờ VN), ~10 bài CĐ/ĐH kèm link."
updated: "2026-09-06"
---

Workflow tay để chạy lại điểm tin bất cứ lúc nào. Lịch 8h dùng nhắc hẹn (seed script), không cần bật workflow lặp.
"""), encoding="utf-8")

print("OK: agent+skill+workflow trong", root)
PY

echo ""
echo "==> XONG seed Báo cáo giáo dục CĐ-ĐH 8h."
echo "    Xem/sửa/tắt: trang Việc định kỳ trên dashboard."
echo "    Cần: Telegram + Zalo (Kênh) và Tavily hoặc WebSearch."
echo "    Chạy tay: Studio → agent/workflow 'Báo cáo giáo dục sáng'."
echo "    Đổi giờ: EDU_BRIEF_CRON='0 7 * * *' bash scripts/seed-edu-brief-vps.sh"
