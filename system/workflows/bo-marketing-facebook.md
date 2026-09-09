---
type: workflow
name: Marketing → Page Facebook
slug: bo-marketing-facebook
status: active
group: Marketing
description: Đọc Page + bài đăng organic → báo cáo dễ hiểu → kiểm chứng.
steps:
- agent: mkt-facebook
  task: 'Báo cáo Facebook Page organic theo brief: {{input}}'
  verify_agent: mkt-kiem-chung
  max_retries: 1
model: gemini-2.5-flash
model_provider: gemini
updated: '2026-09-07'
---

Đọc Page + bài đăng organic → báo cáo dễ hiểu → kiểm chứng.
