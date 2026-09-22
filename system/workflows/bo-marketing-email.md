---
type: workflow
name: Marketing → Email marketing
slug: bo-marketing-email
status: active
group: Marketing
description: Context sản phẩm → chuỗi email → kiểm chứng.
steps:
- agent: mkt-email
  task: 'Đọc product marketing context nếu có, rồi soạn chuỗi email từ: {{input}}

    {{prev}}'
  verify_agent: mkt-kiem-chung
  max_retries: 1
model: gemini-2.5-flash
model_provider: gemini
updated: '2026-09-22'
---

Context → chuỗi email → kiểm chứng.
