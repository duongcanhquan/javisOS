---
name: Lemo-Opuscar
description: "Phim ngắn render bằng code theo 51 style Lemo-Opuscar (không model video)."
description_en: "Short films rendered in code in one of 51 Lemo-Opuscar styles (no video model)."
group: "Video & Motion"
license: MIT
metadata:
  version: "1.0"
  upstream: "https://github.com/lemomo-ai/lemo-opuscar"
---

# Lemo-Opuscar

Adapter Javis cho [lemomo-ai/lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar) (MIT):
phim ngắn **vẽ bằng code** (HTML/CSS/JS/Three/canvas), **không** gọi Kling/Runway.
51 style (sơn dầu, thủy mặc, satellite briefing, product teardown, …).

Skill chỉ giữ hướng dẫn + script setup. Thư viện style nằm ngoài image (sparse clone).

## Khi nào dùng

- User muốn **phim / short / promo / explainer** theo style Lemo, OPUSCAR, "code film",
  "không model video", hoặc gọi tên style (Impasto, Ukiyo-e, Microscope Story, …).
- Pipeline `lam-video` chọn `lemo-opuscar`.

**Không dùng** khi chỉ cần Remotion typography/data → `remotion-best-practices` /
`remotion-topic-explainer`; collage Vox → `paperdesign`; cắt file video có sẵn.

## Chuẩn bị

1. Engine có Bash + `node` ≥20 + `ffmpeg` + Python 3.11+ (hoặc `uv`).
2. `bash .claude/skills/lemo-opuscar/scripts/ensure-lemo.sh` → in `LIB=...`
3. Ngay sau đó (nền được): `bash .../ensure-lemo.sh deps` (lần đầu vài phút).
4. Voice / music chỉ khi phim cần: `ensure-lemo.sh deps voice` hoặc `deps music`.
5. Đọc `$LIB/AGENTS.md`, `$LIB/DIRECTOR.md`, `$LIB/TECHNIQUE.md`.

Thiếu Node/ffmpeg/Python → báo user, không tự cài system package.

## Cách chạy

1. Ensure thư viện (`LEMO_OPUSCAR_HOME` mặc định `$JAVIS_STATE_DIR/vendor/lemo-opuscar`).
2. Chọn style (`$LIB/styles/README.md` hoặc gallery https://lemomo-ai.github.io/lemo-opuscar/).
3. **Một vòng hỏi** (DIRECTOR §1): thiếu gì về chủ đề, tài sản user, ngôn ngữ, có duyệt storyboard không.
4. Project folder trong brain: `exports/video/<slug>/` (skill mode: không dùng `films/` trong LIB).
5. Viết `TREATMENT.md` **trước** khi mở demo. Demo chỉ học kỹ thuật:
   `bash .../ensure-lemo.sh demo <slug>` sau khi đã có treatment.
6. Look → (storyboard nếu user hỏi) → voice → score → animation → mix → render theo TECHNIQUE.md.
7. Chạy tool từ `$LIB`: `cd "$LIB" && node core/render/... "<đường tuyệt đối project>" ...`
8. Giao đúng DIRECTOR §11; copy mp4 vào `attachments/videos/` nếu user muốn xem trong chat.

## Bẫy

- Đừng build trong `styles/` của thư viện; đừng copy story/timeline demo.
- Đừng vendor 200MB demo vào image/vault.
- Không em dash. Description ≤150 đã cắt - trigger dài ở đây.

## Kiểm chứng

- [ ] `ensure-lemo.sh` in `LIB=...` và `deps` xong (hoặc nêu thiếu gì)
- [ ] Có `TREATMENT.md` trước khi đọc demo
- [ ] Artifact trong `exports/video/<slug>/`
