#!/usr/bin/env bash
# Seed Pháp chế (Pha A - nhẹ): agent + khung sources/phap-che theo folder Drive RAG VĂN BẢN.
# Idempotent: ghi đè agent phap-che.md; tạo thư mục lĩnh vực nếu thiếu.
set -euo pipefail

CONTAINER="${JAVIS_CONTAINER:-javis}"
# Folder Drive: https://drive.google.com/drive/u/0/folders/1NwpPUVxnGJfQER-5qKg0ejw7ry57pcGM
DRIVE_FOLDER_ID="${PHAP_CHE_DRIVE_FOLDER_ID:-1NwpPUVxnGJfQER-5qKg0ejw7ry57pcGM}"
DRIVE_URL="https://drive.google.com/drive/folders/${DRIVE_FOLDER_ID}"

echo "==> container hint: $CONTAINER"
if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  CONTAINER=$(docker ps --format '{{.Names}}' | grep -E 'javis' | head -1 || true)
fi
if [ -z "${CONTAINER}" ]; then
  echo "ERROR: không thấy container javis đang chạy"
  exit 1
fi
echo "==> dùng container: $CONTAINER"
echo "==> Drive: $DRIVE_URL"

docker exec -i -u javis -e DRIVE_FOLDER_ID="$DRIVE_FOLDER_ID" -e DRIVE_URL="$DRIVE_URL" \
  "$CONTAINER" python - <<'PY'
from pathlib import Path
import os
from datetime import date

brains_root = Path(os.environ.get("BRAINS_DIR", "/brains"))
drive_id = os.environ.get("DRIVE_FOLDER_ID", "")
drive_url = os.environ.get("DRIVE_URL", "")
today = date.today().isoformat()

# Map folder Drive → slug local (Pha A)
LINH_VUC = [
    ("hanh-chinh-nhan-su", "Hành Chính & Nhân sự"),
    ("luat-nghi-dinh", "Luật & Nghị Định"),
    ("phong-dao-tao", "Phòng đào tạo"),
    ("quy-che-noi-bo", "Quy chế, Quy định nội bộ"),
    ("quy-chuan-bo-gddt", "Quy chuẩn Bộ GDĐT"),
    ("quy-dinh-bo-gddt", "Quy định Bộ GDĐT"),
]

readme = f"""---
type: note
title: Kho pháp chế (sources)
updated: {today}
drive_folder_id: "{drive_id}"
drive_url: "{drive_url}"
---

# Kho pháp chế (sources)

Bản text đã extract từ PDF/DOCX trên Drive **RAG VĂN BẢN**. PDF gốc giữ trên Drive; không nhồi vào memory.

## Drive gốc

- Folder: [RAG VĂN BẢN]({drive_url})
- ID: `{drive_id}`

## Quy ước thư mục

| Thư mục Drive | Thư mục trong brain |
|---|---|
""" + "\n".join(f"| {ten} | `sources/phap-che/{slug}/` |" for slug, ten in LINH_VUC) + f"""

File: `YYYY-<so-hieu>-<ten-ngan>.md`

```yaml
---
type: source
source_kind: legal
status: unprocessed
legal_id: "..."
issued: YYYY-MM-DD
drive_url: "..."
tags: [phap-che]
---
```

## Việc tiếp theo (Pha A)

1. Extract 5–10 văn bản hay hỏi → đúng thư mục lĩnh vực.
2. Chat: ingest source `sources/phap-che/...` (skill **ingest-source**).
3. Hỏi qua agent **Pháp chế** / skill `phap-che` — bắt buộc cite số hiệu + Điều.
4. Pha B (sau): `scripts/sync-phap-che-drive.sh` + RAG sidecar — xem `docs/28-phap-che-ca-nhan.md`.
"""

agent_body = """Bạn là pháp chế nội bộ của nhà trường / tổ chức (không phải luật sư).

BẮT BUỘC tuân skill `phap-che`:
- Chỉ khẳng định khi có căn cứ trong wiki / sources/phap-che / tool `phap_che_search`.
- Mỗi điểm cụ thể ghi số hiệu văn bản + Điều/Khoản (+ [[wikilink]] nếu có).
- Thiếu trong kho → nói rõ và đề xuất đưa file từ Drive RAG VĂN BẢN vào sources rồi INGEST.
- Không nhồi luật vào memory/MEMORY.md.
- Cuối trả lời: disclaimer tham khảo nội bộ, không thay thế tư vấn pháp lý chính thức.

Khi chạy dự án / triển khai: bảng rủi ro | căn cứ | mức chắc | việc cần làm.
So sánh văn bản: skill `so-sanh-van-ban-phap-ly`.
"""

agent_md = f"""---
type: agent
name: Pháp chế
slug: phap-che
role: Tư vấn / tham chiếu văn bản pháp lý từ kho Drive+sources; cite điều khoản; không bịa.
group: Pháp chế
skills: [phap-che, so-sanh-van-ban-phap-ly, snapshot-van-ban-web, query-wiki, ingest-source]
model: gemini-3.1-pro-high
model_provider: antigravity-cli
updated: {today}
---
{agent_body}
"""

dirs = sorted(p for p in brains_root.iterdir() if p.is_dir() and not p.name.startswith("."))
if not dirs:
    print(f"WARN: không thấy brain trong {brains_root}", flush=True)

for root in dirs:
    name = root.name
    (root / "agents").mkdir(parents=True, exist_ok=True)
    (root / "sources" / "phap-che").mkdir(parents=True, exist_ok=True)
    for slug, _ in LINH_VUC:
        d = root / "sources" / "phap-che" / slug
        d.mkdir(parents=True, exist_ok=True)
        keep = d / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")
    (root / "sources" / "phap-che" / "README.md").write_text(readme, encoding="utf-8")
    (root / "agents" / "phap-che.md").write_text(agent_md, encoding="utf-8")
    print(f"==> {name}: agent phap-che + sources/phap-che ({len(LINH_VUC)} lĩnh vực)", flush=True)

print("DONE", flush=True)
PY

echo "==> seed pháp chế xong (Pha A)"
echo "    Drive: $DRIVE_URL"
echo "    Tiếp: extract vài PDF → sources/phap-che/<linh-vuc>/ rồi ingest trong chat"
