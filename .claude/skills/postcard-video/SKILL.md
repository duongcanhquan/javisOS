---
name: Postcard video
description: "Postcard video (shotcraft): promo Remotion từ recipe card, SFX/BGM, 15-45s."
description_en: "Postcard video (shotcraft): Remotion promo from shot cards, SFX/BGM, 15-45s."
group: Nội dung
---

# Postcard video (video-shotcraft)

Adapter Javis cho upstream
[Vincentwei1021/video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft):
làm **promo / launch / demo sản phẩm** kiểu cinematic Remotion (shot recipe + SFX/BGM),
gói gọn thành **postcard video** (ngắn, một thông điệp rõ).

Skill này **không** nhúng cả repo upstream (~100MB) vào image. Lần đầu chạy phải
`ensure-shotcraft` (clone vào `$JAVIS_STATE_DIR/vendor/video-shotcraft`).

## Khi nào dùng

- User nói **postcard video**, **video-shotcraft**, promo Remotion từ shot card, cinematic product video.
- Muốn teaser / launch / demo UI có motion + SFX/BGM (không phải collage Vox, không phải short chỉ ảnh+TTS).
- Pipeline `lam-video` chọn `postcard-video`.

**Không dùng** khi cần VO tiếng Việt tự sinh ngay → `pixcelvideo` / `paperdesign`.  
Cần motion khóa word-level theo file voiceover → gợi ý repo chị em **video-talkcraft** (chưa ship trong Javis).

## Độ dài & tỉ lệ (đọc trước khi hứa)

Chi tiết: `references/duration-and-aspect.md`.

| Độ dài | Khuyến nghị |
|--------|-------------|
| **15-45s** | Postcard mặc định (gợi ý **30s**) |
| ~36s | Đúng độ dài template Ink Press upstream |
| 60-90s | Được nhưng tốn; cảnh báo rõ |
| >2 phút | Từ chối postcard; đổi pipeline hoặc cắt chương |

Tỉ lệ: **9:16** (Stories/Reels), **1:1**, hoặc **16:9** (mặc định upstream). Vertical/square phải đổi composition Remotion, đừng giả định demo landscape chạy sẵn.

## Chuẩn bị (thiếu thì DỪNG)

1. Engine CLI có Bash: Claude Code / Codex / Antigravity. Engine API alone không render Remotion.
2. Máy có `node` (≥20), `npm`, `ffmpeg`.
3. Chạy `bash .claude/skills/postcard-video/scripts/ensure-shotcraft.sh` (hoặc đường tuyệt đối trong brain sau sync). Script clone shallow nếu chưa có.
4. Brief đủ: chủ đề, mục tiêu, độ dài, tỉ lệ, ngôn ngữ chữ trên hình, tài sản (URL sản phẩm / screenshot). Xem `references/postcard-brief.md`.
5. Nạp thêm skill `remotion-best-practices` khi viết/render composition.

Đọc thêm: `references/setup.md`.

## Cách chạy (tóm tắt)

1. **Cổng brief** postcard (độ dài ≤45s trừ khi user ép).
2. **Ensure upstream** + mở `SKILL.md` / `references/pipeline.md` trong thư mục vendor (nguồn sự thật cho shot card, sound-design, template).
3. Chọn mode upstream: template Ink Press / tự do / cùng sáng tạo. Postcard mặc định: **tự do ngắn** hoặc template nếu user muốn giống mẫu.
4. Thu thập screenshot (full page 2x khi có thể) - không bịa UI.
5. Storyboard theo recipe card; SFX/BGM theo `sound-design.md` upstream. VO chỉ khi user đưa file âm thanh.
6. Scaffold / cập nhật Remotion project (30fps), render mp4.
7. QA still từng shot quan trọng; giao `out/*.mp4`. Nếu user muốn lưu brain: copy vào `attachments/videos/<slug>.mp4` và nhúng link trong chat.

Không hứa "xong em báo lại" nếu render chạy nền - giao Kanban hoặc làm xong trong lượt.

## Quy trình với lam-video

Khi skill `lam-video` đã chọn pipeline `postcard-video`: giữ brief chung, rồi chuyển sang skill này từ bước ensure → render. Không song song paperdesign trong cùng một thành phẩm.

## Bẫy

- Đừng copy cả `demos/` / `assets/` vào vault brain (nặng, dễ lệch sync).
- Đừng mặc định 16:9 khi user muốn postcard điện thoại (9:16).
- Đừng gắn TTS Edge như pixcelvideo trừ khi user yêu cầu riêng và chấp nhận làm tay trong Remotion.
- Description router đã cắt 150 ký tự - trigger dài nằm ở mục này, không nhét frontmatter.

## Kiểm chứng

- [ ] Upstream path tồn tại (`ensure-shotcraft` exit 0)
- [ ] Brief đủ 5 mục bắt buộc
- [ ] Độ dài ≤45s hoặc đã cảnh báo + user xác nhận
- [ ] File mp4 ra được; mở được bằng player thường
- [ ] Không dùng em dash trong copy trên hình / caption
