---
name: pixcelvideo
description: "Short video đầy đủ: ảnh AI từng cảnh (ChatGPT) + TTS + mp4; Pixelle nếu có RunningHub."
description_en: "Full short video: AI image per scene (ChatGPT) + TTS + mp4; Pixelle if RunningHub set."
group: Nội dung
---

# pixcelvideo — video có ảnh + giọng (đầy đủ)

## Đường mặc định (đảm bảo có ảnh)

Tool **`javis_render_script_video`** với `with_images: true` (mặc định):

1. Viết / duyệt kịch bản (mỗi cảnh một đoạn)
2. Gọi tool — mỗi cảnh: **ảnh AI ChatGPT** + Edge-TTS + chữ overlay → ghép mp4
3. Cần đã đăng nhập **ChatGPT** ở trang Model (OAuth). Chưa có → vẫn ra video khung chữ và nói rõ.

```
javis_render_script_video(
  script="Hook...\n\nÝ 2...\n\nCTA...",
  title="...",
  aspect="portrait",
  with_images=true,
  image_quality="low"
)
```

Sau khi xong: đưa `attachments/*.mp4` cho user.

## Pixelle (tuỳ chọn)

`javis_pixelle_generate` khi API :8000 sống **và** có `RUNNINGHUB_API_KEY` (template `image_*`).
Không đủ → tool tự fallback sang đường ChatGPT ở trên.

## Quy trình

1. Brief ngắn
2. Kịch bản N cảnh (1 ý / cảnh)
3. Render bằng `javis_render_script_video` (đầy đủ ảnh)
4. Kiểm số cảnh / tỉ lệ

## Bẫy

- Báo Pixelle đang render khi chỉ có static / fallback — SAI; nói đúng nguồn (ChatGPT ảnh hay Pixelle).
- `with_images=false` chỉ khi user muốn bản chữ nhanh.
- Nhiều cảnh + `image_quality=high` tốn quota ChatGPT; mặc định `low`.
