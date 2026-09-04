---
name: pixcelvideo
description: "Tạo short video qua Pixelle-Video: viết kịch bản/storyboard trước, rồi gọi engine (fixed script → ảnh/TTS/BGM → mp4). Alias: Pixelle, pixellevideo."
description_en: "Short video via Pixelle-Video: write script/storyboard first, then call the engine (fixed script → images/TTS/BGM → mp4)."
group: Nội dung
---

# pixcelvideo — Pixelle-Video (kịch bản trước, render sau)

Skill bọc [ATH-MaaS/Pixelle-Video](https://github.com/ATH-MaaS/Pixelle-Video)
(Apache-2.0; upstream cũng mirror [AIDC-AI/Pixelle-Video](https://github.com/AIDC-AI/Pixelle-Video)).

**Khác paperdesign/Remotion:** Pixelle là engine short-video tự động
(LLM → narration → image/video prompts → TTS → BGM → ghép frame HTML).
Trong Javis, skill này **bắt buộc viết kịch bản phù hợp trước**, rồi mới đưa vào
Pixelle ở chế độ `mode: "fixed"` (dùng đúng script đã duyệt — không để engine tự viết lại lung tung).

Slug skill: **`pixcelvideo`** (đúng tên user đặt).

## Khi nào dùng

User muốn: Pixelle / pixcelvideo / short video tự động / topic → mp4 / digital human
(pipeline mở rộng) / hình-ảnh-theo-câu-narration + voice + BGM, hoặc bảo “làm video
kiểu Pixelle”.

Không dùng khi cần collage Vox (`paperdesign`), Remotion timeline React (`remotion`),
hoặc HTML brand pack (`html-video`) — khi đó theo skill `lam-video` catalog.

## Chuẩn bị môi trường (kiểm tra, đừng bỏ)

Pixelle **chạy ngoài** process Javis (máy local / Docker / Windows package). Cần:

1. Repo + `config.yaml` (copy từ `config.example.yaml`) đã có:
   - `llm.api_key` + `base_url` + `model` (OpenAI-compatible; có thể trỏ Ollama)
   - Image/video: RunningHub / ComfyUI selfhost / `api_providers` (DashScope, OpenAI, Kling…)
   - TTS mặc định: `selfhost/tts_edge.json` (Edge-TTS) hoặc workflow khác
2. `ffmpeg` trên máy chạy Pixelle
3. API lắng nghe (mặc định docs): `uv run uvicorn api.app:app --host 0.0.0.0 --port 8000`
   - Web UI thường `:8501`
4. Biến môi trường Javis (tuỳ chọn): `PIXELLE_API_BASE` = `http://host:8000`
   (nếu trống: hỏi user URL hoặc hướng dẫn chạy WebUI/API)

Thiếu cấu hình → **DỪNG**, nêu rõ thiếu gì; vẫn có thể giao **Manual pack**
(kịch bản + image prompts) để user dán vào WebUI Pixelle.

Đọc thêm: `references/api.md`, `references/templates.md`.

## Quy trình bắt buộc (4 cổng)

### 1. Brief (đọc `references/brief.md`)

Đủ: chủ đề, mục tiêu, độ dài (~n_scenes), tỉ lệ (template), ngôn ngữ.
Thiếu → hỏi; không giả định rồi gọi API tốn tiền.

### 2. Viết kịch bản / storyboard (BẮT BUỘC — làm trong Javis)

Đọc `references/script-format.md`. Xuất file trong brain, ví dụ:

`sources/video-scripts/YYYY-MM-DD-<slug>-pixcelvideo.md`

Nội dung tối thiểu:

- Tiêu đề video
- Hook ≤ 1–2 câu đầu
- **N cảnh** — mỗi cảnh: narration (VO) + mô tả hình (image_prompt tiếng Anh khuyến nghị)
- CTA / kết nếu cần
- Gợi ý template (`1080x1920/image_default.html` …) + tone/style prefix

**Show kịch bản cho user duyệt** trước khi gọi Pixelle. Sửa theo feedback.

Công thức độ dài thô: 15s ≈ 3–4 cảnh; 30s ≈ 5–7; 60s ≈ 8–12
(`n_scenes` API 1–20). Mỗi narration ~5–20 từ (Pixelle mặc định); tiếng Việt có thể dài hơn một chút nhưng giữ **một ý / cảnh**.

### 3. Đưa kịch bản vào Pixelle (`mode: fixed`)

Ghép narration thành `text` theo format fixed (mỗi cảnh **một đoạn / một dòng** —
xem `references/script-format.md`). Gọi:

- Ưu tiên async: `POST {PIXELLE_API_BASE}/api/video/generate/async`
- Poll: `GET {PIXELLE_API_BASE}/api/tasks/{task_id}`
- Sync chỉ khi video ngắn / user đồng ý chờ: `.../generate/sync`

Body cốt lõi:

```json
{
  "text": "<script đã duyệt, mỗi cảnh một đoạn>",
  "mode": "fixed",
  "title": "<tiêu đề>",
  "frame_template": "1080x1920/image_default.html",
  "prompt_prefix": "<style tiếng Anh nếu có>",
  "bgm_volume": 0.3
}
```

- `mode: "generate"` chỉ dùng khi user **cố ý** muốn Pixelle tự viết lại từ topic
  (vẫn nên có outline Javis làm brief). Mặc định skill này = **`fixed`**.
- Sau khi xong: lưu `video_url` / tải file vào `attachments/` hoặc `sources/` brain nếu user muốn.

### 4. Kiểm chứng

Đối chiếu brief + kịch bản đã duyệt: số cảnh, ngôn ngữ, tỉ lệ, CTA.
Lệch → chỉnh script rồi gọi lại `fixed`, không nhảy pipeline khác trừ khi user đổi ý.

## Pipeline mở rộng (Pixelle)

Upstream còn: Digital Human, Image-to-Video, Motion Transfer, Custom Media.
Khi user yêu cầu các chế độ đó: đọc docs upstream + WebUI; skill này vẫn **viết brief/script
phù hợp trước**, rồi hướng dẫn thao tác / API tương ứng nếu có. Đừng bịa endpoint không có trong `references/api.md`.

## Bẫy

- Gọi `mode: generate` sau khi đã viết kịch bản kỹ → engine viết lại, lệch brief.
- Bỏ duyệt script → tốn RunningHub/Comfy/API.
- Nhầm với `paperdesign` (collage Vox) hoặc Remotion.
- Hardcode `localhost` trong Docker Javis mà Pixelle chạy trên host → dùng IP/gateway
  hoặc `PIXELLE_API_BASE` trỏ đúng máy.
- Narration quá dài một cảnh → TTS lê thê; cắt lại trước khi `fixed`.

## Kiểm chứng xong việc

- [ ] Brief đã chốt
- [ ] File kịch bản trong brain + user đã duyệt
- [ ] Request Pixelle `mode: fixed` (hoặc Manual pack đủ dán WebUI)
- [ ] Có `video_url` / đường dẫn mp4 hoặc lý do dừng rõ ràng
