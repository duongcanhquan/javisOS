# Nhật ký cập nhật

Lịch sử phiên bản Javis OS. Bản mới nhất ở trên cùng. Xem ngay trong app tại mục **Cập nhật** trên thanh bên trái.

Định dạng: mỗi phiên bản là một khối `## [x.y.z] - ngày`, bên dưới nhóm thay đổi theo `### Thêm mới / Sửa lỗi / Cải thiện / Bảo mật`.

## [0.35.49] - 2026-09-05
### Sửa lỗi
- **Nhắc hẹn Ollama Local hết chạy cực chậm trên VPS 6GB.** Hạ `num_ctx` 16k→8k (tránh swap), giữ model nóng 30 phút, cắt `num_predict`, giới hạn 8 vòng tool, báo "đang xử lý" ngay trên Telegram.

#