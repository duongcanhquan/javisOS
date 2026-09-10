# Design catalog - chọn lọc layout

Chọn **2–3** option khớp brief. Không dump cả bảng cho user trừ khi họ hỏi «còn kiểu nào».

Cảm hứng: SaaS landing kiểu Simple Light (sáng, hero + features + social + CTA).
Mã trong `assets/` là template Javis, không phải bản sao Cruip.

## Catalog

| id | Tên | Khi dùng | Tránh khi |
|----|-----|----------|-----------|
| `simple-light` | Simple Light | SaaS / tool / app B2B-B2C, cần trang chuẩn đủ section | Cần tối / luxury nặng |
| `dark-product` | Dark Product | Devtool, AI, sản phẩm «tech» | Dịch vụ địa phương ấm |
| `founder-story` | Founder Story | Personal brand, coach, studio sáng tạo | Nhiều gói giá phức tạp |
| `course-offer` | Course / Offer | Khoá học, cohort, offer có giá + chương trình | Chỉ thu email waitlist |
| `local-service` | Local Service | Spa, phòng khám, sửa chữa, quán - CTA gọi/Zalo | SaaS global |
| `waitlist` | Waitlist Minimal | Prelaunch, 1 promise + form email | Cần giáo dục sản phẩm dài |

## Token gợi ý (đổi theo brand)

| id | Nền | Ink | Accent | Font display / body |
|----|-----|-----|--------|---------------------|
| `simple-light` | `#ffffff` / `#f8fafc` | `#0f172a` | `#4f46e5` indigo | Inter / Inter |
| `dark-product` | `#0b1220` | `#e2e8f0` | `#22d3ee` cyan | Space Grotesk / Inter |
| `founder-story` | `#faf7f2` | `#1c1917` | `#b45309` amber | Fraunces / Source Sans |
| `course-offer` | `#fff` / `#fef3c7` soft | `#111827` | `#dc2626` | DM Sans / DM Sans |
| `local-service` | `#f0fdf4` | `#14532d` | `#059669` | Be Vietnam Pro / same |
| `waitlist` | `#fafafa` | `#171717` | `#2563eb` | Inter / Inter |

Font: ưu tiên Google Fonts link trong `<head>`. Nếu offline / API engine: stack
`system-ui, sans-serif` vẫn chấp nhận được.

## Cách đề xuất (mẫu)

> Brief là SaaS lịch hẹn cho spa. Mình đề xuất:
> 1. **simple-light** (khuyến nghị) - đủ features + social, dễ tin
> 2. **local-service** - nhấn CTA Zalo/gọi nếu khách chủ yếu tại chỗ
> 3. **waitlist** - chỉ khi chưa mở bán

Rồi `JAVIS_ASK` hoặc chờ user chọn.

## Sau khi chọn

Ghi vào `BRIEF.md`: `layout: <id>`. Build theo `build-html.md` - starter mặc định
bám `simple-light`; layout khác = đổi token + bật/tắt section (ẩn pricing nếu không có,
đổi hero 1 cột cho waitlist, v.v.).
