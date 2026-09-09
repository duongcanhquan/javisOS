# Tạo video workbench (wizard A) - design

Date: 2026-09-09  
Status: approved (user: wizard A, no CapCut timeline)

## Goal

Add sidebar page **Công việc → Tạo video** (`id: video`): visual wizard that wraps existing video pipelines (postcard, short+VO, collage, Remotion, auto) with brief form, script box, step progress, and SSE log - same pattern as Bài giảng / Marketing.

## Non-goals (v1)

- CapCut / Motion Workbench timeline
- New render engine
- Bundling video-shotcraft assets into the image

## UX

```
[Postcard] [Short+VO] [Collage] [Remotion] [Tự chọn]
┌ Left ─────────────────┐  ┌ Right ──────────────────┐
│ Brief card for tab    │  │ Steps: Nghiên cứu → …   │
│ Chủ đề *              │  │ Status                  │
│ Mục tiêu *            │  │ Log / kết quả SSE       │
│ Độ dài / tỉ lệ / NN   │  │ Hint: Files attachments │
│ URL / tài sản         │  │                         │
│ Kịch bản / beat       │  │                         │
│ [Chuẩn bị] [Chạy]     │  │                         │
└───────────────────────┘  └─────────────────────────┘
```

## Run path

1. `POST /studio/seed-video` (idempotent) - ensures `bo-video-da-pipeline` + agents.
2. `EventSource /workflows/run?slug=bo-video-da-pipeline&brain=&input=<brief>`
3. Brief always includes `Pipeline: <id>` so đạo diễn does not guess against the tab.

## Files

- `dashboard/video.js` - `window.renderTaoVideo`
- `dashboard/console.js` - rail + VIEW_META + render branch
- `dashboard/index.html` - script tag
- `dashboard/i18n/{vi,en}.json` - page.video.*
- `server/main.py` - seed-video director text mentions postcard-video
- Reuse `dashboard/workbench.css` (`.jw-*`)

## Version

Ship with postcard-video skill on same branch if still open, or follow-up bump.
