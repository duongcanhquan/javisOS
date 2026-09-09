---
type: workflow
name: Bài giảng → Video
slug: bo-bai-giang-video
status: active
group: Nội dung
description: Nghiên cứu → beat/video bài giảng (lam-video) → kiểm chứng.
steps:
- agent: bg-nghien-cuu
  task: 'Cổng brief + nghiên cứu cho video bài giảng từ: {{input}}'
- agent: bg-video
  task: 'Làm video bài giảng từ brief ''{{input}}'' và nghiên cứu:

    {{prev}}'
  verify_agent: bg-kiem-chung
  max_retries: 1
model: gemini-2.5-flash
model_provider: gemini
updated: '2026-09-07'
---

Nghiên cứu → beat/video bài giảng (lam-video) → kiểm chứng.
