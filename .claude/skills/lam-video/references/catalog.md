# Catalog pipeline làm video

Chọn **một** pipeline chính. Có thể kết hợp phụ (vd motion-anything nhúng vào html-video).

| ID | Tên | Repo / skill | Hợp khi | Cần có |
|---|---|---|---|---|
| `paperdesign` | Vox paper-collage | skill `paperdesign` ([vox-director](https://github.com/Alisa0808/vox-director)) | Explainer, scrapbook, quảng cáo collage, talking-head A-roll, ảnh sản phẩm C-roll | `ATLASCLOUD_API_KEY`, ffmpeg, Pillow |
| `pixcelvideo` | Short video đầy đủ | skill `pixcelvideo` + `javis_render_script_video` (ảnh ChatGPT + TTS); Pixelle tuỳ chọn | Topic/script → ảnh AI + VO → mp4 | ChatGPT OAuth (ảnh) + ffmpeg + Edge-TTS; RunningHub chỉ nếu dùng Pixelle image_* |
| `remotion` | Remotion (React) | skill `remotion-best-practices` ([remotion-dev/skills](https://github.com/remotion-dev/skills)) | Motion UI, data viz, caption frame-perfect, video tham số hoá | Node, Remotion project, (render) ffmpeg |
| `html-video` | HTML → MP4 | [OmmiStudio](https://github.com/duongcanhquan/OmmiStudio) + [nexu html-video](https://github.com/nexu-io/html-video) | Template sẵn, brand pack, short marketing HTML kinetic | Node 20+, pnpm setup, Playwright Chromium, ffmpeg |
| `motion-css` | CSS kinetic | [motion-anything](https://github.com/nexu-io/motion-anything) (qua OmmiStudio) | Chữ/kinetic typography nhúng HTML hoặc video | Cùng stack html-video |
| `html-still` | HTML → ảnh/PDF | [html-anything](https://github.com/nexu-io/html-anything) | Thumbnail, slide, poster tĩnh (không phải video) | OmmiStudio / nexu |
| `manual` | Prompt-pack | Không render | Chưa có API/key/binary; user tự gen bên ngoài | Không |

## Luật chọn nhanh

1. User nói **Vox / collage / paperdesign / scrapbook** → `paperdesign`.
2. User nói **Pixelle / pixcelvideo / short tự động / topic ra mp4 có VO** → `pixcelvideo`
   (viết kịch bản → **`javis_render_script_video`**; Pixelle chỉ nếu API :8000 đang sống).
3. User nói **Remotion / React video / data trên timeline** → `remotion`.
4. User nói **Ommi / LYON Studio / template HTML / brand pack** → `html-video` (+ `motion-css` nếu cần chữ kinetic).
5. Chỉ cần **ảnh/slide** → `html-still`, đừng mở pipeline video.
6. Thiếu key/binary bắt buộc → `manual` + nêu rõ thiếu gì; hoặc đổi pipeline còn chạy được.

## OmmiStudio (repo của chủ)

Local studio bọc 5 repo nexu: `html-anything`, `html-video`, `motion-anything`, `open-design`, `nexu`.

- UI: `http://localhost:5173` · API: `:3001`
- Setup: `pnpm install && pnpm setup && pnpm dev`
- MP4 cần ffmpeg + Playwright Chromium sau `pnpm setup`

Khi chọn `html-video`: viết brief + chọn template + brand tokens; không bịa API Ommi nếu chưa có máy chạy studio.

## Paperdesign - cổng bắt buộc

1. Duyệt beat map trước khi gen ảnh.
2. Style bake-off rồi user (hoặc agent ghi rõ giả định) chọn theme.
3. Look nằm ở bước ảnh; motion sau.
