---
name: "Tra cứu CMS sinh viên"
description: "Tra cứu CMS sinh viên VietMyCollege theo tên, mã SV, lớp, ngành, khóa và tổng hợp trạng thái học phí."
description_en: "Look up VietMyCollege student CMS by name/ID/class/major/cohort; summarize tuition status."
group: "Operations"
origin: javis-learned
status: active
created: 2026-09-14
---
## Khi nào dùng
Dùng khi anh Quân hỏi về dữ liệu sinh viên APC HN từ CMS VietMyCollege: tìm sinh viên theo tên, mã sinh viên, số điện thoại, email; kiểm tra tình trạng học tập, lớp, ngành, khóa, học phí; hoặc tổng hợp số lượng sinh viên theo lớp/ngành/khóa.

## Chuẩn bị
- Đọc memory/MEMORY.md để kiểm tra thông tin kết nối CMS đã lưu.
- Nếu cần chi tiết kết nối, đọc memory/facts/business-ket-noi-cms-doc-du-lieu-sinh-vien-voi-javis.md.
- Chỉ dùng quyền đọc dữ liệu. Không ghi, sửa, xóa dữ liệu CMS.
- Nếu có script truy vấn sẵn trong brain, ưu tiên dùng script đó thay vì tự dựng request mới.

## Cách chạy
- Xác định ý định truy vấn: tìm cá nhân hay tổng hợp danh sách.
- Nếu tìm cá nhân, ưu tiên khóa định danh mạnh theo thứ tự: mã sinh viên, số điện thoại, email, họ tên đầy đủ.
- Nếu tổng hợp, xác định bộ lọc: ngành, khóa, lớp, hệ đào tạo, trạng thái sinh viên, tình trạng học phí.
- Gọi CMS hoặc script truy vấn đã có trong brain để lấy dữ liệu thật.
- Không tự bịa số liệu nếu CMS không trả dữ liệu hoặc endpoint không có trường cần hỏi.

## Quy trình
1. Chuẩn hóa câu hỏi thành bộ lọc rõ ràng.
2. Kiểm tra xem câu hỏi cần dữ liệu hiện tại hay chỉ cần nhắc lại snapshot cũ.
3. Với dữ liệu hiện tại, gọi CMS trực tiếp.
4. Với kết quả cá nhân, nếu có nhiều bản ghi cùng tên, trình bày từng bản ghi và chỉ rõ điểm khác nhau.
5. Với kết quả tổng hợp, đếm tổng, chia theo lớp/khóa/ngành/trạng thái/học phí nếu dữ liệu có đủ trường.
6. Ghi rõ thời điểm truy vấn trong câu trả lời.
7. Nếu thiếu endpoint điểm danh hoặc dữ liệu lớp học phần, nói rõ CMS hiện chưa cung cấp dữ liệu đó trong API đang dùng.
8. Kết luận bằng 1 đến 3 hành động đề xuất, ví dụ yêu cầu CMS mở thêm endpoint điểm danh hoặc xuất danh sách đối soát.

## Bẫy
- Không gọi nhầm CMS là CIS nếu người dùng đã đính chính đây là CMS.
- Không coi một bản ghi tuyển sinh và một bản ghi học tập là hai người khác nhau nếu trùng thông tin định danh.
- Không khẳng định dữ liệu điểm danh nếu API hiện tại chưa có endpoint điểm danh chi tiết.
- Không công khai API key hoặc token trong câu trả lời.
- Không đưa thông tin nhạy cảm dài dòng nếu người dùng chỉ hỏi số lượng tổng hợp.

## Kiểm chứng
- Với tổng hợp số lượng, kiểm tra tổng các nhóm con phải bằng tổng chính.
- Với tỷ lệ phần trăm, tính lại từ mẫu số thực tế và làm tròn hợp lý.
- Với danh sách sinh viên, kiểm tra mỗi dòng có tối thiểu họ tên, mã sinh viên, lớp và trạng thái liên quan.
- Nếu kết quả khác snapshot cũ trong memory, nêu rõ đây là dữ liệu mới tại thời điểm truy vấn.
