---
type: workflow
name: Thiết kế từ ý tưởng (tới spec)
slug: thiet-ke-tu-y-tuong
status: active
group: AI
description: "Brainstorm Spike/Bounded/Architectural → draft design/spec → kiểm chứng. Dừng chờ user duyệt trước writing-plans."
steps:
  - agent: brainstorm-thiet-ke-he-thong
    task: "Brief: {{input}}. Nạp skill brainstorming. Phân loại luồng, nói to tên luồng, HARD-GATE. Architectural: viết docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md (JTBD, unit, PII/legal nếu cần). Bounded/Spike: thiết kế/khuyến nghị trong chat + nêu rõ chờ duyệt. Cuối bài: hướng dẫn user duyệt rồi chạy workflow lap-ke-hoach-tu-spec. Không viết code."
  - agent: kiem-chung-spec-thiet-ke
    task: "Kiểm chứng output {{prev}} / file spec vừa tạo theo checklist brainstorming. FAIL thì nêu đoạn sửa cụ thể."
    max_retries: 1
  - agent: brainstorm-thiet-ke-he-thong
    task: "Nếu {{prev}} có FAIL: sửa spec/thiết kế. Nếu PASS: tóm tắt đường dẫn spec (nếu có) và nhắc HARD-GATE - chờ user duyệt trước workflow lập kế hoạch. Không gọi writing-plans."
updated: 2026-09-06
---

# Thiết kế từ ý tưởng (tới spec)

Workflow **không** tự code. Kết thúc ở thiết kế/spec + nhắc user duyệt.

## Cách chạy

1. Studio → Workflows → **Thiết kế từ ý tưởng (tới spec)** (● Sẵn sàng; nếu mờ → **Kích hoạt**).
2. **▶ Chạy** với brief ý tưởng / module.
3. Đọc kết quả + file spec (Architectural).
4. Khi **đã duyệt** → chạy workflow **Lập kế hoạch từ spec**.

Skill: `brainstorming` (+ `nghien-cuu-thi-truong` khi cần JTBD thị trường).
