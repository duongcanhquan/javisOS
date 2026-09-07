---
name: Kiểm tra SEO
description: "Soi SEO on-page/nội dung: title, meta, H1-H2, từ khóa, liên kết; checklist sửa có ưu tiên."
group: Marketing
---

# Kiểm tra SEO

## Khi nào dùng

User đưa URL, HTML, hoặc bản nháp bài và muốn biết **lỗi SEO + cách sửa**.

## Quy trình

1. Chốt brief: URL hoặc nội dung, từ khóa mục tiêu (nếu có), đối tượng.
2. Thu thập: WebFetch trang (nếu có); không fetch được thì yêu cầu dán title/H1/đoạn mở.
3. Soi theo thứ tự ưu tiên:
   - Index / canonical / trùng title
   - Title (≤60 ký tự ý), meta description (≤155), H1 đúng 1
   - Cấu trúc H2-H3, từ khóa tự nhiên
   - Ảnh alt, internal links, CTA
   - Open Graph (dùng thêm skill `fixing-metadata` nếu là HTML trong repo)
4. Chấm nhanh: Tốt / Cần sửa / Yếu + điểm 0-10 từng mục.
5. Checklist sửa ưu tiên P0/P1/P2 (câu cụ thể, có thể copy).
6. Lưu `exports/marketing/<slug>/seo-audit.md`.

## Định dạng đầu ra

```
# SEO audit: <url hoặc tên>
## Tóm tắt (3-5 dòng)
## Bảng điểm
## Chi tiết theo mục
## Checklist sửa (P0 → P2)
## Ví dụ title/meta đề xuất (2-3 biến thể)
```

## Bẫy

Không bịa thứ hạng Google. Không hứa «lên top 1». Thiếu dữ liệu thì ghi rõ giả định.
