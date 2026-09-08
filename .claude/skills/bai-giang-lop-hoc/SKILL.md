---
name: Bài giảng lớp học
description: "Gói lớp học tương tác: outline, cảnh, quiz, script giảng; tạo OpenMAIC ngay trong Javis."
description_en: "Interactive class pack: outline, scenes, quiz, teaching script; create OpenMAIC inside Javis."
group: Nội dung
---

# Bài giảng lớp học

## Khi nào dùng

User chọn đầu ra **lớp học** / classroom / interactive lesson.

**Chuẩn chất lượng:** lớp phải nghe như giảng viên đang dạy (giới thiệu, giải thích,
ví dụ, chuyển cảnh) kèm giọng đọc — **không** chấp nhận vài dòng nói xong rồi hết.
Kiến thức nguồn đầy đủ thì script/`lop-hoc.md` phải GIỮ và TRIỂN khai, không nén slogan.

## Quy trình

1. Chốt brief (chủ đề, đối tượng, mục tiêu, thời lượng ước lượng, ngôn ngữ).
2. Đọc file đính kèm; thiếu kiến thức then chốt → `deep-research`.
3. Viết **outline cảnh** (8-15 scene): mục tiêu cảnh, hoạt động, câu hỏi, visual.
4. Thêm **quiz** (4-8 câu) + **PBL ngắn** (1 task thực hành).
5. Viết **script giảng** từng cảnh (giọng nói tự nhiên, 45–90s/cảnh).
   - Script **tiếng Việt dấu đầy đủ**; không Pinyin, không chữ Hán, không trộn zh.
   - **Cấm nội dung mỏng:** mỗi cảnh dạy phải có định nghĩa / vì sao quan trọng / 1–2 ví dụ /
     lỗi hay gặp / takeaway. Không chỉ liệt kê tiêu đề rồi “xem slide sau”.
6. Với mỗi cảnh, ghi **gợi ý visual** rõ: layout (2 cột, timeline, bước quy trình…),
   biểu đồ (loại + trục/nhãn), hoặc mô tả ảnh minh họa cần sinh.
7. Lưu `exports/bai-giang/<slug>/lop-hoc.md` (+ quiz.md).
8. **Handoff OpenMAIC trong Javis** — xem khối dưới. **Không** bảo user mở domain `openmaic.*` hay Live Demo.

## Handoff OpenMAIC (trong Javis)

Sau khi có `lop-hoc.md`, hướng dẫn:

1. Ở trang **Việc → Bài giảng → Lớp học**, cột Kết quả: bấm **Tạo lớp OpenMAIC**.
2. Javis gọi API self-host (`POST /openmaic/generate`) — user không gõ key / access code.
3. Classroom hiện **iframe** ngay trong panel Kết quả.

Ràng buộc kỹ thuật (server đã xử lý; chỉ nhắc nếu user hỏi):

| Mục | Giá trị |
|-----|---------|
| API `language` | `en-US` (OpenMAIC chỉ nhận en-US\|zh-CN; `vi` sẽ **fallback zh-CN** → giọng Trung) |
| Nội dung | Requirement + script + quiz **tiếng Việt**; Javis ép **8-15 scene** + giảng dạy chi tiết + visual |
| TTS | OpenAI → Javis Edge (Hoài My/Nam Minh); cấm Browser Native / Doubao / Qwen / zh-* |
| Ảnh/biểu đồ | Javis bật `enableImageGeneration` nếu `/api/health` có `imageGeneration=true` (cần provider ảnh trên OpenMAIC) |
| LLM | Model yếu (vd. `gpt-4o-mini`) → slide mỏng / ít hình — ưu tiên Gemini Flash / `gpt-4o` |
| Live Demo | Cấm |

**Không phải giới hạn 1 slide của Javis.** OpenMAIC tự sinh outline từ requirement; nếu LLM chỉ outline 1 cảnh (hoặc các cảnh sau fail rồi bỏ qua) thì classroom vẫn “succeeded” với 1 slide. Javis sẽ cảnh báo khi `scenesCount < 3`.

## Đầu ra

Markdown: mục tiêu, outline, script (VI), quiz, Sources. Cuối: một dòng nhắc bấm **Tạo lớp OpenMAIC** trong Javis.
