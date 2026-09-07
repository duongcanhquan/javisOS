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
7. Nếu OpenMAIC sẵn (`vendor/OpenMAIC` hoặc Live Demo): đề xuất bước tạo classroom; không thì dừng ở gói markdown đủ chạy thủ công.

## Đầu ra

Markdown có: mục tiêu, outline, script, quiz, tài liệu tham chiếu (Sources).
