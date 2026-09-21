---
type: workflow
name: Bài giảng → Slide
slug: bo-bai-giang-slide
status: active
group: Giáo dục
description: Nghiên cứu → deck HTML đẹp (slide-wright) + notes → kiểm chứng.
steps:
- agent: bg-nghien-cuu
  task: 'Cổng brief + nghiên cứu cho slide từ: {{input}}'
- agent: bg-slide
  task: 'Thiết kế slide từ brief ''{{input}}'' và nghiên cứu:

    {{prev}}'
  verify_agent: bg-kiem-chung
  max_retries: 1
model: gemini-2.5-flash
model_provider: gemini
updated: '2026-09-16'
---

Nghiên cứu → deck HTML đẹp (slide-wright) + notes → kiểm chứng.
