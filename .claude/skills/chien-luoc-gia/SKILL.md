---
name: Chiến lược giá
description: "Chiến lược giá & packaging (metric, tier, trial); neo tài chính MKT nếu có số."
description_en: "Pricing & packaging strategy (metric, tiers, trial); anchor finance-MKT skill when numbers exist."
group: Marketing
---

# Chiến lược giá & packaging

Thiết kế giá / gói / trial / freemium khớp value metric và willingness-to-pay.

## When to use

- Pricing page, tăng giá, đổi tier, freemium vs trial, per-seat vs usage.
- Audit trang giá (người đọc + AI đọc được plan).
- Offer/bonus/guarantee ngắn: gộp vào mục Offer bên dưới (không tách skill).

## Trước khi đề xuất

1. Đọc `product-marketing-context` nếu có.
2. Loại SP, giá hiện tại, ICP, GTM (self-serve / sales), đối thủ, mục tiêu (growth vs margin).
3. Có số thật (ARPU, churn, conversion) → nạp `phan-tich-tai-chinh-mkt` nếu phù hợp; **không bịa**.

## Khung quyết định

- **Value metric** - khách trả theo gì (seat, usage, outcome).
- **Good-better-best** - 3 tier rõ khác biệt; neo mid-tier nếu phù hợp.
- **Trial / freemium** - mục tiêu học sản phẩm vs thu lead; thời hạn / giới hạn rõ.
- **Annual vs monthly** - incentive hợp lý, không ép.
- **Offer** - bonus, guarantee, scarcity chỉ khi trung thực.

## Pricing page (checklist nhanh)

- Ai nên chọn gói nào trong 10 giây.
- Feature so sánh scannable; CTA theo tier.
- FAQ giá / hủy / thuế nếu liên quan.
- (Tuỳ) cấu trúc để AI/agent đọc được plan - gắn `seo-gpt` nếu user cần.

## Đầu ra

`exports/marketing/<slug>/pricing.md`: giả thuyết, bảng tier đề xuất, rủi ro, câu hỏi còn mở với user.

## Nguồn

Rút gọn VI từ [marketingskills/pricing](https://github.com/coreyhaines31/marketingskills) (+ offers gọn) (MIT).
