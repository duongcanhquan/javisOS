---
name: pixcelvideo
description: "Short video: ưu tiên javis_render_script_video (Edge-TTS+ffmpeg); Pixelle fixed nếu có API :8000."
description_en: "Short video: prefer javis_render_script_video; Pixelle fixed mode when API :8000 is up."
group: Nội dung
---

# pixcelvideo — short video (native trước, Pixelle sau)

Skill bọc pipeline short-video. **Ưu tiên tool native của Javis** để LUÔN ra được mp4;
Pixelle ([ATH-MaaS/Pixelle-Video](https://github.com/ATH-MaaS/Pixelle-Video)) chỉ dùng khi
API đang chạy và user muốn ảnh AI / template HTML Pixelle.

Slug: **`pixcelvideo`** (alias: Pixelle, pixellevideo).

## Khi nào dùng

User muốn: Pixelle / pixcelvideo / short video / topic → mp4 / VO + chữ trên hình,
hoặc “làm video kiểu Pixelle”.

Không dùng khi cần collage Vox (`paperdesign`), Remotion timeline, hoặc HTML brand pack
(`html-video`) — theo catalog `lam-video`.

## Quy trình bắt buộc

### 1. Brief

Đủ: chủ đề, mục tiêu, độ dài (~n cảnh), tỉ lệ (portrait mặc định), ngôn ngữ.
Thiếu → hỏi ngắn.

### 2. Viết kịch bản (BẮT BUỘC)

File gợi ý: `sources/video-scripts/YYYY-MM-DD-<slug>-pixcelvideo.md`

- Hook ≤ 1–2 câu đầu
- N cảnh: mỗi cảnh **một ý**, narration ~1 câu (tiếng Việt OK)
- CTA cuối nếu cần
- Show user duyệt trước khi render (trừ khi user bảo render luôn)

Công thức thô: 15s ≈ 3–4 cảnh; 30s ≈ 5–7; 60s ≈ 8–12 (tối đa 20).

### 3. Render — chọn đường theo thứ tự

**A. Mặc định (đảm bảo có video): tool `javis_render_script_video`**

Plugin bundled `script-video`. Edge-TTS tiếng Việt + khung chữ + ffmpeg → `attachments/*.mp4`.
Không cần Pixelle, RunningHub hay Comfy.

```
javis_render_script_video(
  script="<mỗi cảnh một đoạn, cách dòng trống>",
  title="<tiêu đề>",
  aspect="portrait"   # hoặc landscape|square
)
```

Sau khi xong: đưa link `attachments/...` cho user (markdown).

**B. Pixelle API (tuỳ chọn, đẹp hơn nếu đã bật)**

Chỉ khi `PIXELLE_API_BASE` trỏ được (vd `http://host:8000`) và `GET {base}/health` OK:

- `POST {base}/api/video/generate/async` với `mode: "fixed"`, `frame_template` …
- Poll `GET {base}/api/tasks/{task_id}`

Thiếu Pixelle → **không dừng ở hướng dẫn dán WebUI** nếu user đòi có file:
chuyển ngay sang **A**. Chỉ đưa Manual pack khi user tự muốn chạy WebUI Pixelle.

**C. Đổi pipeline** (`paperdesign` / Remotion / html-video) khi user yêu cầu đúng style đó
và máy có đủ key/binary.

### 4. Kiểm chứng

Đối chiếu brief: số cảnh, ngôn ngữ, tỉ lệ. Lệch → sửa script rồi render lại.

## Bẫy

- Báo “đang render Pixelle” khi :8000 chết → SAI. Dùng A hoặc nói rõ thiếu gì.
- `mode: generate` Pixelle sau khi đã viết kịch bản kỹ → engine viết lại, lệch brief.
- Narration quá dài một cảnh → TTS lê thê; cắt trước khi render.
- Nhầm với `paperdesign` / Remotion.

## Kiểm chứng xong việc

- [ ] Brief đã chốt
- [ ] Kịch bản đã duyệt (hoặc user bảo render luôn)
- [ ] Có `attachments/*.mp4` (đường A) hoặc `video_url` Pixelle (đường B) hoặc lý do dừng rõ
