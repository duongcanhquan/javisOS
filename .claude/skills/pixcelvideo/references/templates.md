# Template & tỉ lệ Pixelle

Template nằm dưới `templates/<WxH>/` trong repo Pixelle. Path đưa vào
`frame_template` dạng `"1080x1920/image_default.html"`.

## Chọn theo tỉ lệ

| Tỉ lệ | Thư mục | Dùng cho |
|-------|---------|----------|
| 9:16 | `1080x1920/` | Reels, TikTok, Shorts |
| 16:9 | `1920x1080/` | YouTube ngang |
| 1:1 | `1080x1080/` | Feed vuông |

## Loại template (theo tên file)

| Prefix | Ý nghĩa |
|--------|---------|
| `image_*` | Cần AI gen ảnh từng cảnh |
| `video_*` | Cần AI gen video clip |
| `static_*` | Ít/không media AI (layout chữ) |

Mặc định an toàn: **`1080x1920/image_default.html`**.

Khác thường gặp (README/config): `image_modern.html`, `image_elegant.html`,
`image_film.html` (ngang), `static_simple.html`, `image_minimal_framed.html` (vuông).

Liệt kê chính xác trên máy user: xem thư mục `templates/` của bản Pixelle họ cài,
hoặc API templates nếu server expose.

## Style ảnh

Dùng `prompt_prefix` (tiếng Anh), ví dụ:

- `Minimalist black-and-white matchstick figure style illustration, clean lines`
- `Cinematic photo, natural light, shallow depth of field`
- `Flat vector infographic, bold shapes, limited palette`

Không nhồi brand cấm vào prefix nếu user đã ghi “cấm …”.
