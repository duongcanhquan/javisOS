---
name: Viết bài SEO
description: "Viết bài SEO + SEO GPT: từ khóa, meta, lead trả lời thẳng, FAQ, chunk dễ AI trích dẫn."
description_en: "Write SEO + SEO GPT posts: keywords, meta, direct-answer lead, FAQ, AI-citable chunks."
group: Marketing
---

# Viết bài SEO (+ SEO GPT)

## Khi nào dùng

Cần bài web/blog/landing **xếp tìm kiếm** và **dễ được ChatGPT/Claude/Gemini đưa vào câu trả lời** khi người dùng hỏi.

## Chuẩn bị

Nạp **`seo-gpt`**. Research ngắn (`deep-research`) nếu thiếu fact.

## Quy trình

1. Brief: chủ đề, từ khóa + **câu hỏi chat chính** (vd «học vẽ online ở đâu Hà Nội?»), đối tượng, độ dài (mặc định 1000-1500 chữ), CTA, ngôn ngữ.
2. Outline: H1; 4-7 H2 dạng câu hỏi/ý rõ; khối FAQ; chỗ định nghĩa.
3. Viết:
   - **Lead SEO GPT** (40-80 chữ): trả lời thẳng câu hỏi chính, nêu entity.
   - Thân bài đoạn ngắn, ví dụ cụ thể, từ khóa tự nhiên (không nhồi).
   - Định nghĩa 1 câu + bước đánh số nếu là how-to.
   - **FAQ** 3-6 Q&A cuối (hoặc xen mục).
4. Khối kỹ thuật SEO cổ điển:
   - Title ≤60, meta ≤155, slug
   - 3 biến thể OG title
5. Khối SEO GPT (bắt buộc trong file xuất):
   - «Đoạn chat có thể trích» (copy lead)
   - Danh sách entity (tên, nơi, đối tượng)
   - FAQ raw
6. Lưu `exports/marketing/<slug>/bai-seo.md`.

## Kiểm chứng

H1 đúng 1; lead trả lời thẳng; ≥3 FAQ; ≥1 ví dụ; ≥1 CTA; meta hợp lệ; không bịa số; đọc skill `seo-gpt` đủ tiêu chí chính.
