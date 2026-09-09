---
type: workflow
name: Marketing → Báo cáo Facebook Ads
slug: bo-marketing-ads
status: active
group: Marketing
description: Kéo insights account+campaign → báo cáo số đo đầy đủ, dễ hiểu → kiểm
  chứng.
steps:
- agent: mkt-ads
  task: 'Báo cáo Facebook Ads đầy đủ số đo theo brief: {{input}}'
  verify_agent: mkt-kiem-chung
  max_retries: 1
model: gemini-2.5-flash
model_provider: gemini
updated: '2026-09-07'
---

Kéo insights account+campaign → báo cáo số đo đầy đủ, dễ hiểu → kiểm chứng.
