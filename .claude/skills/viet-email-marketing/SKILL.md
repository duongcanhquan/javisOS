---
name: Viết email marketing
description: "Soạn chuỗi email nurture/welcome/cold B2B; chỉ bản thảo, không tự gửi trừ khi được lệnh."
description_en: "Draft nurture/welcome/cold B2B email sequences; drafts only unless user orders send."
group: Marketing
---

# Viết email marketing

Chuỗi lifecycle / drip và cold B2B: subject, body, CTA, nhịp gửi - **chỉ soạn bản**.

## When to use

- Welcome, nurture, re-engage, post-purchase, event, educational.
- Cold outreach / prospecting / follow-up B2B.
- Không dùng cho «gửi giúp email ngay» qua MCP trừ khi user **lệnh rõ** thread/người nhận.

## Trước khi viết

1. Đọc `product-marketing-context` nếu có.
2. Loại chuỗi, trigger vào list, mục tiêu chính, tone, ràng buộc pháp lý (không spam / không bịa claim).

## Lifecycle / drip

- Map 3-7 email: mục đích từng lá, delay gợi ý, 1 CTA/lá.
- Subject ngắn, cụ thể; preview text không lặp subject.
- Body scannable; P.S. tùy chọn cho CTA phụ.
- Lưu `exports/marketing/<slug>/email-sequence.md`.

## Cold B2B

- Viết như đồng nghiệp, không brochure.
- Cá nhân hóa neo pain / tín hiệu thật user cung cấp (không bịa research).
- Siêu ngắn: mỗi câu phải đẩy tới reply.
- Chuỗi follow-up 2-4 lá, góc khác nhau, không «checking in» trống.
- Goal mặc định = trả lời / book họp, không hard-sell ngay lá 1.

## An toàn

- Mặc định **không** gọi MCP gửi mail / Zalo / Telegram.
- User bảo gửi → xác nhận người nhận / thread rồi mới dùng tool kênh tương ứng.
- Không tạo loop `mode: full` tự blast email.

## Nguồn

Rút gọn VI từ [marketingskills/emails](https://github.com/coreyhaines31/marketingskills) + cold-email (MIT).
