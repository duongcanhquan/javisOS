# Tạo video: thời lượng kéo + slide + yêu cầu theo kiểu

## Mục tiêu

Trên trang **Công việc → Tạo video**, mỗi tab kiểu video có thêm:

1. **Thanh kéo thời lượng** (giây) tới **tối đa 10 phút** (600s), không còn select cố định 15–90s.
2. **Số lượng slide / cảnh / shot** theo kiểu (nhãn và khoảng min–max khác nhau).
3. **Khối yêu cầu riêng** theo pipeline (nhạc, giọng đọc, kiểu giấy, phong cách đồ họa…).

## Hành vi

- Đổi tab: giữ draft chung; clamp thời lượng + số slide vào khoảng của kiểu mới; extras theo kiểu mới (giữ nếu cùng `id`).
- Brief gửi workflow ghi rõ: độ dài (chuỗi kiểu `2 phút 30 giây` / `45 giây`), số slide, và từng extras.
- Gợi ý khuyến nghị vẫn hiện dưới thanh kéo (vd promo 15–45s) nhưng không khóa max.

## Phạm vi

Chỉ UI + brief; không đổi engine Remotion/upstream trong PR này.

## Bổ sung 0.55.173 - tận dụng catalog

| Tab | Pipeline | Năng lực đưa lên form |
|-----|----------|------------------------|
| Promo cinematic | postcard-video | 3 mode, nhóm 157 shot, card name, capture 2x, cam energy, BGM đôi bản, beat-sync, SFX, workbench, Jianying |
| Có lời đọc | pixcelvideo | nguồn ảnh, require images, Pixelle, Edge-TTS, cấu trúc Hook→CTA |
| Collage Vox | paperdesign | 9 theme, arc, motion, voice xAI/vi, caption, music prompt, C/A-roll, res, duyệt beat |
| Đồ họa Remotion | remotion | kind data/UI/captions/maps, fps, transparent, Studio |
| HTML kinetic | html-video | template, kinetic, brand tokens, html-still, Ommi local |
| Javis chọn | auto | ưu tiên + tránh pipeline theo catalog |

Chung: CTA, cấm/brand, chip `caps` dưới brief.
