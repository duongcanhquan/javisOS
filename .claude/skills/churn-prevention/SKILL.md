---
name: Churn prevention
description: "Giữ khách SaaS: cancel flow, save offer, dunning, tín hiệu rủi ro. Draft kế hoạch - không tự đổi billing."
description_en: "SaaS retention: cancel flow, save offers, dunning, risk signals. Plan drafts only - no billing changes."
group: Marketing
license: MIT
metadata:
  version: "1.0"
  upstream: "https://github.com/coreyhaines31/marketingskills/tree/main/skills/churn-prevention"
---

# Churn prevention

## Khi nào dùng

Churn cao, cancel flow yếu, thanh toán fail, cần save offer / dunning / health score.

## Chuẩn bị

Hỏi/đọc: churn hiện tại (%), lý do hủy phổ biến, billing (Stripe…), dữ liệu usage. Thiếu số → nêu giả định rõ, không bịa %.

## Cách chạy

1. **Cancel flow:** survey ngắn → save offer động (giảm giá / pause / downgrade) → xác nhận hủy.
2. **Proactive:** tín hiệu rủi ro (login giảm, feature core không dùng, support ticket) → can thiệp trước khi hủy.
3. **Involuntary:** dunning email + smart retry; tách churn chủ động / thanh toán fail.
4. Xuất: checklist cancel UI + bảng offer + chuỗi email dunning (draft).
5. Metrics: logo churn, revenue churn, save rate, recovery rate.

## Bẫy

- Không tự đổi subscription / charge thẻ.
- Không dark pattern chặn hủy.
- Không em dash.

## Kiểm chứng

- [ ] Có luồng cancel + ít nhất 1 save offer
- [ ] Tách churn chủ động vs thanh toán
- [ ] Draft đo lường rõ
