# Build HTML

## Nguồn

1. Đọc `assets/starter-simple-light.html` (template MIT của skill).
2. Ghi ra `exports/landing/<slug>/index.html` (không sửa file trong skill).
3. Thay toàn bộ copy từ `COPY.md`; áp token từ layout đã chọn.

## Stack bắt buộc (chế độ mặc định)

- Một file HTML (hoặc HTML + `assets/` ảnh local trong cùng folder).
- Tailwind qua CDN Play (`https://cdn.tailwindcss.com`) **hoặc** CSS utility đã viết tay
  nếu môi trường cấm CDN - ghi chú trong chat nếu dùng bản không CDN.
- Không React/Next ở chế độ mặc định.
- `lang` đúng ngôn ngữ; charset UTF-8; viewport; title + meta description.

## Section tối thiểu (simple-light)

1. Skip link / nav sticky
2. Hero
3. Logo strip (có thể rút nếu không có logo)
4. Features (grid 3)
5. How it works
6. Testimonial
7. Final CTA
8. Footer

Bật thêm theo layout: pricing (`course-offer`), form email (`waitlist`),
khối «gọi ngay» (`local-service`), narrative dài (`founder-story`).

## Checklist trước khi giao

- [ ] Không còn chữ mẫu «Acme», «Lorem», «Your Company»
- [ ] CTA `href` thật hoặc `#lead` / `mailto:` / Zalo đã thống nhất với brief
- [ ] Contrast chữ/nền đủ đọc (tránh xám nhạt trên trắng)
- [ ] Ảnh có `alt`; icon trang trí `aria-hidden="true"`
- [ ] `prefers-reduced-motion`: animation nhẹ hoặc tắt
- [ ] File path vault-relative khi nhúng trong chat

## Sửa vòng 2

User bảo «đổi hero / thêm FAQ / đổi màu» → sửa `index.html` (+ `COPY.md` nếu đổi chữ),
không tạo slug mới trừ khi họ xin bản song song.
