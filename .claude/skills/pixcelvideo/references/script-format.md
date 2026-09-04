# Định dạng kịch bản → Pixelle `mode: fixed`

## Mục tiêu

Javis viết kịch bản **phù hợp brief**, user duyệt, rồi đưa nguyên narration vào Pixelle
ở chế độ **fixed** (engine không viết lại lời — chỉ tách cảnh, gen ảnh/TTS/ghép).

## File trong brain

`sources/video-scripts/YYYY-MM-DD-<slug>-pixcelvideo.md`

```markdown
---
type: source
source_kind: video-script
pipeline: pixcelvideo
status: draft
title: "..."
n_scenes: 6
aspect: "9:16"
template: "1080x1920/image_default.html"
language: vi
prompt_prefix: "cinematic soft light, clean composition, ..."
---

# <Tiêu đề>

## Brief đã chốt
- ...

## Storyboard

### Cảnh 1 — Hook
- **Narration:** ...
- **Image prompt (EN):** ...
- **Cảm xúc / nhịp:** ...

### Cảnh 2
...

## Script fixed (dán API)

<đoạn 1>

<đoạn 2>
...
```

## Luật narration

1. **Một cảnh = một ý** — không nhồi 2 CTA trong một đoạn.
2. Độ dài: bám ~5–25 từ/cảnh (VO tiếng Việt có thể 8–35 từ nếu vẫn một hơi).
3. Hook cảnh 1 ≤ 3 giây nói.
4. Cảnh cuối: CTA hoặc punchline rõ.
5. Image prompt: tiếng Anh, mô tả hình (không chép nguyên narration), khớp `prompt_prefix`.

## Cách ghép `text` cho API `fixed`

Pixelle hỗ trợ tách theo **đoạn / dòng / câu** (cấu hình WebUI). Để ổn định:

- Mỗi cảnh một **đoạn văn** ngăn bằng dòng trống; hoặc
- Mỗi cảnh một **dòng** (không xuống dòng giữa câu).

Ví dụ `text`:

```
Bạn có biết thói quen nhỏ quyết định cả năm?

Mỗi ngày chỉ cần 1% tốt hơn là đã đổi đời.

Hãy bắt đầu từ việc ghi nhật ký 3 dòng tối nay.
```

→ 3 scenes khi split theo paragraph.

**Không** nhét image prompt vào `text` fixed — image prompt chỉ nằm trong file kịch bản
(để người duyệt / Manual pack). Khi `fixed`, Pixelle tự sinh image prompt từ narration
(trừ khi pipeline/API mở rộng hỗ trợ truyền riêng — đừng bịa field).

## Duyệt với user

Trước khi gọi API, hiện bảng ngắn:

| # | Narration | Hình (tóm tắt) |
|---|-----------|----------------|
| 1 | ... | ... |

Chờ xác nhận (hoặc chỉnh 1–2 cảnh) rồi mới `POST .../generate/async`.
