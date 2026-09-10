# Intake - chuẩn hoá brief landing

## Mục tiêu

Ra một `BRIEF.md` đủ để chọn layout và viết copy, không hỏi lan man.

## Hai chế độ vào

### A. Brief đầy đủ

User đã đưa sản phẩm, đối tượng, lợi ích, CTA, ràng buộc. Chỉ hỏi lại nếu thiếu
**một** trong các mục bắt buộc dưới đây mà không đoán được an toàn.

### B. Chỉ chủ đề / vài dòng

AI tự draft toàn bộ; ghi rõ **Giả định:** trong `BRIEF.md` và nhắc 1 câu trong chat.
Chỉ hỏi khi đoán sai sẽ hại: giá bán, claim pháp lý, tên thương hiệu chính thức, ngôn ngữ.

## Trường bắt buộc (điền hoặc giả định)

```markdown
# BRIEF — <tên dự án>

- **Slug:** <ascii-kebab>
- **Sản phẩm / dịch vụ:**
- **Đối tượng (1 câu):**
- **Job-to-be-done:**
- **Promise chính (1 câu):**
- **CTA chính:** (chữ nút + URL hoặc #lead)
- **Ngôn ngữ trang:**
- **Tone:** (vd tin cậy / năng động / cao cấp)
- **Ràng buộc:** (không dùng từ X, không cam kết Y, thị trường VN…)
- **Giả định:** (liệt kê nếu chế độ B)
```

## Trường nên có (nếu biết)

- 3–5 lợi ích / tính năng
- Social proof (tên khách, số liệu thật - không bịa)
- Phân biệt với đối thủ (1 câu)
- Palette / logo path trong vault
- Section bắt buộc / cấm (vd bắt buộc FAQ, cấm countdown giả)

## Output bước này

Ghi `exports/landing/<slug>/BRIEF.md`. Sang `copy-framework.md` rồi
`design-catalog.md` - **chưa** viết HTML.
