---
type: workflow
name: Bài giảng → Lớp học
slug: bo-bai-giang-lop-hoc
status: active
group: Nội dung
description: Nghiên cứu → thiết kế lớp học tương tác (cảnh/quiz/script) → kiểm chứng.
steps:
- agent: bg-nghien-cuu
  task: 'Cổng brief + nghiên cứu cho lớp học từ: {{input}}'
- agent: bg-lop-hoc
  task: 'Thiết kế lớp học từ brief ''{{input}}'' và nghiên cứu:

    {{prev}}'
  verify_agent: bg-kiem-chung
  max_retries: 1
model: gemini-2.5-flash
model_provider: gemini
updated: '2026-09-07'
---

Nghiên cứu → thiết kế lớp học tương tác (cảnh/quiz/script) → kiểm chứng.
