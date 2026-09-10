---
name: tong-hop-bao-chi
description: "Tổng hợp/tóm tắt báo chí theo danh mục RSS; mỗi bài ghi rõ báo, giờ xuất bản, link đọc; tối đa 10 bài."
description_en: "Summarize press by RSS category; each item shows newspaper, publish time, and read link; up to 10."
group: Nội dung
---

# Tổng hợp báo chí

Skill = **kỹ năng**: chọn danh mục RSS → lọc cửa sổ sáng → tóm tắt → gửi.
Nguồn RSS **tách theo danh mục** trong `Javis/bao-chi-cau-hinh.md`.

## Khi nào dùng

- Workflow/nhắc 8h `brief-bao-chi-sang` → danh mục **`giao-duc`**.
- User gọi tay: «tổng hợp báo chí tài chính», «RSS bất động sản».
- Cần tối đa **10 bài mới**, mỗi bài **bắt buộc** có: tên báo + giờ xuất bản + **link đọc bấm được**.

**Khác** skill **`theo-doi-rss-chu-de`**: skill này = danh mục báo chí cố định trong
`Javis/bao-chi-cau-hinh.md`. RSS theo **chủ đề tùy ý** (blog đối thủ, newsletter ngành)
→ dùng `theo-doi-rss-chu-de`.

## Chuẩn bị

1. Đọc `Javis/bao-chi-cau-hinh.md`. Thiếu → tạo từ `references/cau-hinh-mau.md`.
2. Chọn **danh mục** (`slug`): brief sáng → `giao-duc`; user nêu lĩnh vực → map slug.
3. Cửa sổ giờ VN: **00:00 hôm qua → 08:00 hôm nay**.
4. Kênh gửi: nhắc hẹn đẩy kết quả qua `chat_id` (Telegram/Zalo).

## Cách chạy

```bash
python skills/tong-hop-bao-chi/scripts/fetch_rss.py \
  --config Javis/bao-chi-cau-hinh.md \
  --category giao-duc \
  --limit 10
```

JSON có:
- `articles[]`: `title`, `link`, `source_name`, `published_human`, `summary`
- **`tin_moi_markdown`**: khối Tin mới đã gắn `[tiêu đề](url)` + dòng `Đọc chi tiết: https://...` — **DÁN NGUYÊN VĂN**

## Quy trình (bắt buộc)

1. Chạy script → lấy JSON.
2. Viết **Tóm tắt** 4-8 bullet (không bịa số ngoài feed).
3. Mục **Tin mới**: **copy nguyên** field `tin_moi_markdown`. Không viết lại, không rút gọn, không bỏ URL.
4. Feed lỗi → mục Nguồn lỗi từ `errors`.

## Định dạng đầu ra

```markdown
### Báo chí · <nhãn danh mục> · <dd/mm>

**Danh mục:** <slug>
**Cửa sổ:** 00:00 <hôm qua> → 08:00 <hôm nay> (VN)

**Tóm tắt**
- ...

<dán nguyên tin_moi_markdown ở đây>

**Nguồn lỗi** (bỏ nếu không có)
- …
```

## CẤM

- CẤM tự viết lại danh sách tin (model hay quên URL → Telegram/Zalo không bấm được).
- CẤM bỏ dòng `Đọc chi tiết:` / `Link:` hoặc thay bằng «xem tại nguồn».
- CẤM gộp «nguồn · giờ» trên một dòng mà mất URL.
- CẤM paste URL feed RSS làm tên báo; dùng `source_name`.
- Brief 8h chỉ danh mục `giao-duc`.

## Kiểm chứng trước khi gửi

- Mỗi bài trong Tin mới có **URL `https://`** (trong tiêu đề markdown hoặc dòng Đọc chi tiết) chưa?
- Nếu thiếu → dán lại `tin_moi_markdown`, không gửi bản thiếu link.

## Thêm danh mục mới

Copy khối `## Danh mục: <slug>` trong `Javis/bao-chi-cau-hinh.md`. Không cần sửa skill.

## Liên kết

- Workflow `brief-bao-chi-sang` - brief 8h `giao-duc`.
- `notes` / `ingest-source` - khi user muốn lưu bài vào brain.
- `query-wiki` - đối chiếu wiki cùng chủ đề nếu cần.
