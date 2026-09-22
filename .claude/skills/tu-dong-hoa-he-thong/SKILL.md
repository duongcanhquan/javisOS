---
name: Xây dựng tự động hóa
description: "Thiết kế tự động hóa bằng loop/workflow/Kanban/MCP; chọn công cụ nhỏ nhất đủ chạy và ghi đúng chỗ."
description_en: "Design automation with loop/workflow/Kanban/MCP; pick the smallest tool that works."
group: Second Brain
---

# Xây dựng hệ thống tự động hóa

## Khi nào dùng

User muốn "tự chạy mỗi sáng", digest email định kỳ, pipeline nghiên cứu → proposal,
nhắc hạn, nối Zalo/Gmail/Drive thành chuỗi, hoặc nhiệm vụ 5 của brain thứ 2.

## Thang công cụ (nhỏ → lớn) — chọn MỘT mức đủ

1. Trả lời / checklist tay — nếu chỉ làm một lần.
2. `javis_task` (Kanban) — một lần, chạy nền.
3. `javis_schedule` nhắc hẹn — mốc giờ cố định.
4. Loop `Javis/loops/<slug>.md` — lặp vô hạn theo chu kỳ + kiểm chứng.
5. Workflow `workflows/<slug>.md` — nhiều bước / nhiều agent.
6. Skill mới — cách-làm tái dùng, chưa cần code.
7. Plugin — chỉ khi cần tool native mới.

Đọc `Javis/index.md` trước khi tạo, tránh trùng.

## Khi thiết kế loop digest (ví dụ)

- Trigger: cron sáng (timezone `Asia/Ho_Chi_Minh`).
- Bước: skill `tong-hop-email-drive` → ghi `sources/digest-...` → gửi kênh user chọn
  (web/Zalo), không spam nếu không có việc.
- Kiểm chứng: connector Gmail/Drive `ok`; nếu 403 thì báo lỗi, không bịa digest.

## An toàn

Không bật loop gửi email hàng loạt. Không full-auto việc irreversible (xoá, thanh toán)
mà không có bước duyệt. Ghi file đúng path tuyệt đối trong vault.
