# Brief — pixcelvideo / Pixelle

Thiếu mục **bắt buộc** → DỪNG và hỏi. Không gọi API Pixelle khi chưa chốt.

## Mẫu nhanh

```
Chủ đề:
Mục tiêu: (giáo dục | bán | nhận diện | viral | giải trí)
Độ dài: (15s | 30s | 60s | khác → ước n_scenes)
Tỉ lệ: (9:16 → 1080x1920 | 16:9 → 1920x1080 | 1:1 → 1080x1080)
Ngôn ngữ VO:
Tone / style ảnh: (1 cụm tiếng Anh cho prompt_prefix)
Template: (để trống = image_default theo tỉ lệ)
CTA:
Pixelle URL: (http://…:8000 hoặc WebUI :8501)
```

## Bắt buộc

| Mục | Ghi chú |
|-----|---------|
| Chủ đề | Một câu rõ |
| Mục tiêu | Quyết định hook + CTA |
| Độ dài / n_scenes | Map sang số cảnh |
| Tỉ lệ | Chọn thư mục template |
| Ngôn ngữ | Narration viết đúng ngôn ngữ này |

## Nên có

- Tone / `prompt_prefix` (style ảnh)
- Template cụ thể (`references/templates.md`)
- BGM / giọng TTS / voice clone
- `PIXELLE_API_BASE` hoặc xác nhận user tự chạy WebUI
