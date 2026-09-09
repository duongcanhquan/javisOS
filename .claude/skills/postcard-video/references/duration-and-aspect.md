# Độ dài và tỉ lệ - postcard video

## Độ dài

Upstream **không** khóa cứng số giây. Template Ink Press ~**36.2s** (1085 frames @ 30fps).

Khuyến nghị Javis cho mode postcard:

| Mục tiêu | Frames @30fps | Ghi chú |
|----------|---------------|---------|
| 15s | 450 | Teaser cực ngắn |
| 30s | 900 | Mặc định hỏi user |
| 45s | 1350 | Trần postcard khuyến nghị |
| 60-90s | 1800-2700 | Chỉ khi user xác nhận; nhiều shot hơn |
| >120s | - | Từ chối; tách video hoặc pipeline khác |

Khi brief >60s: nói rõ Remotion + agent sẽ chậm/tốn, hỏi cắt còn 30-45s hay giữ.

## Tỉ lệ khung hình

| Tỉ lệ | Dùng khi | Việc phải làm |
|-------|----------|----------------|
| **9:16** | Reels / TikTok / Stories (postcard điện thoại) | Đặt composition width/height Remotion 1080×1920; crop/reframe screenshot |
| **1:1** | Feed vuông | 1080×1080 |
| **16:9** | YouTube / web (mặc định upstream) | 1920×1080 như template |

Demo và recipe card upstream thiết kế quanh **landscape**. Vertical không phải "đổi một số" - phải đổi canvas và kiểm lại chữ (đủ cao ≥5% chiều khung theo aesthetic-rules upstream).

## Âm thanh vs độ dài

- BGM phủ cả clip; SFX gắn theo beat/shot.
- File SFX dài >5s trong kho upstream **bắt buộc** cắt `durationInFrames` kẻo tràn shot sau.
- Có BGM: xuất thêm bản không BGM nếu user cần tự lồng nhạc nền tảng.
