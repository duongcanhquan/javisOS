---
name: Tối ưu chuyển đổi CRO
description: "Audit CRO trang/form: giá trị 5 giây, CTA, ma sát; ưu tiên sửa; bàn giao landing/SEO."
description_en: "CRO audit for pages/forms: 5-second value, CTA, friction; prioritize fixes; hand off landing/SEO."
group: Marketing
---

# Tối ưu chuyển đổi (CRO)

Audit trang / form để tăng chuyển đổi: rõ giá trị, CTA, giảm ma sát.

## When to use

- User nói CRO, «không convert», «landing yếu», «form bỏ giữa chừng», gửi URL cần feedback.
- Signup/popup: gộp vào checklist dưới (không tách skill).

## Trước khi audit

1. Đọc `product-marketing-context` nếu có (`wiki/product-marketing.md` hoặc `exports/marketing/product-marketing.md`).
2. Xác định: loại trang, **1 CTA chính**, nguồn traffic (organic/paid/email/social).

## Khung phân tích (ưu tiên impact)

1. **Value 5 giây** - hiểu ngay «là gì / cho ai / vì sao quan tâm»; tránh jargon nội bộ.
2. **CTA** - một hành động chính; copy cụ thể; vị trí above-the-fold + lặp hợp lý.
3. **Bằng chứng** - số, testimonial, logo, bảo đảm (không bịa).
4. **Ma sát form** - số field, lý do hỏi từng field, lỗi / mobile.
5. **Tin cậy & lo lắng** - chính sách, bảo mật, «sẽ xảy ra gì sau khi bấm».
6. **Đồng bộ message** - headline khớp ad/email đã dẫn traffic.
7. **Popup/signup (nếu có)** - timing, giá trị đổi lấy email, dễ đóng.

## Đầu ra

Lưu `exports/marketing/<slug>/cro-audit.md`:

- Tóm tắt giả thuyết (1-3)
- Bảng: vấn đề | mức impact | effort | sửa đề xuất
- Top 5 việc làm trước
- Nếu cần dựng lại trang → bàn giao `landing-page`; SEO on-page → `kiem-tra-seo` / `seo-gpt`

## Không làm

- Không tự publish / chạy A/B trên ads trừ khi user lệnh rõ + MCP.
- Không thay `landing-page` (dựng HTML) - skill này audit + brief.

## Nguồn

Rút gọn VI từ [marketingskills/cro](https://github.com/coreyhaines31/marketingskills) (+ gợi ý signup/popups) (MIT).
