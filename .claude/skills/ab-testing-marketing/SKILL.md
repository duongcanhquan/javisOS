---
name: A/B testing marketing
description: "Thiết kế A/B test MKT: giả thuyết, metric, sample size, variant. Không tự bật test trên ads."
description_en: "Design marketing A/B tests: hypothesis, metrics, sample size, variants. Do not launch live tests."
group: Marketing
license: MIT
metadata:
  version: "1.0"
  upstream: "https://github.com/coreyhaines31/marketingskills/tree/main/skills/ab-testing"
---

# A/B testing marketing

## Khi nào dùng

User muốn A/B / thí nghiệm landing, CTA, giá, email subject, ads creative.

## Cách chạy

1. Giả thuyết: vì X đổi Y sẽ cải thiện metric Z (đo được).
2. **Một** thay đổi chính mỗi test.
3. Chốt primary + secondary + guardrail metrics.
4. Ước sample size / thời gian tối thiểu; cảnh báo peeking sớm.
5. Mô tả variant A/B (và C nếu cần) + traffic split.
6. Checklist pre-launch + cách đọc kết quả (significance, segment).
7. Xuất playbook experiment (Markdown) - **không** tự bật trên Meta/Google.

## Bẫy

- Test nhiều thứ cùng lúc → không kết luận được.
- Dừng sớm khi «thấy thắng».
- Không em dash.

## Kiểm chứng

- [ ] Có giả thuyết + primary metric
- [ ] Variant mô tả rõ
- [ ] Ghi điều kiện dừng / thời gian tối thiểu
