---
name: Bài giảng lớp học
description: "Gói lớp học tương tác: outline, cảnh, quiz, script giảng; đẩy OpenMAIC self-host tiếng Việt chuẩn."
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
7. **Handoff OpenMAIC** (bắt buộc khi user muốn classroom live) — xem khối dưới.

## Handoff OpenMAIC (chuẩn tiếng Việt)

Luôn dùng **self-host trường**, không Live Demo / không open.maic.chat (mã `sk-…` tạm dễ lệch locale Trung + Browser Native → giọng ngọng).

| Mục | Giá trị |
|-----|---------|
| URL | `https://openmaic.vietmycollege.com` |
| Mã site | `vietmy-openmaic` (nhập 1 lần / trình duyệt) |
| `language` | `vi` (bắt buộc). Cấm `zh` / `zh-CN` / `zh-TW`. Cấm fallback `en-US` khi nội dung là Việt. |
| TTS | OpenAI provider → Javis Edge-TTS. Voice: `nova`/`alloy` (Hoài My) hoặc `onyx`/`echo` (Nam Minh). `enableTTS=true` nếu health.tts. |
| Cấm TTS | Browser Native, speechSynthesis, Doubao, Qwen, mọi `zh-*` |

Khi xong gói markdown, đưa user (hoặc copy sẵn) lệnh kiểu:

```text
Self-hosted OpenMAIC https://openmaic.vietmycollege.com (mã site vietmy-openmaic).
Tạo LẠI classroom từ exports/bai-giang/<slug>/lop-hoc.md (+ quiz.md nếu có).
language=vi — toàn bộ script/quiz/UI tiếng Việt dấu đủ. Không zh, không en-US fallback.
TTS: OpenAI (Edge VI), voice nova hoặc alloy; CẤM Browser Native / Doubao / Qwen / zh-*.
enableTTS=true nếu health cho phép.
Trả một dòng URL classroom tuyệt đối trên openmaic.vietmycollege.com.
```

Trong Javis: **Việc → Bài giảng → Lớp học** → **Copy lệnh OpenMAIC** / Mở OpenMAIC.

## Đầu ra

Markdown có: mục tiêu, outline, script (VI), quiz, Sources, và khối hướng dẫn handoff OpenMAIC ở cuối.
