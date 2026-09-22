---
name: Tổng hợp email & Drive
description: "Đọc Gmail + Drive, lọc tín hiệu, gửi bản tổng kết ngày/tuần kèm nguồn và việc cần làm."
description_en: "Read Gmail+Drive, filter signals, send day/week digest with sources and next actions."
group: Second Brain
---

# Tổng hợp email, Drive và gửi tóm tắt

## Khi nào dùng

User nói: tổng kết email, inbox hôm nay, đọc Drive rồi tóm tắt, brief sáng, digest tuần,
"có thư/file nào cần anh xử lý không", hoặc nhiệm vụ 1 của brain thứ 2.

## Bắt buộc gọi tool — không đoán inbox

1. Xác định tài khoản: mặc định `duongcanhquan@gmail.com`; nếu nói trường / Việt Mỹ thì
   `quan.duong@caodangvietmy.edu.vn`. Có cả hai thì nêu rõ đang đọc tài khoản nào.
2. Gmail: tìm thư chưa đọc / quan trọng trong cửa sổ thời gian user nêu (mặc định 24h,
   "tuần" = 7 ngày). Lấy subject, from, ngày, 3–6 câu ý chính. Không bịa thread.
3. Drive / Workspace: tìm file sửa gần đây cùng cửa sổ thời gian. Đọc file user chỉ định
   hoặc 5 file mới nhất liên quan. Trích đoạn + tên file, không tóm file chưa mở.
4. Calendar cùng tài khoản: cuộc họp 24–48h tới nếu liên quan digest.
5. Ghi bản tổng kết vào `sources/digest-YYYY-MM-DD.md` (frontmatter `type: source`,
   `source_kind: own-note`, `status: unprocessed`) rồi trả lời user. Có insight tái dùng
   thì đề xuất lên wiki, không tự INGEST trừ khi user bảo lưu wiki.

## Khuôn bản tổng kết (ngắn, tiếng Việt)

- **Cần xử lý hôm nay** (tối đa 7 mục, mỗi mục: việc + nguồn thư/file + hạn nếu có)
- **Thông tin** (tin đã đọc, không cần hành động)
- **Lịch sắp tới**
- **Thiếu quyền / tool lỗi** — nói thẳng connector nào fail, đừng bịa nội dung

## An toàn

Không gửi email, không chia sẻ Drive, không xoá thư trừ khi user ra lệnh rõ.
Compose / draft chỉ khi user bảo soạn.
