---
name: tong-ket-sang
description: "Tổng kết sáng: email hôm qua, việc cần làm/đã xong, lịch hôm nay và nhắc lịch ngày mai."
description_en: "Morning brief: yesterday's email, open/done tasks, today's calendar, and tomorrow's advance reminder."
group: Năng suất
---

# Tổng kết sáng

## Khi nào dùng

- Nhắc hẹn 8h sáng hàng ngày (label `Tổng kết sáng 8h`).
- User hỏi "tóm tắt sáng nay", "email hôm qua + lịch hôm nay", "brief buổi sáng".

Báo cáo của nhắc hệ thống (`chat_id=all`) được gửi về **cả Telegram và Zalo** nếu đã đấu ở trang Kênh.

## Chuẩn bị

1. Kiểm tra đã đấu **Gmail** (hoặc Google Workspace) và **Google Calendar** (hoặc Lịch trong Workspace). Thiếu thì nói thẳng thiếu gì, không bịa.
2. Lấy ngày theo giờ Việt Nam (UTC+7): **hôm qua**, **hôm nay**, **ngày mai**.
3. Chỉ **đọc**. Không gửi mail, không sửa/xoá sự kiện, không tạo đơn.

## Cách chạy

1. **Email hôm qua:** tìm thư công việc nhận/gửi trong ngày hôm qua (ưu tiên hộp thư công việc nếu user có nhiều tài khoản). Gom theo chủ đề / người gửi.
2. **Việc:** từ email + lịch + Tasks/Kanban nếu có - tách **cần làm** và **đã xử lý** (đã trả lời, đã xong, đã huỷ).
3. **Lịch hôm nay:** sự kiện trong ngày, giờ bắt đầu-kết thúc, địa điểm/link nếu có.
4. **Lịch ngày mai (remind trước):** sự kiện quan trọng cần chuẩn bị từ hôm nay.

Thiếu nguồn nào thì ghi rõ "(chưa đấu Gmail/Lịch)" ở đúng mục đó, vẫn trả các mục còn lại.

## Định dạng đầu ra

Viết như tin nhắn ngắn (Telegram/Zalo), tiếng Việt, không bảng, không gạch ngang dài (em dash).

```markdown
### Tổng kết sáng · <ngày hôm nay, dd/mm>

**Email hôm qua**
- ... (3-8 ý; không có thì "Không có thư đáng chú ý")

**Việc cần làm**
- ...

**Đã xử lý**
- ... (không có thì bỏ mục)

**Lịch hôm nay**
- HH:MM - tên sự kiện

**Nhắc trước · ngày mai**
- HH:MM - tên sự kiện (hoặc "Ngày mai trống lịch")

**Gợi ý 1-3 việc ưu tiên hôm nay**
- ...
```

## Bẫy

- Không bịa thư hay cuộc họp. Không thấy tool / lỗi quyền → nói thật.
- Không gửi mail hay đổi lịch dù có quyền full.
- Tránh tường chữ: mỗi mục vài gạch đầu dòng, in đậm số giờ và hạn chót.
