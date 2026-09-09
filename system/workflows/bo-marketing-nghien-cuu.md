---
type: workflow
name: Marketing → Nghiên cứu thị trường
slug: bo-marketing-nghien-cuu
status: active
group: Marketing
description: Deep-research + khung thị trường → kiểm chứng.
steps:
- agent: mkt-nghien-cuu
  task: 'Nghiên cứu thị trường đầy đủ cho: {{input}}'
  verify_agent: mkt-kiem-chung
  max_retries: 1
model: gemini-2.5-flash
model_provider: gemini
updated: '2026-09-07'
---

Deep-research + khung thị trường → kiểm chứng.
