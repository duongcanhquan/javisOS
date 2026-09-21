---
name: "Xử lý cache static Javis"
description: "Chẩn đoán cảnh báo file static cũ và bump VERSION để ép trình duyệt tải lại asset mới."
group: "AI"
origin: javis-learned
status: active
created: 2026-09-11
---
## Khi nào dùng

Dùng khi dashboard Javis báo người dùng vẫn đang chạy bản cũ của một file static như `voice.js`, dù đã tải lại trang hoặc hard refresh.

Dùng khi có dấu hiệu file trên máy chủ đã được sửa nhưng trình duyệt vẫn giữ URL cũ có tham số phiên bản, ví dụ `voice.js?v=0.55.190`.

## Chuẩn bị

- Xác định chính xác file static bị cache, ví dụ `voice.js`.
- Kiểm tra cảnh báo freshness trên dashboard nếu có.
- Kiểm tra phiên bản hiện tại trong file `VERSION` của app.
- Kiểm tra URL asset đang được trình duyệt dùng, đặc biệt tham số `?v=`.

## Cách chạy

1. Đọc cảnh báo cache để biết file nào đang lệch.
2. Kiểm tra file static thật trên máy chủ đã là bản mới chưa.
3. Kiểm tra file `VERSION` đang giữ số phiên bản nào.
4. Nếu nội dung file đã đổi nhưng `VERSION` chưa đổi, bump `VERSION` lên bản mới.
5. Yêu cầu người dùng reload trang một lần để trình duyệt tải URL asset mới.

## Quy trình

1. Xác định triệu chứng:
   - Người dùng thấy thanh cảnh báo dạng vẫn đang chạy bản cũ.
   - Cảnh báo nêu rõ tên file static, ví dụ `voice.js`.

2. Xác định nguyên nhân:
   - Static asset được phục vụ kèm `?v=<VERSION>`.
   - Nếu header cache là dạng dài hạn hoặc immutable, trình duyệt có thể giữ asset rất lâu.
   - Nếu file đã sửa nhưng `VERSION` chưa tăng, URL không đổi nên cache cũ vẫn thắng.

3. Sửa đúng điểm:
   - Không yêu cầu người dùng xoá cache thủ công trước khi kiểm tra version.
   - Bump `VERSION` để sinh URL mới cho asset.
   - Đảm bảo URL mới khác URL cũ, ví dụ từ `voice.js?v=0.55.190` sang `voice.js?v=0.55.191`.

4. Hướng dẫn người dùng:
   - Sau khi bump version, chỉ cần reload trang.
   - Nếu vẫn còn cảnh báo, kiểm tra thêm tầng cache trung gian hoặc service worker nếu hệ thống có dùng.

## Bẫy

- Đừng chỉ bảo người dùng bấm Ctrl+Shift+R nếu nguyên nhân là URL version chưa đổi.
- Đừng nói đã sửa tận gốc khi chưa kiểm tra `VERSION`.
- Đừng sửa file static lặp lại nhiều lần nếu asset mới chưa được phát qua URL mới.
- Đừng dùng lời giải thích quá dài cho người dùng cuối; chỉ nêu nguyên nhân, việc đã làm và thao tác cần reload.

## Kiểm chứng

- `VERSION` đã tăng so với bản cũ.
- HTML/dashboard trỏ tới asset với `?v=` mới.
- Người dùng reload trang và cảnh báo cache biến mất.
- Nếu cảnh báo chưa mất, kiểm tra mã băm file thực tế và mã băm file trình duyệt đang chạy.
