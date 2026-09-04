---
name: phan-tich-cuoc-hop
description: "Tổng kết transcript cuộc họp như trợ lý chuyên nghiệp: diễn biến, ý kiến, đề xuất, quyết định, việc cần làm, lưu ý. Không bịa."
description_en: "Professionally summarize a meeting transcript: flow, opinions, proposals, decisions, actions, notes. Do not invent."
group: AI
---

# Phân tích / tổng kết cuộc họp

## Khi nào dùng

Người dùng vừa ghi cuộc họp trên dashboard (Moonshine) hoặc có file trong
`sources/meetings/*.md`, và muốn bản tổng kết logic như thư ký chuyên nghiệp.

Nút **Tổng kết cuộc họp** gọi Ollama local (`qwen2.5:3b`) với cùng khuôn này.

## Bắt buộc

1. **Đọc transcript** (và ghi chú trước họp nếu có) trước khi viết.
2. **Không bịa** tên, ý kiến, đề xuất, quyết định, số liệu không có trong transcript.
3. Tôn trọng nhãn người nói trong transcript (`**[giờ] Tên:** ...`). Nếu không có nhãn thì gom theo nội dung, không bịa tên.
4. Transcript quá ngắn / mơ hồ: nói thẳng phần còn thiếu.

## Đầu ra (markdown)

```markdown
## Diễn biến cuộc họp
(Cuộc họp thế nào: mục đích, không khí, chủ đề theo thứ tự)

## Ý kiến các bên
(Gom theo người / nhóm; nêu quan điểm chính)

## Đề xuất đã nêu
(Các phương án được đưa ra)

## Quyết định
(Đã chốt gì; chưa chốt thì ghi rõ)

## Việc cần làm
- [ ] Việc — người phụ trách (nếu có) — hạn (nếu có)

## Cần lưu ý
(Rủi ro, điểm nghẽn, thông tin thiếu, follow-up)

## Tổng hợp
(1 đoạn ngắn, logic, như trợ lý chuyên nghiệp kết luận cả cuộc họp)
```

## Ghi file

- `sources/meetings/<stem>-summary.md`
- Frontmatter: `type: source`, `source_kind: meeting-summary`, `meeting_id`, `source`

## Model

Ollama local `qwen2.5:3b`. Transcript dài: cắt khối rồi gộp.
