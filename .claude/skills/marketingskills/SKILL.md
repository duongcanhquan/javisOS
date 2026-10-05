---
name: Marketing Skills (Corey Haines)
description: "Bộ marketing MIT: CRO, copy, SEO, ads, email, launch, giá, churn, A/B - map sang skill Javis."
description_en: "MIT marketing suite hub: CRO, copy, SEO, ads, email, launch, pricing, churn, A/B - maps to Javis skills."
group: Marketing
license: MIT
metadata:
  version: "1.0"
  upstream: "https://github.com/coreyhaines31/marketingskills"
---

# Marketing Skills (hub)

## Dùng để làm gì

Điều phối bộ kỹ năng marketing từ
[coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) (MIT)
sang skill Javis sẵn có hoặc skill bổ sung. **Không clone cả repo vào vault.**

## Khi nào dùng

- «dùng marketingskills», «bộ Corey Haines», «CRO / cold email / churn / A/B / lead magnet»
- User hỏi rộng «marketing giúp gì» mà chưa chỉ skill cụ thể

**Không dùng** khi đã rõ một skill Javis (vd chỉ viết email → `viet-email-marketing`).

## Map nhanh (ưu tiên skill Javis)

| Việc | Skill Javis | Ghi chú upstream |
|------|-------------|------------------|
| CRO / landing convert | `toi-uu-chuyen-doi-cro` | cro |
| Copy hero/CTA | `viet-copy-marketing` | copywriting, copy-editing |
| Email nurture / welcome | `viet-email-marketing` | emails |
| Cold email B2B | `cold-email-b2b` | cold-email |
| SEO audit / viết SEO | `kiem-tra-seo` + `seo-gpt` / `viet-bai-seo` | seo-audit, ai-seo, programmatic-seo |
| Ads đa kênh | `quang-cao-da-kenh` | ads, ad-creative |
| Launch / GTM | `ra-mat-san-pham` | launch |
| Giá / packaging | `chien-luoc-gia` | pricing, offers, paywalls |
| Kế hoạch MKT | `ke-hoach-marketing` | marketing-plan |
| Context sản phẩm / ICP | `product-marketing-context` | product-marketing |
| Churn / giữ khách | `churn-prevention` | churn-prevention |
| A/B test MKT | `ab-testing-marketing` | ab-testing |
| Lead magnet | `lead-magnets` | lead-magnets |
| Menu tổng | `marketing-hub` | - |

Chi tiết đủ 50 slug: `references/catalog.md`.

## Cách chạy

1. Đọc brief user → chọn **một** hàng trong bảng trên.
2. Nạp skill Javis tương ứng (không dump cả catalog).
3. Nếu thiếu context sản phẩm → nạp `product-marketing-context` trước.
4. Báo cáo ngắn: skill đã dùng + đầu ra (file/exports).

## Bẫy

- Không `git clone` cả marketingskills vào brain.
- Không bịa số ads/ranking. Không tự bật chiến dịch / blast email.
- Không em dash.
- Skill upstream description dài - Javis dùng description ≤150; trigger đầy đủ ở thân skill.

## Kiểm chứng

- [ ] Đã chọn đúng 1 skill Javis (không mở 5 skill cùng lúc)
- [ ] Có `upstream` khi trích khung từ bộ Corey
- [ ] Đầu ra nằm `exports/marketing/` hoặc wiki khi user yêu cầu lưu
