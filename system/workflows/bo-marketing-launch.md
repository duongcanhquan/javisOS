---
type: workflow
name: Marketing → Ra mắt sản phẩm
slug: bo-marketing-launch
status: active
group: Marketing
description: Context/proposal → kế hoạch launch → kiểm chứng.
steps:
- agent: mkt-launch
  task: 'Đọc product marketing context nếu có, rồi lập kế hoạch launch/GTM từ: {{input}}

    {{prev}}'
  verify_agent: mkt-kiem-chung
  max_retries: 1
model: gemini-2.5-flash
model_provider: gemini
updated: '2026-09-22'
---

Context → plan launch → kiểm chứng.
