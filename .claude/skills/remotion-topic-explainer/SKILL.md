---
name: Remotion Topic Explainer
description: "Tạo video dọc 50-60s (9:16) giải thích chủ đề bằng Remotion + TTS; template CuongIT."
description_en: "Make a 50-60s vertical (9:16) topic explainer with Remotion + TTS; CuongIT template."
group: "Video & Motion"
license: MIT
metadata:
  version: "1.0"
  upstream: "https://github.com/Cuongyd196/remotion-cuongit-template"
---

# Remotion Topic Explainer (CuongIT)

Adapter Javis cho
[Cuongyd196/remotion-cuongit-template](https://github.com/Cuongyd196/remotion-cuongit-template):
video dọc **50-60 giây**, **1080×1920 @ 30fps** (TikTok / Shorts / Reels), 6 cảnh
Hook → Pain → Solution ×2 → Benefits → Outro, giọng TTS + phụ đề 1 dòng.

Skill **không** nhúng cả repo Remotion vào image. Lần đầu chạy `ensure-template.sh`
(clone vào `$JAVIS_STATE_DIR/vendor/remotion-cuongit-template`).

## Khi nào dùng

- User nói **topic explainer**, **video dọc kiến thức**, **Remotion CuongIT**, short 9:16
  giải thích công nghệ / quy trình / khái niệm.
- Pipeline `lam-video` chọn `remotion-topic-explainer`.

**Không dùng** khi cần collage Vox → `paperdesign`; postcard cinematic → `postcard-video`;
phim style Lemo → `lemo-opuscar`; Remotion data/UI chung → `remotion-best-practices`.

## Chuẩn bị

1. Engine có Bash (Claude Code / Codex / Antigravity / Grok Build).
2. Máy có `node` (≥18), `npm`, `ffmpeg`.
3. `bash .claude/skills/remotion-topic-explainer/scripts/ensure-template.sh`
4. Nạp thêm `remotion-best-practices` khi viết composition.
5. TTS mặc định **Edge** (`edge-tts-universal` / Edge trên Javis). CIT Voice Studio chỉ khi
   user đã cài và bật `TTS_PROVIDER=cit`.

Brief tối thiểu: chủ đề, ngôn ngữ (mặc định tiếng Việt), tên kênh/badge (mặc định từ
`CHANNEL_NAME` hoặc "VietMy OS"), có/không CTA cuối.

## Cách chạy

1. Ensure template → `TPL=$JAVIS_STATE_DIR/vendor/remotion-cuongit-template`.
2. Copy project sang brain: `exports/video/<slug>/` (đừng làm việc trực tiếp trong vendor).
3. Cấu hình `.env` (xem `references/env.md`): `TTS_PROVIDER=edge`, `EDGE_TTS_VOICE=vi-VN-HoaiMyNeural`, `CHANNEL_NAME=...`.
4. Viết 6 cảnh + lời thoại; sinh audio theo script template (`scripts/generate-tts.ts` hoặc tương đương).
5. Component `src/<TopicName>/` theo khung upstream (BrandHeader top 150px, nội dung giữa, SubtitleBox `mt-64`, buffer `+3` frames).
6. Đăng ký `Composition` 1080×1920 @ 30fps trong `Root.tsx`.
7. Preview: `npm run dev`. Render: `npx remotion render <TopicName> out/<TopicName>.mp4`.
8. Copy mp4 vào `attachments/videos/` hoặc để trong `exports/video/<slug>/` và nhúng link chat.

Antigravity: render bằng `run_command` / `npx remotion render`. Không hứa "xong sẽ báo" nếu chưa queue Kanban.

## Bẫy

- Đừng vendor cả `node_modules` / `public/audio` demo vào vault.
- Đừng dùng tỉ lệ 16:9 khi user muốn Reels (9:16).
- Description router cắt 150 ký tự - trigger dài nằm ở mục này.
- Không em dash.

## Kiểm chứng

- [ ] `ensure-template` exit 0
- [ ] Project ở `exports/video/<slug>/`, không sửa vendor
- [ ] MP4 9:16 mở được; phụ đề 1 dòng; badge kênh không đụng UI TikTok
