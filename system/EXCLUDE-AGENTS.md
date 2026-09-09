# Agent KHÔNG đưa vào system/agents (kiến thức / vai trò riêng tổ chức)

Các file này chỉ nằm trong brain APC.HN (hoặc brain nội bộ), không ship trong image:

- danh-gia-doi-tac-htdt
- doi-moi-cong-nghe-nha-truong
- hop-tac-quoc-te-htdt
- thuc-tap-doanh-nghiep
- tu-van-bgh-chien-luoc
- du-an-uav
- du-an-dien-tu-fdi

Khi thêm agent dùng chung: copy vào `system/agents/` rồi bump VERSION.
Khi thêm agent nội bộ: chỉ ghi vào brain, **không** copy vào `system/`.
