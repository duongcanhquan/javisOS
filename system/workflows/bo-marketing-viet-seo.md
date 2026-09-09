---
type: workflow
name: Marketing → Viết bài SEO (+ SEO GPT)
slug: bo-marketing-viet-seo
status: active
group: Marketing
description: Nghiên cứu → viết bài SEO + SEO GPT (lead/FAQ/meta) → kiểm chứng.
steps:
- agent: mkt-nghien-cuu
  task: 'Research góc cạnh tranh + fact cho bài SEO từ: {{input}}'
- agent: mkt-viet-seo
  task: 'Viết bài SEO từ brief ''{{input}}'' và nghiên cứu:

    {{prev}}'
  verify_agent: mkt-kiem-chung
  max_retries: 1
model: gemini-2.5-flash
model_provider: gemini
updated: '2026-09-07'
---

Nghiên cứu → viết bài SEO + SEO GPT (lead/FAQ/meta) → kiểm chứng.
