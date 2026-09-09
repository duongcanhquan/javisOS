# Brief postcard video

Bổ sung cho `lam-video/references/brief-checklist.md` khi pipeline = `postcard-video`.

## Mẫu

```
Chủ đề:
Mục tiêu: (nhận diện | launch | demo tính năng | bán)
Audience:
Độ dài: (15s | 30s | 45s)   # mặc định 30s; >60s phải xác nhận
Tỉ lệ: (9:16 | 1:1 | 16:9)
Ngôn ngữ chữ trên hình:
Kênh:
CTA:
Tone / vibe: (cinematic | sạch | playful | …)
Pipeline: postcard-video
URL sản phẩm / staging:
Screenshot sẵn: (không | đường dẫn…)
Mode shotcraft: (template Ink Press | tự do | cùng sáng tạo)
Voice: (không | file VO sẵn: …)   # không có TTS mặc định
Cấm / brand:
```

## Bắt buộc riêng postcard

- URL hoặc bộ screenshot thật (không bịa UI).
- Độ dài trong 15-45s hoặc xác nhận vượt trần.
- Mode shotcraft (một trong ba).

## Đầu ra mong đợi

1. Storyboard / shot list (tên recipe card nếu dùng).
2. Remotion project chạy được `npx remotion render …`.
3. `final.mp4` (+ bản no-BGM nếu có nhạc).
4. Vài frame QA (still) các shot quan trọng.
