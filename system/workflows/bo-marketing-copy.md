---
type: workflow
name: Marketing → Copy chuyển đổi
slug: bo-marketing-copy
status: active
group: Marketing
description: Context sản phẩm → viết copy → kiểm chứng.
steps:
- agent: mkt-copy
  task: 'Đọc product marketing context nếu có, rồi viết/sửa copy từ: {{input}}

    {{prev}}'
  verify_agent: mkt-kiem-chung
  max_retries: 1
model: gemini-2.5-flash
model_provider: gemini
updated: '2026-09-22'
---

Context → copy → kiểm chứng.
