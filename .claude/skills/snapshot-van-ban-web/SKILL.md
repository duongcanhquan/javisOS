---
name: snapshot-van-ban-web
description: "Chụp văn bản pháp lý công khai từ web vào sources/phap-che (bản ngày), rồi đề xuất INGEST. Không phụ thuộc URL sống lâu dài."
description_en: "Snapshot a public legal text from the web into sources/phap-che (dated copy), then suggest INGEST. Do not rely on live URLs long-term."
group: AI
---

# Snapshot văn bản web → kho pháp chế

## Khi nào dùng

Người dùng cần nghị định / thông tư / luật **mới trên mạng** mà chưa có trong
`sources/phap-che` hoặc wiki. Dùng sau deep-research hoặc khi họ dán URL chính thức.

## Cách làm

1. Xác định nguồn **chính thức** (cổng thông tin pháp luật, công báo). Ghi URL + ngày truy cập.
2. Lấy **toàn văn** (hoặc các Điều liên quan đủ để cite). Không chỉ tóm tắt từ SERP.
3. Ghi file:

```
sources/phap-che/<linh-vuc>/YYYY-MM-DD-snapshot-<so-hieu-ngan>.md
```

Frontmatter gợi ý:

```yaml
---
type: source
source_kind: legal
status: unprocessed
legal_id: "..."
issued: YYYY-MM-DD
snapshot_date: YYYY-MM-DD
source_url: "https://..."
tags: [phap-che, snapshot]
---
```

4. Thân bài: giữ số **Điều / Khoản**; cuối file mục `## Nguồn snapshot` (URL + ngày).
5. Đề xuất chạy skill **ingest-source** → wiki; cập nhật `wiki/index.md` mục Pháp chế.
6. Nếu kho PDF lớn: nhắc sync Drive (`scripts/sync-phap-che-drive.sh`) + RAG sidecar — không thay bước wiki.

## Cấm

- Chỉ để link mà không có bản text trong vault.
- Nhồi snapshot vào `memory/MEMORY.md`.
- Khẳng định hiệu lực pháp lý tuyệt đối chỉ từ một trang web thứ cấp.
