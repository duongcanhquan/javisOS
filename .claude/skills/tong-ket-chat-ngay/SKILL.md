---
name: tong-ket-chat-ngay
description: "Tổng kết Google Chat trong ngày: chủ đề trao đổi, ai nhắc tới bạn, việc cần phản hồi."
description_en: "Daily Google Chat digest: topics discussed, who mentioned you, items needing reply."
group: Năng suất
---

# Tổng kết Google Chat trong ngày

## Khi nào dùng

- Nhắc hẹn **Tổng kết Chat 18h** (cuối ngày làm việc).
- User hỏi: "Chat hôm nay nói gì", "ai nhắc tôi trên Google Chat", "tóm tắt Chat ngày".

Báo cáo nhắc hệ thống mặc định (`chat_id=zalo`) chỉ gửi **Zalo**. Dùng `chat_id=all` nếu muốn cả Telegram.

## Chuẩn bị

1. Kiểm tra đã đấu **Google Chat** (Kết nối → Google → Google Chat). Thiếu thì nói thẳng, không bịa.
2. Cần tài khoản **Google Workspace** (email tên miền công ty). @gmail.com cá nhân không dùng được Chat API.
3. Lấy **hôm nay** theo giờ Việt Nam (UTC+7). User hỏi ngày khác thì theo ngày họ nói.
4. Biết **email hoặc tên hiển thị** của user để nhận @mention (từ kết nối OAuth, Memory, hoặc hỏi một lần nếu chưa có).
5. Chỉ **đọc**. Không gửi tin Chat, không đánh dấu đã đọc, trừ khi user yêu cầu rõ.

## Cách chạy (tool Google Chat MCP)

1. **Khám phá space:** `search_conversations` hoặc liệt kê space/DM đang hoạt động (ưu tiên space làm việc, DM nhóm).
2. **Tin trong ngày:** với mỗi space quan trọng, dùng `list_messages` / `search_messages` lọc theo ngày hôm nay (hoặc query có từ khóa + thời gian nếu tool hỗ trợ).
3. **Ai nhắc tôi:** tìm mention tên user, @email, hoặc reply trực tiếp tới user. Ghi rõ **ai**, **space nào**, **nội dung ngắn**.
4. **Tổng hợp chủ đề:** gom theo space hoặc chủ đề (dự án, phòng ban), không chép nguyên văn từng tin dài.
5. **Việc cần phản hồi:** tin hỏi thẳng user, giao việc, deadline, hoặc thread chưa có câu trả lời của user.

Thiếu quyền / lỗi tool → nói đúng lỗi, gợi ý đăng nhập lại hoặc bật API Chat trên Google Cloud. Không bịa tin nhắn.

## Định dạng đầu ra

Viết như tin nhắn ngắn (Telegram/Zalo), tiếng Việt, không bảng, không em dash.

```markdown
### Tổng kết Chat · <ngày dd/mm>

**Tóm tắt nhanh**
- 1-3 câu: hôm nay Chat chủ yếu về gì.

**Theo space / nhóm**
- *Tên space:* ý chính (2-5 gạch đầu dòng; không có hoạt động thì "Im lặng hôm nay")

**Ai nhắc tới bạn**
- *Người* (space): nội dung ngắn + cần làm gì (không có thì "Không ai nhắc trực tiếp")

**Cần phản hồi / theo dõi**
- ...

**Gợi ý 1-3 việc**
- ...
```

## Bẫy

- Không bịa tin hoặc người. Space trống thì ghi "không có tin mới".
- Không gửi tin Chat dù có quyền full trừ khi user yêu cầu riêng.
- Chat họp online (Meet) thường không đủ trong Chat API nếu người chỉ nói miệng - nói rõ giới hạn nếu user hỏi.
