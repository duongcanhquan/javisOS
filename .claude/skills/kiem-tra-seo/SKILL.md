---
name: Kiểm tra SEO
description: "Audit SEO cổ điển + SEO GPT (LLM): title/meta/H1 và khả năng được chat AI trích dẫn."
group: Marketing
---

# Kiểm tra SEO (+ SEO GPT)

## Khi nào dùng

User đưa URL / HTML / bản nháp và muốn biết lỗi **SEO tìm kiếm** lẫn **SEO GPT** (để mô hình ngôn ngữ dễ đọc và đưa vào khi chat).

## Chuẩn bị

Nạp thêm skill **`seo-gpt`** (tiêu chí GEO/LLMO). HTML trong repo: có thể dùng `fixing-metadata`.

## Quy trình

1. Chốt brief: URL hoặc nội dung, từ khóa / câu hỏi mục tiêu, đối tượng.
2. Thu thập: WebFetch nếu có URL; không được thì xin title, H1, đoạn mở, mục lục.
3. **SEO cổ điển** (ưu tiên):
   - Index / canonical / trùng title
   - Title ≤60 ý, meta ≤155, đúng 1 H1
   - H2-H3, từ khóa tự nhiên, alt, internal link, CTA
   - Open Graph nếu soi HTML
4. **SEO GPT** (bắt buộc, theo skill `seo-gpt`):
   - Có câu trả lời thẳng đầu trang?
   - Entity / tên thương hiệu rõ?
   - H2 dạng câu hỏi hội thoại?
   - Có FAQ đủ ý?
   - Định nghĩa + bước / bảng?
   - Chunk đoạn ngắn, có nguồn/uy tín?
5. Chấm 0-10 từng mục; Tốt / Cần sửa / Yếu.
6. Checklist P0→P2 (câu copy được), tách cột Cổ điển | GPT nếu khác nhau.
7. Lưu `exports/marketing/<slug>/seo-audit.md`.

## Định dạng đầu ra

```
# SEO audit: <url hoặc tên>
## Tóm tắt (3-5 dòng) - nêu cả SEO web và SEO GPT
## Bảng điểm SEO cổ điển
## Bảng điểm SEO GPT (theo tiêu chí seo-gpt)
## Chi tiết
## Checklist sửa (P0 → P2)
## Title / meta / lead trả lời thẳng đề xuất (2-3 biến thể)
## Gợi ý FAQ (3-5 Q&A) nếu trang đang thiếu
```

## Bẫy

Không bịa ranking Google hay «ChatGPT sẽ nhắc tới brand». Thiếu dữ liệu thì ghi giả định.
