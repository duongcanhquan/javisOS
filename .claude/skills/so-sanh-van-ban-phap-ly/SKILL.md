---
name: so-sanh-van-ban-phap-ly
description: "So sánh / đối chiếu hai (hoặc nhiều) văn bản pháp lý đã có trong wiki hoặc sources/phap-che: bảng theo Điều, điểm giống/khác, xung đột."
description_en: "Compare legal instruments already in wiki or sources/phap-che: article matrix, overlaps, conflicts."
group: AI
---

# So sánh văn bản pháp lý

## Khi nào dùng

"So ND-A với ND-B", "điều này còn hiệu lực không khi có luật mới", "đối chiếu hợp đồng với
nghị định X".

## Cách làm

1. Xác định **đúng** các văn bản (số hiệu + năm). Dùng `phap_che_search` nếu có.
2. Đọc trang wiki / `sources/phap-che/...md` tương ứng (đủ Điều liên quan — không chỉ tóm tắt).
3. Lập bảng:

| Chủ đề / Điều | Văn bản A | Văn bản B | Ghi chú |
|---|---|---|---|
| ... | Điều … | Điều … | khớp / lệch / xung đột |

4. Mục **Xung đột / khoảng trống**: liệt kê chỗ mâu thuẫn hoặc một bên im lặng.
5. Mục **Khuyến nghị vận hành** (không phải kết luận pháp lý tuyệt đối): việc cần hỏi luật sư /
   cần bổ sung nguồn.
6. Nếu kết quả tái dùng được → đề xuất lưu `wiki/phap-che/so-sanh-<a>-vs-<b>.md` + dòng trong
   `wiki/index.md`.

## Cấm

- So sánh khi chưa đọc được ít nhất một nguồn trong kho (trừ khi user dán nguyên văn vào chat).
- Bịa số Điều. Thiếu thì ghi "không thấy trong bản đã lưu".
