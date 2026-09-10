---
name: tom-tat-video
description: "Tóm tắt YouTube/Bilibili: phụ đề/search → outline, quote, timestamp; lưu sources/research."
description_en: "Summarize YouTube/Bilibili: captions/search → outline, quotes, timestamps; save sources/research."
group: Nội dung
---

# Tóm tắt video (YouTube / Bilibili)

Lấy phụ đề hoặc mô tả có cấu trúc từ video công khai → outline, ý chính, quote +
timestamp. Ưu tiên Agent-Reach (`yt-dlp` / `bili-cli`).

## Khi nào dùng

- «Tóm tắt video này», «YouTube nói gì», «Bilibili tìm … rồi tóm»
- Nghiên cứu trước khi làm video / bài giảng / fact-check từ talk

**Không dùng** cho transcript họp nội bộ (`phan-tich-cuoc-hop`).

## Chuẩn bị

1. Nạp **`agent-reach`** → doctor YouTube/Bilibili.
2. Input: URL video **hoặc** từ khóa search (giới hạn 3–5 video rồi hỏi user chọn nếu nhiều).
3. Thiếu phụ đề → nói rõ; thử mô tả + chapter; không bịa lời nói trong video.

## Quy trình

1. Lấy metadata (title, channel, duration, URL).
2. Trích phụ đề / transcript (yt-dlp hoặc backend doctor chỉ định).
3. Viết:
   - Tóm tắt 5–10 dòng
   - Outline theo mục / timestamp
   - 3–7 quote then chốt (kèm thời điểm nếu có)
   - Góc dùng lại (học / content / phản biện)
4. Lưu `sources/research/<slug>/video-<id>.md` (và bản ngắn trong chat).
5. User đang làm video → đề xuất đưa insight sang `lam-video` / `deep-research`.

Mẫu: `references/report-template.md`.

## Fallback

- Không Reach: WebFetch trang video (mỏng) + Tavily về chủ đề; **không** giả vờ có transcript.
- `agent-browser` chỉ khi cần đọc UI; không thay phụ đề.

## Bẫy

- Không bịa timestamp.
- Tôn trọng bản quyền: tóm tắt nghiên cứu, không dump toàn bộ script dài để tái xuất bản nguyên văn.
- Phân biệt Bilibili vs YouTube backend (không dùng yt-dlp cho B站 nếu doctor bảo hỏng).

## Kiểm chứng

- [ ] Có URL video + title
- [ ] Có Sources / đường dẫn file
- [ ] Nêu được đã có phụ đề hay chỉ metadata
