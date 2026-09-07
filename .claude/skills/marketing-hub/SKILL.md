---
name: Marketing (điều phối)
description: "Điều phối Marketing: kiểm SEO, viết bài SEO, nghiên cứu thị trường, tổng kết Facebook/Ads."
group: Marketing
---

# Marketing - điều phối cho giảng viên / marketer

## Khi nào dùng

- User muốn làm việc Marketing từ chat, Telegram, Zalo, hoặc trang **Công việc → Marketing**.
- Cần chọn đúng đầu ra: kiểm SEO / viết bài SEO / nghiên cứu thị trường / tổng kết Facebook.

## Menu chọn (nói rõ + ví dụ)

| Chọn | Khi nào | Ví dụ | Workflow |
|------|---------|-------|----------|
| **Kiểm SEO** | Có URL hoặc bản nháp cần soi kỹ thuật + nội dung | `https://truong.edu.vn/khoa-hoc` thiếu meta | `bo-marketing-kiem-seo` |
| **Viết bài SEO** | Cần bài đăng web có từ khóa, H1-H2, CTA | «học vẽ online Hà Nội» 1200 chữ | `bo-marketing-viet-seo` |
| **Nghiên cứu thị trường** | Hiểu phân khúc, đối thủ, insight trước khi chạy ads | Trường nghệ thuật vs đối thủ địa phương | `bo-marketing-nghien-cuu` |
| **Tổng kết Facebook** | Xem Page/Ads đã đấu, tóm tắt bài đăng & hiệu suất | «Tuần này Page đăng gì, ads nào chạy» | `bo-marketing-facebook` |

Hỏi bằng JAVIS_ASK (tối đa 4 lựa chọn) nếu user chưa chọn.

## Chuẩn bị

- Seed: Studio → **Bộ Marketing** hoặc trang Marketing → **Chuẩn bị lần đầu**.
- Agent seed dùng **Gemini** (`model_provider: gemini`).
- Facebook/Ads: cần connector Store `facebook-pages` / `meta-ads-graph` / `facebook-monitor`. Thiếu thì nói rõ, không bịa số.
- SEO URL: dùng WebFetch/WebSearch khi engine có; không có thì yêu cầu user dán HTML/text.

## Lộ trình chung

1. Chốt brief (mục tiêu, đối tượng, URL/từ khóa, kỳ thời gian).
2. Research / đọc nguồn (skill `deep-research` hoặc MCP Meta).
3. Viết ví dụ / checklist hành động.
4. Ghi `exports/marketing/<slug>/`.
5. Trả đường dẫn + 1-3 việc nên làm tiếp.

## Kênh

Cùng agent/workflow chạy trên dashboard, Telegram, Zalo - không cần flow riêng. Chỉ gửi tin Zalo/Telegram khi user yêu cầu rõ.

## Bẫy

- Không bịa traffic, ranking, chi phí ads.
- Không đăng bài Page / sửa ads trừ khi user yêu cầu rõ và quyền `full`.
- Không em dash.
