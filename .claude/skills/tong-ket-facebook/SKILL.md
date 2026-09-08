---
name: Tổng kết Facebook Page
description: "Báo cáo Page Facebook: kết nối, bài đăng kỳ, tương tác; checklist nội dung tuần tới."
description_en: "Facebook Page report: connection, period posts, engagement; next-week content checklist."
group: Marketing
---

# Tổng kết Facebook Page (organic)

## Khi nào dùng

User muốn xem **Page đã kết nối**, bài đăng trong kỳ, tương tác - **không** thay báo cáo Ads (dùng skill `bao-cao-facebook-ads`).

## Chuẩn bị

1. Connector **`facebook-pages`** (`fb_pages_list`, `fb_page_posts`, `fb_page_comments`).
2. Thiếu → hướng dẫn Store/Kết nối. Không bịa số.
3. (Tuỳ) `facebook-monitor` để soi page công khai đối thủ.

## Quy trình

1. Brief: kỳ (7/14/30 ngày), Page nào nếu nhiều.
2. `fb_pages_list` → chọn Page.
3. `fb_page_posts` kỳ gần đây (giới hạn hợp lý, vd 20-30 bài).
4. Với 1-3 bài nổi bật: `fb_page_comments` nếu cần cảm xúc cộng đồng.
5. Báo cáo dễ hiểu:

```
# Tổng kết Facebook Page - <tên>
Kỳ: …

## Tình hình nhanh
3-5 câu: đăng bao nhiêu bài, chủ đề chính, bài nào nổi.

## Bảng bài đăng
| Ngày | Tóm tắt nội dung | Ghi chú tương tác (nếu có) |

## Chủ đề / góc nội dung
## Việc tuần tới (3 gợi ý caption/ý tưởng)
## Nguồn (tool + page_id)
```

6. Lưu `exports/marketing/<slug>/facebook-page.md`.

## An toàn

Chỉ đọc. Không đăng/sửa/xoá trừ khi user yêu cầu rõ và quyền cho phép.
