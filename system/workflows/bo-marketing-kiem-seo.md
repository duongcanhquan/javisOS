---
type: workflow
name: Marketing → Kiểm SEO (+ SEO GPT)
slug: bo-marketing-kiem-seo
status: active
group: Marketing
description: Nghiên cứu ngắn → audit SEO cổ điển + SEO GPT → kiểm chứng.
steps:
- agent: mkt-nghien-cuu
  task: 'Nếu brief đã có URL/nội dung rõ thì tóm tắt ngữ cảnh SEO ngắn; nếu chỉ có
    từ khóa/thị trường thì research nhẹ cho: {{input}}'
- agent: mkt-kiem-seo
  task: 'Audit SEO từ brief ''{{input}}'' và ngữ cảnh:

    {{prev}}'
  verify_agent: mkt-kiem-chung
  max_retries: 1
model: gemini-2.5-flash
model_provider: gemini
updated: '2026-09-07'
---

Nghiên cứu ngắn → audit SEO cổ điển + SEO GPT → kiểm chứng.
