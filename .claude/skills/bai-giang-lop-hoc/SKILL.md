---
name: Bài giảng lớp học
description: "Gói lớp học tương tác: outline, cảnh, quiz, script giảng; tùy chọn đẩy OpenMAIC."
group: Nội dung
---

# Bài giảng lớp học

## Khi nào dùng

User chọn đầu ra **lớp học** / classroom / interactive lesson.

## Quy trình

1. Chốt brief (chủ đề, đối tượng, mục tiêu, thời lượng ước lượng, ngôn ngữ).
2. Đọc file đính kèm; thiếu kiến thức then chốt → `deep-research`.
3. Viết **outline cảnh** (8-15 scene): mục tiêu cảnh, hoạt động, câu hỏi, visual.
4. Thêm **quiz** (4-8 câu) + **PBL ngắn** (1 task thực hành).
5. Viết **script giảng** từng cảnh (giọng nói tự nhiên, ≤90s/cảnh).
6. Lưu `exports/bai-giang/<slug>/lop-hoc.md` (+ quiz.md).
7. Mở **OpenMAIC self-host** của trường (`https://openmaic.vietmycollege.com`) — dán outline/script vào Generate classroom.
   - Mã site (ACCESS_CODE) nhập **1 lần** trên trình duyệt (đã cấu hình trên VPS, mặc định `vietmy-openmaic`).
   - **Không** lấy mã tạm trên open.maic.chat.
   - Trong Javis → Việc → Bài giảng → tab Lớp học: Lưu mã & URL / Copy brief / Mở OpenMAIC.

## Đầu ra

Markdown có: mục tiêu, outline, script, quiz, tài liệu tham chiếu (Sources).
