---
name: pixcelvideo
description: "Short video qua Pixelle (javis_pixelle_generate) hoặc native ffmpeg; ưu tiên Pixelle nếu :8000 sống."
description_en: "Short video via Pixelle API or native ffmpeg; prefer Pixelle when :8000 is up."
group: Nội dung
---

# pixcelvideo — Pixelle đầy đủ + fallback native

Trên VPS Javis (0.35.36+), deploy **tự bật Pixelle** (`scripts/setup-pixelle-vps.sh` +
`--profile pixelle`) trừ khi `.env` có `JAVIS_ENABLE_PIXELLE=false`.

- API: `http://pixelle-api:8000` (host `localhost:8000`)
- WebUI: `localhost:8501`
- Biến: `PIXELLE_API_BASE`, `PIXELLE_LLM_*`, `RUNNINGHUB_API_KEY` (tuỳ chọn ảnh AI)

## Khi nào dùng

User muốn short video / Pixelle / pixcelvideo / topic → mp4.

## Quy trình

1. **Brief** rồi **viết kịch bản** (mỗi cảnh một đoạn). Duyệt với user trừ khi bảo render luôn.
2. **Render** — gọi tool theo thứ tự:

### A. `javis_pixelle_generate` (đầy đủ Pixelle)

```
javis_pixelle_generate(
  script="<mỗi cảnh một đoạn>",
  title="...",
  frame_template="1080x1920/static_default.html"
)
```

Có `RUNNINGHUB_API_KEY` → dùng `1080x1920/image_default.html` (ảnh AI).

Tool **tự fallback** sang native nếu Pixelle chết.

### B. `javis_render_script_video` (native Edge-TTS + khung chữ)

Dùng khi muốn chắc chắn / nhanh, không qua Pixelle.

3. Đưa đường dẫn / `video_url` cho user.

## Config LLM cho Pixelle (trên VPS `.env`)

```
PIXELLE_LLM_API_KEY=...
PIXELLE_LLM_BASE_URL=https://api.openai.com/v1
PIXELLE_LLM_MODEL=gpt-4o-mini
RUNNINGHUB_API_KEY=...
```

Không có key ảnh → template **static** vẫn ra video + TTS.

## Bẫy

- Đòi ảnh AI mà chưa có RunningHub → nói thật, dùng static hoặc native.
- `mode: generate` Pixelle viết lại script — skill này mặc định **fixed** qua tool.
