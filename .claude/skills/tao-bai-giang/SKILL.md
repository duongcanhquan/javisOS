---
name: Tạo bài giảng
description: "Điều phối tạo bài giảng từ chủ đề/file: chọn đầu ra lớp học, video, slide hoặc văn bản minh họa."
description_en: "Orchestrate lesson creation from a topic/files: classroom, video, slide, or illustrated document."
group: Nội dung
---

# Tạo bài giảng

## Khi nào dùng

- User muốn **làm bài giảng / giáo án / khóa học ngắn** từ chủ đề hoặc file đính kèm.
- User chọn (hoặc hỏi) đầu ra: **lớp học**, **video**, **slide**, **văn bản + ảnh/biểu đồ**.
- Trang **Việc → Bài giảng** hoặc chat "làm bài giảng về …".

## Chuẩn bị

- Models: ưu tiên **Gemini** đã cấu hình (agent seed dùng `model_provider: gemini`).
- Workflow seed: bấm Studio → **Bộ Bài giảng** (hoặc trang Bài giảng → Chuẩn bị năng lực).
- File đính kèm: upload `/upload` rồi ghi đường dẫn vào brief; có thể `ingest-source` nếu cần vào Sources.

## Menu chọn đầu ra (cho giảng viên)

Hỏi **một lần** nếu chưa chọn. Nói rõ + ví dụ, không dùng jargon pipeline:

| Chọn | Khi nào | Ví dụ | Workflow |
|------|---------|-------|----------|
| **Slide trình chiếu** | Dạy trên lớp, chiếu máy chiếu | Quang hợp lớp 8 → 12 slide + notes | `bo-bai-giang-slide` |
| **Video giải thích** | Clip ngắn xem lại / LMS / Zalo | «Vì sao trời xanh?» 75 giây | `bo-bai-giang-video` |
| **Lớp học tương tác** | Buổi live: cảnh, quiz, thực hành | Python biến → outline + quiz + script | `bo-bai-giang-lop-hoc` |
| **Bài đọc + ảnh & biểu đồ** | Handout / đọc trước / gửi phụ huynh | An toàn mạng + checklist | `bo-bai-giang-van-ban` |

Trên dashboard: **Việc → Bài giảng** (thẻ chọn có mô tả + ví dụ). Trong chat: dùng JAVIS_ASK với đúng 4 lựa chọn trên.

## Cách chạy

1. Chốt định dạng (bảng trên).
2. Brief: chủ đề, đối tượng, mục tiêu, ngôn ngữ, file đính kèm nếu có.
3. Chạy workflow tương ứng (Studio / trang Bài giảng / chat).
4. File vào `exports/bai-giang/<slug>/`.


## Brief bắt buộc

Trước khi research/gen, brief phải có:

- Chủ đề (1 dòng rõ)
- Đối tượng học (ai, trình độ)
- Mục tiêu học được gì (2-4 bullet)
- Ngôn ngữ đầu ra
- Định dạng đã chọn

Thiếu → hỏi, **không** giả định rồi làm luôn.

## Lộ trình chung (mọi định dạng)

1. **Đọc & chuẩn bị** - tóm tắt file đính kèm / wiki liên quan.
2. **Tìm hiểu chuyên sâu** - skill `deep-research` (breadth≈3-4, depth≈2) khi thiếu fact.
3. **Viết khung + ví dụ** - outline, ví dụ thật, bài tập ngắn.
4. **Thiết kế ấn tượng** - hook, nhịp, **ảnh/biểu đồ**, điểm nhấn visual (kiểu Remotion);
   với lớp học/slide: **kịch bản nói dài** (thường 45–90s/ý) trước khi gen OpenMAIC/deck.
5. **Sinh media** - `javis_generate_image`, `diagram-design` khi hợp; lưu `attachments/bai-giang/`.
6. **Tạo file** - ghi `exports/bai-giang/<slug>/`, trả đường dẫn.

## Chuẩn chất lượng (lớp học & slide)

- Không chấp nhận gói chỉ có chữ + TTS đọc chữ.
- Script/speaker note phải có giải thích + ví dụ + dẫn giải nội dung đang hiện.
- Mỗi cảnh/slide then chốt có visual emphasis; ưu tiên có ảnh hoặc chart.
- OpenMAIC: liên mạch (không chào lại từng slide) - prompt server + skill `bai-giang-lop-hoc`.

## Bẫy

- Đẩy OpenMAIC chỉ khi user muốn classroom live: **trong Javis** (nút Tạo lớp OpenMAIC). Không mở domain riêng / Live Demo / open.maic.chat.
- API language = `en-US` + nội dung VI + TTS Edge (không gửi `language=vi`  -  sẽ thành zh-CN).
- Đừng gọi OpenMAIC nếu user chỉ cần slide/markdown.
- Đừng render video tốn tiền gen khi brief/beat chưa duyệt.
- Không bịa số liệu; thiếu nguồn thì ghi rõ.
- Không dùng em dash.

## Kiểm chứng

Cuối mỗi gói: mục tiêu học đã cover chưa, có ví dụ/thực hành chưa, file đã nằm trong vault chưa, CTA/bước tiếp theo cho học viên chưa.
