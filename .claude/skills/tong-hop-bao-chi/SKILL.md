---
name: tong-hop-bao-chi
description: "Tổng hợp/tóm tắt báo chí theo danh mục RSS; mỗi bài ghi rõ báo, giờ xuất bản, link đọc; tối đa 10 bài."
description_en: "Summarize press by RSS category; each item shows newspaper, publish time, and read link; up to 10."
group: Nội dung
---

# Tổng hợp báo chí

Skill = **kỹ năng**: chọn danh mục RSS → lọc cửa sổ sáng → tóm tắt → format gửi (Telegram/Zalo/chat).
Nguồn RSS **tách theo danh mục** trong `Javis/bao-chi-cau-hinh.md`.

## Khi nào dùng

- Workflow/nhắc 8h `brief-bao-chi-sang` → danh mục **`giao-duc`**.
- User gọi tay: «tổng hợp báo chí tài chính», «RSS bất động sản».
- Cần tối đa **10 bài mới**, mỗi bài **bắt buộc** có: tên báo + giờ xuất bản + link đọc.

## Chuẩn bị

1. Đọc `Javis/bao-chi-cau-hinh.md`. Thiếu → tạo từ `references/cau-hinh-mau.md`.
2. Chọn **danh mục** (`slug`): brief sáng → `giao-duc`; user nêu lĩnh vực → map slug.
3. Cửa sổ giờ VN: **00:00 hôm qua → 08:00 hôm nay**.
4. Kênh gửi: nhắc hẹn đẩy kết quả qua `chat_id`.

## Cách chạy

```bash
python skills/tong-hop-bao-chi/scripts/fetch_rss.py \
  --config Javis/bao-chi-cau-hinh.md \
  --category giao-duc \
  --limit 10
```

JSON mỗi bài có: `title`, `link`, `source_name` (tên báo), `published_human` (giờ VN), `summary`.

## Quy trình

1. Chạy script → đọc `articles[]`.
2. Viết **Tóm tắt** 4-8 bullet (không bịa số ngoài feed).
3. Mục **Tin mới** (tối đa 10): **mỗi tin một khối**, đủ 3 trường bắt buộc dưới đây.
4. Feed lỗi → mục Nguồn lỗi.

## Định dạng đầu ra (BẮT BUỘC)

Tiếng Việt, không bảng, không em dash. **Mỗi tin phải có đủ Báo / Xuất bản / Link** - thiếu một trong ba là sai khuôn.

```markdown
### Báo chí · <nhãn danh mục> · <dd/mm>

**Danh mục:** <slug>
**Cửa sổ:** 00:00 <hôm qua> → 08:00 <hôm nay> (VN)

**Tóm tắt**
- ...

**Tin mới (tối đa 10)**

1. **<Tiêu đề bài>**
   - Báo: <VnExpress | Tuổi Trẻ | Thanh Niên | …>  ← dùng `source_name`
   - Xuất bản: <HH:mm dd/mm/yyyy>  ← dùng `published_human`
   - Link: <url đầy đủ, bấm được>  ← dùng `link` (có thể viết [Đọc bài](url))
   - Tóm tắt 1 câu: <từ summary, không bịa>

2. **<Tiêu đề bài>**
   - Báo: …
   - Xuất bản: …
   - Link: …
   - Tóm tắt 1 câu: …

**Nguồn lỗi** (bỏ nếu không có)
- …
```

Ví dụ một tin đúng:

```markdown
1. **Chi phí du học Mỹ vượt 100.000 USD/năm ở 15 trường**
   - Báo: VnExpress
   - Xuất bản: 00:02 06/09/2026
   - Link: https://vnexpress.net/chi-phi-du-hoc-my-vuot-100-000-usd-nam-o-15-truong-5114638.html
   - Tóm tắt 1 câu: 15 đại học Mỹ công bố chi phí trên 100.000 USD với tân sinh viên.
```

## Thêm danh mục mới

Copy khối `## Danh mục: <slug>` trong `Javis/bao-chi-cau-hinh.md` (RSS + từ khóa). Không cần sửa skill.

## Bẫy

- Không viết «nguồn · giờ» mơ hồ trên một dòng - phải tách **Báo** / **Xuất bản** / **Link**.
- Không chỉ paste URL RSS feed làm «Báo»; dùng `source_name` (VnExpress, Tuổi Trẻ…).
- Không bỏ link; không bịa giờ/báo nếu JSON thiếu - ghi «không rõ» đúng field đó.
- Brief 8h chỉ danh mục `giao-duc`.

## Kiểm chứng

- Mỗi tin trong top 10 có đủ 3 dòng Báo + Xuất bản + Link chưa?
- Link mở được bài gốc chưa?
- Đúng danh mục / cửa sổ giờ VN chưa?

## Liên kết

- Workflow `brief-bao-chi-sang` - brief 8h `giao-duc`.
- `notes` / `ingest-source` - khi user muốn lưu bài vào brain.
- `query-wiki` - đối chiếu wiki cùng chủ đề nếu cần.
