---
type: workflow
name: Nexu Video Pipeline
slug: nexu-video-pipeline
status: off
description: "text → open-design → htmlanything → motionanything → htmltomp4 → MP4"
steps:
  - agent: nexu-brief-design
    task: "Từ brief user: {{input}}. Chốt slug, DESIGN.md và 00-brief.md trong wiki/VIDEO/<slug>/. Trả đường dẫn file cho bước sau."
  - agent: nexu-html-builder
    task: "Dựa trên {{prev}} và file brief/DESIGN vừa ghi: dựng HTML multi-frame bằng htmlanything vào wiki/VIDEO/<slug>/02-frames/. Khớp khổ và thời lượng."
  - agent: nexu-motion
    task: "Dựa trên {{prev}}: gắn motion vào HTML bằng motionanything, cập nhật frame, ghi 03-motion-notes.md."
  - agent: nexu-render
    task: "Dựa trên {{prev}}: render MP4 bằng htmltomp4, lưu attachments/videos/<slug>.mp4, nêu path tuyệt đối để Telegram gửi file. {{input}} có thể chứa yêu cầu giọng đọc/nhạc."
updated: 2026-09-02
---
Pipeline Nexu đầy đủ: brief/design → HTML → motion → MP4.

Cách chạy:
1. Vào Workflows → bật status workflow này.
2. ▶ Chạy và dán brief (chủ đề, CTA, khổ, thời lượng, có/không giọng đọc).
3. Hoặc chat: nhờ chạy workflow nexu-video-pipeline với brief...

Thư mục chuẩn: wiki/VIDEO/<slug>/00-brief.md, 01-design.md, 02-frames/, 03-motion-notes.md, attachments/videos/<slug>.mp4.
