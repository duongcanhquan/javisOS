---
name: Tổng kết Facebook
description: "Tóm tắt Page/Ads Facebook đã kết nối: bài đăng, bình luận nổi bật, insights; nêu nếu thiếu MCP."
group: Marketing
---

# Tổng kết Facebook

## Khi nào dùng

User muốn xem **trạng thái kết nối Facebook** và **tổng kết hoạt động** (bài đăng, ads) trong kỳ.

## Chuẩn bị

1. Gọi `javis_connections` (hoặc tương đương) để xem connector nào đang có:
   - `facebook-pages` → tool `fb_pages_list`, `fb_page_posts`, …
   - `meta-ads-graph` → `meta_ads_accounts`, `meta_ads_insights`, `meta_ads_campaigns`
   - `facebook-monitor` → `fb_monitor` (page/group công khai)
2. Thiếu connector → nói rõ cần cài gói nào trên trang MCP/Store; hỏi có muốn tạo checklist kết nối không. **Không bịa số.**

## Quy trình khi đã kết nối

1. Brief: kỳ (7 ngày / 30 ngày), Page nào, có xem Ads không.
2. Liệt kê Page/ad account thật từ tool.
3. Lấy bài đăng gần đây + (nếu có) insights campaigns.
4. Tổng kết: chủ đề đăng, tương tác nổi bật, ads đang chạy / tốn kém (số thật), 3 gợi ý nội dung tuần tới.
5. Lưu `exports/marketing/<slug>/facebook-tong-ket.md`.

## An toàn

Mặc định **chỉ đọc**. Không đăng/xóa/sửa post trừ khi user yêu cầu rõ ràng và chế độ cho phép.
