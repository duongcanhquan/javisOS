# Năng lực hệ thống (agents / workflows)

Đồng bộ vào mọi brain qua `server/system_sync.py` (cùng cơ chế skill/loop).

- Nguồn: `system/agents/*.md`, `system/workflows/*.md`
- Đích: `<brain>/agents/`, `<brain>/workflows/`
- Không gồm agent HTĐT / dự án APC nội bộ (xem EXCLUDE trong script đóng gói).
- User sửa file → app không ghi đè (manifest `user-modified`).
- Studio seed vẫn dùng được để làm mới / bổ sung biến thể.
