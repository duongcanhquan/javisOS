---
type: workflow
name: Lập kế hoạch từ spec
slug: lap-ke-hoach-tu-spec
status: active
group: AI
description: "Sau khi user duyệt spec brainstorming: writing-plans → file plan chi tiết. Không tự code."
steps:
  - agent: viet-ke-hoach-trien-khai
    task: "Input: {{input}}. Phải có đường dẫn spec đã duyệt hoặc USER_APPROVED_SPEC=yes. Nạp writing-plans. Viết docs/superpowers/plans/YYYY-MM-DD-<feature>.md. Nếu chưa duyệt → DỪNG và bảo chạy thiet-ke-tu-y-tuong / duyệt spec trước. Không code."
    verify_agent: kiem-chung-spec-thiet-ke
    max_retries: 1
updated: 2026-09-06
---

# Lập kế hoạch từ spec

Chạy **sau** khi user duyệt spec từ workflow **Thiết kế từ ý tưởng**.

## Cách chạy

1. Studio → **Lập kế hoạch từ spec** → **▶ Chạy**.
2. Input ví dụ: `USER_APPROVED_SPEC=yes spec=docs/superpowers/specs/2026-09-06-xxx-design.md`
3. Lấy plan tại `docs/superpowers/plans/`.

Skill: `writing-plans` (gate từ `brainstorming`).
