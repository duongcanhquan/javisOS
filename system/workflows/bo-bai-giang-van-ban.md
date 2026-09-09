---
type: workflow
name: Bài giảng → Văn bản minh họa
slug: bo-bai-giang-van-ban
status: active
group: Nội dung
description: Nghiên cứu → bài đọc kèm ảnh/biểu đồ → kiểm chứng.
steps:
- agent: bg-nghien-cuu
  task: 'Cổng brief + nghiên cứu cho bài đọc minh họa từ: {{input}}'
- agent: bg-van-ban
  task: 'Viết bài minh họa từ brief ''{{input}}'' và nghiên cứu:

    {{prev}}'
  verify_agent: bg-kiem-chung
  max_retries: 1
model: gemini-2.5-flash
model_provider: gemini
updated: '2026-09-07'
---

Nghiên cứu → bài đọc kèm ảnh/biểu đồ → kiểm chứng.
