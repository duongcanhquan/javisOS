---
type: workflow
name: Marketing → CRO chuyển đổi
slug: bo-marketing-cro
status: active
group: Marketing
description: Context sản phẩm → audit CRO → kiểm chứng.
steps:
- agent: mkt-cro
  task: 'Đọc/bổ sung product marketing context nếu thiếu, rồi audit CRO từ: {{input}}'
  verify_agent: mkt-kiem-chung
  max_retries: 1
model: gemini-2.5-flash
model_provider: gemini
updated: '2026-09-22'
---

Context → CRO audit → kiểm chứng.
