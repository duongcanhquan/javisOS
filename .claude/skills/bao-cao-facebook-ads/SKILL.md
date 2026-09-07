---
name: Báo cáo Facebook Ads
description: "Báo cáo Meta Ads đầy đủ số đo: spend, CTR, CPC, CPM, reach, campaign; diễn giải dễ hiểu."
group: Marketing
---

# Báo cáo Facebook Ads

## Khi nào dùng

User muốn **báo cáo quảng cáo Facebook/Instagram** có số đo thật, bảng chiến dịch, và phần giải thích dễ hiểu (không chỉ dump JSON).

## Chuẩn bị

1. Connector Store **`meta-ads-graph`** phải đã đăng nhập. Kiểm bằng `javis_connections` / thử `meta_ads_accounts`.
2. Thiếu → nói rõ vào **Kết nối / Store → Meta Ads (Graph API)**; **không bịa số**.
3. Kỳ mặc định: `last_7d`. Brief có thể ghi `last_14d` / `last_30d` / `this_month` hoặc `since`+`until` (YYYY-MM-DD).

## Quy trình lấy số (bắt buộc gọi tool)

1. `meta_ads_accounts` - liệt kê ad account (tên, currency, amount_spent).
2. Chọn account (theo brief hoặc account đầu tiên nếu chỉ có 1).
3. `meta_ads_insights` - `level=account`, `date_preset` theo brief.
4. `meta_ads_insights` - `level=campaign` cùng kỳ (bảng từng chiến dịch).
5. `meta_ads_campaigns` - trạng thái, objective, ngân sách.
6. (Tuỳ chọn) `meta_ads_get` path `act_…/insights` với `level=ad` nếu user cần xuống từng ad; hoặc so kỳ trước (`last_7d` vs `previous` bằng since/until) khi brief yêu cầu so sánh.

Số đo lấy từ API (và giải thích trong báo cáo):

| Field | Ý nghĩa dễ hiểu |
|-------|-----------------|
| spend | Tiền đã chi (đúng currency account) |
| impressions | Lượt hiển thị |
| reach | Số người đã thấy (ước) |
| frequency | Trung bình 1 người thấy bao nhiêu lần |
| clicks | Click (link/all tùy Meta trả) |
| ctr | % click / hiển thị |
| cpc | Chi phí mỗi click |
| cpm | Chi phí mỗi 1000 hiển thị |
| actions / action_values | Chuyển đổi (lead, purchase…) nếu có - **chỉ ghi loại Meta trả về** |

## Định dạng báo cáo (bắt buộc)

Viết tiếng Việt, đoạn ngắn, bảng markdown. Cấu trúc:

```
# Báo cáo Facebook Ads - <tên account>
Kỳ: <preset hoặc since→until> | Tiền tệ: <VND/USD…> | Lấy lúc: <ISO hoặc giờ VN>

## 1. Tóm tắt tình hình (đọc 30 giây)
3-5 câu người không chuyên ads cũng hiểu: đang chi bao nhiêu, kết quả chính, tốt/yếu gì.

## 2. Số đo tổng (account)
| Chỉ số | Giá trị | Diễn giải ngắn |
| spend | … | …
| impressions | … | …
| reach | … | …
| frequency | … | …
| clicks | … | …
| CTR | …% | …
| CPC | … | …
| CPM | … | …
| Chuyển đổi (nếu có) | loại = số | …

## 3. Chiến dịch
Bảng: Tên | Trạng thái | Mục tiêu | Ngân sách | Spend kỳ | Impression | Click | CTR | CPC | Nhận xét 1 dòng
Sắp xếp spend giảm dần. Chiến dịch ACTIVE nổi bật; PAUSED ghi rõ.

## 4. Đọc số như thế nào
- Frequency cao (>3) → có thể đang đụng cùng người nhiều lần.
- CTR thấp so mặt bằng ngành (nêu là ước/giả định nếu không có benchmark nội bộ) → creative/targeting yếu.
- CPC/CPM tăng → cạnh tranh hoặc audience hẹp.
Chỉ khẳng định khi có số; không bịa benchmark.

## 5. Việc nên làm (3-5 gợi ý)
Cụ thể, ưu tiên: tắt/giữ/điều chỉnh ngân sách, test creative, siết audience - **không tự sửa ads**.

## 6. Nguồn
Ghi tool đã gọi + account_id + date_preset/time_range.
```

Lưu: `exports/marketing/<slug>/bao-cao-ads.md`.

## Kiểm chứng

Có bảng số tổng + ít nhất 1 bảng campaign (hoặc giải thích account không có campaign). Có mục «Tóm tắt tình hình». Không có số nào không đến từ tool.
