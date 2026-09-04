---
name: pixcelvideo
description: "Video đầy đủ bắt buộc có ảnh từng cảnh (ChatGPT/Pollinations) + TTS; không trả bản chỉ chữ."
description_en: "Full video requires per-scene images (ChatGPT/Pollinations) + TTS; never text-only."
group: Nội dung
---

# pixcelvideo — bắt buộc có ảnh

## Tool mặc định

`javis_render_script_video` với `with_images=true` + `require_images=true`:

1. Mỗi cảnh tạo **ảnh** (ưu tiên ChatGPT OAuth; không có thì Pollinations)
2. Edge-TTS + chữ overlay
3. Ghép mp4 — **nếu thiếu ảnh bất kỳ cảnh → ERROR**, không trả video chữ trơn

```
javis_render_script_video(
  script="Hook\n\nÝ 2\n\nCTA",
  title="...",
  aspect="portrait",
  with_images=true,
  require_images=true
)
```

## Pixelle

`javis_pixelle_generate` khi có RunningHub. Lỗi → fallback tool trên (vẫn có ảnh).

## Cấm

- Không gọi với `with_images=false` trừ khi user bảo rõ “chỉ chữ / không cần ảnh”.
- Không báo “đã có video đầy đủ” khi `images` = 0.
