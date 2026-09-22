---
name: Tổng hợp & so sánh báo cáo
description: "Đọc báo cáo/tài liệu, tổng hợp và so sánh kỳ hoặc bản A/B, nêu lệch số cùng giả định."
description_en: "Summarize reports; compare periods or A/B; call out number gaps with assumptions."
group: Second Brain
---

# Đọc, tổng hợp, nghiên cứu và so sánh báo cáo

## Khi nào dùng

User gửi / chỉ file báo cáo, PDF, sheet, doc Drive, "so sánh tháng này với tháng trước",
"đối chiếu 2 bản", "chưng cất báo cáo tài chính / vận hành".

## Quy trình

1. Xác định file: đường dẫn vault, ID Drive, hoặc thư đính kèm. **Đọc từng file** bằng
   tool (Workspace / Gmail / `javis_read_file`). Không tóm file chưa mở.
2. Với mỗi nguồn: kỳ báo cáo, đơn vị tiền/số, định nghĩa KPI (nếu tác giả nêu).
3. Bảng so sánh (markdown): chỉ số | nguồn A | nguồn B | lệch | ghi chú giả định.
4. Mâu thuẫn số: giữ cả hai, không chọn một bên im lặng. Ghi `## Mâu thuẫn`.
5. Kết luận: 5–8 gạch việc / rủi ro / câu hỏi còn mở. Citation `[[tên file]]` hoặc
   tên file Drive.
6. Nếu tái dùng: đề xuất trang wiki; ghi `sources/` nếu user muốn lưu.

## An toàn

Không bịa KPI. Ô trống = "không có trong nguồn".
Không gửi báo cáo ra ngoài (email/Zalo) trừ khi user bảo gửi.
