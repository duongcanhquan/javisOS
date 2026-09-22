---
name: Hybrid Antigravity / Claude
description: "Việc nhẹ dùng Antigravity (miễn phí); việc nặng đề xuất Claude: proposal, so sánh sâu, tự động hóa rủi ro."
description_en: "Light work on Antigravity (free); heavy work prefer Claude: proposals, deep compare, risky automation."
group: Second Brain
---

# Phân luồng model: Antigravity mặc định, Claude khi nặng

Main hiện tại: **antigravity-cli / gemini-3.8-flash-high**. Việc nền (auxiliary) cũng
trỏ Antigravity để khỏi đốt token Claude.

## Ở lại Antigravity (làm luôn, gọi tool đầy đủ)

- Digest email/Drive, hỏi đáp, tóm ngắn, lịch, soạn nháp.
- Tư vấn 2–3 phương án, copy nhanh.
- Gọi MCP, skill, Kanban, loop đơn giản.

## Đề xuất chuyển Claude (picker → Claude / sonnet hoặc model Claude trên Antigravity)

Nêu 1 câu: việc này sâu, tốn token, nên chuyển Claude rồi nhắc lại yêu cầu.

- Proposal / chiến lược 12 tháng, pitch khách.
- So sánh nhiều báo cáo, đọc file dài, đối chiếu số liệu.
- Thiết kế hệ thống tự động hóa nhiều nhánh, review rủi ro.
- Khi Antigravity lỗi tool / trả lời nông sau 2 vòng gọi tool.

Không tự đổi engine (Javis không switch provider giữa lượt). User đổi ở Models.
Sau khi user đổi, làm tiếp đúng skill, không hỏi lại từ đầu.
