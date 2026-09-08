---
name: Bài giảng lớp học
description: "Gói lớp học tương tác: outline, cảnh, quiz, script giảng; tạo OpenMAIC ngay trong Javis."
description_en: "Interactive class pack: outline, scenes, quiz, teaching script; create OpenMAIC inside Javis."
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
   - Script **tiếng Việt dấu đầy đủ**; không Pinyin, không chữ Hán, không trộn zh.
6. Lưu `exports/bai-giang/<slug>/lop-hoc.md` (+ quiz.md).
7. **Handoff OpenMAIC trong Javis** — xem khối dưới. **Không** bảo user mở domain `openmaic.*` hay Live Demo.

## Handoff OpenMAIC (trong Javis)

Sau khi có `lop-hoc.md`, hướng dẫn:

1. Ở trang **Việc → Bài giảng → Lớp học**, cột Kết quả: bấm **Tạo lớp OpenMAIC**.
2. Javis gọi API self-host (`POST /openmaic/generate`) — user không gõ key / access code.
3. Classroom hiện **iframe** ngay trong panel Kết quả.

Ràng buộc kỹ thuật (server đã xử lý; chỉ nhắc nếu user hỏi):

| Mục | Giá trị |
|-----|---------|
| API `language` | `en-US` (OpenMAIC chỉ nhận en-US\|zh-CN; `vi` sẽ **fallback zh-CN** → giọng Trung) |
| Nội dung | Requirement + script + quiz **tiếng Việt** |
| TTS | OpenAI → Javis Edge (Hoài My/Nam Minh); cấm Browser Native / Doubao / Qwen / zh-* |
| Live Demo | Cấm |

## Đầu ra

Markdown: mục tiêu, outline, script (VI), quiz, Sources. Cuối: một dòng nhắc bấm **Tạo lớp OpenMAIC** trong Javis.
