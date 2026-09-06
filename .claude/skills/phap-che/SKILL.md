---
name: phap-che
description: "Pháp chế cá nhân: tư vấn / tham chiếu văn bản pháp lý từ wiki+sources/phap-che (và tool phap_che_search nếu có). Luôn cite số hiệu + điều; không bịa; không thay luật sư."
description_en: "Personal legal counsel: advise from wiki+sources/phap-che (and phap_che_search if available). Always cite instrument + article; never invent; not a substitute for a lawyer."
group: AI
---

# Pháp chế cá nhân

## Khi nào dùng

Người dùng hỏi luật, nghị định, thông tư; cần rà compliance khi chạy dự án; đối chiếu
hợp đồng với quy định; hoặc bảo "đóng vai pháp chế".

## Kho dữ liệu (không nhồi MEMORY.md)

| Lớp | Nơi | Vai trò |
|---|---|---|
| Bản gốc PDF/DOCX | Google Drive `Phap-che/...` | Source of truth file |
| Text đã extract | `sources/phap-che/<linh-vuc>/<so-hieu>.md` | Ingest được |
| Tri thức đã chắt | `wiki/` (mục Pháp chế / trang theo văn bản) | Cite ổn định |
| Memory | `memory/` | **Không** dùng làm thư viện luật |

Quy ước Drive + vault: xem `docs/28-phap-che-ca-nhan.md`.

## Bắt buộc

1. **Đọc trước khi khẳng định:** `wiki/index.md` → trang wiki pháp chế → `sources/phap-che/` nếu thiếu.
2. Gọi tool **`phap_che_search`** (nếu có trong session) với câu hỏi / số hiệu / từ khóa Điều.
   - Kết quả wiki/sources: ưu tiên.
   - Kết quả RAG sidecar: dùng khi wiki mỏng; vẫn phải ghi rõ nguồn file.
3. Mỗi khẳng định cụ thể kèm **số hiệu văn bản + Điều/Khoản** (và `[[wikilink]]` nếu có trang).
4. **Không bịa** điều khoản. Thiếu trong kho → nói rõ "chưa có trong kho pháp chế" + đề xuất
   đưa file vào Drive/`sources/phap-che` rồi INGEST.
5. Cuối câu trả lời có **disclaimer ngắn**: tham khảo nội bộ, không thay thế luật sư / tư vấn pháp lý chính thức.
6. Cấm: nhồi nội dung luật dài vào `memory/MEMORY.md` hoặc `memory/facts/`.

## Luồng khi chạy dự án

1. Đọc brief / project pins (chỉ `.md` — PDF phải extract trước).
2. Liệt kê rủi ro pháp lý liên quan lĩnh vực dự án.
3. `phap_che_search` + query-wiki cho từng rủi ro.
4. Bảng: rủi ro | căn cứ (số hiệu+điều) | mức chắc | việc cần làm / hỏi thêm.

## Ingest văn bản mới

1. Đặt/extract thành `sources/phap-che/<linh-vuc>/<YYYY>-<so-hieu>-<ten-ngan>.md`
   Frontmatter gợi ý: `type: source`, `source_kind: legal`, `status: unprocessed`,
   `legal_id`, `issued`, `drive_url` (nếu có).
2. Chạy skill **ingest-source** → wiki 1 trang / văn bản (hoặc theo chương nếu rất dài).
3. Cập nhật `wiki/index.md` mục **Pháp chế**.

## So sánh hai văn bản

Dùng skill **so-sanh-van-ban-phap-ly** (bảng Điều A vs Điều B, cite hai phía).

## Liên kết

- `ingest-source` — nạp văn bản mới vào wiki.
- `query-wiki` — tra khái niệm đã chắt.
- `deep-research` — chỉ khi cần văn bản **công khai mới trên web**; sau đó dùng
  **snapshot-van-ban-web** để lưu vào `sources/phap-che` (không phụ thuộc URL sống).
- Tool `phap_che_search` / `phap_che_status` (plugin bundled).
- `so-sanh-van-ban-phap-ly` — đối chiếu Điều A vs B.
