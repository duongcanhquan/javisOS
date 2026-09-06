---
name: Tạo ảnh minh họa
description: "Viết prompt có cấu trúc rồi gọi javis_generate_image cho poster, cảnh video hoặc hình proposal."
description_en: "Build structured prompts and call javis_generate_image for posters, video scenes, or proposal visuals."
group: Nội dung
---

# Tạo ảnh minh họa

## Khi nào dùng

User / agent cần **ảnh minh họa** cho poster, từng cảnh video, bìa/infographic proposal, rồi ghép vào sản phẩm. Không dùng khi chỉ cần mô tả ảnh bằng chữ.

## Chuẩn bị

1. Chốt **chế độ**: `poster` | `video-scene` | `proposal`.
2. Chốt brief tối thiểu: chủ đề, audience, thông điệp/ chữ trên ảnh (nếu có), tỉ lệ.
3. ChatGPT OAuth đã kết nối (tool `javis_generate_image`). Chưa có → nói rõ cách bật ở Models, không giả vờ đã gen.
4. Đọc `references/che-do.md` khi chọn style / bố cục.

## Cách chạy

### 1. Viết prompt theo khối (bắt buộc)

```
Subject: ...
Layout: ...
Style: ...
Text on image: "..." (đúng chữ user; không bịa slogan)
Aspect: square | landscape | portrait
Constraints: no watermark, readable text, ...
Negative: clutter, extra fingers, wrong logo, ...
```

Rút style từ `references/che-do.md`. Giữ cấu trúc khối; không nhồi cả thư viện case.

### 2. Gọi tool

`javis_generate_image` với:

- `prompt` = bản đã ghép từ các khối (một đoạn rõ ràng)
- `aspect_ratio` = square | landscape | portrait
- `quality` = medium (mặc định) hoặc high khi user cần in / pitch
- `images` = đường dẫn ảnh mẫu trong brain nếu user gửi tham chiếu (tối đa 4)

### 3. Nhúng ngay

Sau khi tool trả `attachments/...`, **bắt buộc** nhúng:

`![mô tả ngắn](attachments/...)`

Kèm 1 dòng: chế độ + tỉ lệ + chữ đã lock trên ảnh.

## Quy trình theo chế độ

### poster

- 1 ảnh chính (thêm biến thể chỉ khi user xin).
- Portrait cho story/A4 dọc; landscape cho banner; square cho feed.
- Text on image phải **đúng** headline/CTA user chốt; thiếu chữ bắt buộc → hỏi trước khi gen.

### video-scene

- Mỗi beat/scene một prompt + một ảnh (trừ scene-only-text).
- Aspect theo tỉ lệ video (9:16 → portrait, 16:9 → landscape).
- Giữ **cùng style bible** xuyên suốt các cảnh (palette, lighting, medium).
- Trả bảng: `scene_id | path | prompt ngắn`.

### proposal

- Tối thiểu: 1 ảnh bìa + 1 hình giải thích (funnel / positioning / timeline / so sánh).
- Landscape ưu tiên trang slide/PDF; chữ trên ảnh ít, ưu tiên số/nhãn đọc được.
- Trả danh sách path để bước soạn proposal nhúng vào markdown.

## Bẫy

- Gen khi chưa chốt chữ trên poster → sai CTA, phải gen lại tốn quota.
- Mỗi cảnh video một style khác nhau → video rời rạc.
- Proposal chỉ có ảnh trang trí, không có hình mang insight.
- Tả lại ảnh mẫu bằng lời thay vì truyền `images`.
- Dùng em dash trong prompt hoặc báo cáo.

## Kiểm chứng

- Có file `attachments/...` thật và đã nhúng markdown.
- Đúng chế độ + aspect đã chốt.
- Chữ trên ảnh (nếu có) khớp brief.
- Chưa kết nối ChatGPT thì đã nói cách bật, không bịa path ảnh.
