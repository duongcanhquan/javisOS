# Kho pháp chế (sources)

Thư mục này chứa **bản text** văn bản pháp lý đã extract từ PDF/DOCX (hoặc chép từ nguồn
công khai), sẵn sàng INGEST vào wiki.

## Quy ước

```
sources/phap-che/
  <linh-vuc>/                          # vd lao-dong, thue, doanh-nghiep, du-lieu-ca-nhan
    YYYY-<so-hieu>-<ten-ngan>.md       # vd 2023-13-2023-ND-CP-bao-ve-du-lieu.md
```

Frontmatter gợi ý:

```yaml
---
type: source
source_kind: legal
status: unprocessed
legal_id: "13/2023/NĐ-CP"
issued: 2023-04-17
drive_url: "https://drive.google.com/..."
tags: [phap-che, du-lieu]
---
```

Giữ nguyên số **Điều / Khoản** trong thân bài. PDF gốc để trên Drive `Phap-che/`; không
cần commit PDF vào git brain.

## Việc tiếp theo

1. Thêm file `.md` vào đúng lĩnh vực.
2. Trong chat: "ingest source sources/phap-che/..." (skill **ingest-source**).
3. Hỏi / chạy dự án với skill **phap-che** hoặc agent **Pháp chế** (Studio → seed pháp chế).

Chi tiết: `docs/28-phap-che-ca-nhan.md`.
