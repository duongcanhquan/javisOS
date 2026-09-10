---
name: Marketing (điều phối)
description: "Điều phối Marketing: SEO+SEO GPT, nghiên cứu, Page Facebook, báo cáo Ads đủ số đo."
description_en: "Marketing hub: SEO+SEO GPT, research, Facebook Page, Ads reports with full metrics."
group: Marketing
---

# Marketing - điều phối

## Khi nào dùng

Trang **Công việc → Marketing**, hoặc chat/Telegram/Zalo: kiểm SEO, viết SEO, nghiên cứu, Page FB, báo cáo Ads.

## Menu chọn

| Chọn | Khi nào | Ví dụ | Workflow |
|------|---------|-------|----------|
| **Kiểm SEO** | URL/bản nháp: SEO web + **SEO GPT** (LLM trích dẫn) | Landing thiếu lead trả lời thẳng + meta | `bo-marketing-kiem-seo` |
| **Viết bài SEO** | Bài web + meta + FAQ/chunk cho chat AI | «học vẽ online Hà Nội» có lead + FAQ | `bo-marketing-viet-seo` |
| **Landing page** | Trang giới thiệu / sales HTML từ brief hoặc chủ đề | SaaS, khoá học, waitlist → `exports/landing/` | Skill **`landing-page`** (không workflow riêng) |
| **Nghiên cứu thị trường** | Trước ads/content | Phân khúc + đối thủ | `bo-marketing-nghien-cuu` |
| **Page Facebook** | Bài đăng organic, lịch nội dung | Tuần này Page đăng gì | `bo-marketing-facebook` |
| **Báo cáo Ads** | Số đo spend/CTR/CPC + bảng campaign | Ads 7 hoặc 30 ngày | `bo-marketing-ads` |

Skills SEO: luôn nạp **`seo-gpt`** cùng `kiem-tra-seo` / `viet-bai-seo`. Không chỉ tối ưu Google.
Landing xong cần SEO audit URL/file → **Kiểm SEO**; cần `.pke` → **`html-to-webcake`**.

Chat: nếu user nói chung «Facebook» → hỏi Page hay Ads (JAVIS_ASK, ≤4 lựa chọn gộp SEO/viết/nghiên cứu/FB rồi tách FB).

## Chuẩn bị

- Seed **Bộ Marketing** / Chuẩn bị lần đầu.
- Agents: Gemini. Ads: `meta-ads-graph`. Page: `facebook-pages`.
- File: `exports/marketing/`.

## Bẫy

Không bịa số ads/ranking. Không tự sửa chiến dịch. Không em dash.
