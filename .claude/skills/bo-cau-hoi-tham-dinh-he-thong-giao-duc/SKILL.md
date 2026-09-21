---
name: "Bộ câu hỏi thẩm định hệ thống giáo dục"
description: "Soạn bộ câu hỏi thẩm định hệ thống giáo dục theo kỹ thuật, nghiệp vụ, dữ liệu và lộ trình phát triển."
group: "AI"
origin: javis-learned
status: active
created: 2026-09-11
---
## Khi nào dùng
Dùng khi cần chuẩn bị câu hỏi làm việc với nhà cung cấp phần mềm giáo dục, ERP trường học, SIS, LMS, UMS hoặc hệ thống quản trị vận hành nhà trường.

Dùng khi mục tiêu là buộc đối tác trả lời rõ bằng bằng chứng, demo, tài liệu kỹ thuật, cam kết pháp lý hoặc lộ trình nghiệm thu, thay vì trả lời chung chung.

## Chuẩn bị
- Xác định hệ thống đang dùng và hệ thống được đề xuất thay thế.
- Thu thập danh sách phân hệ hiện có, phân hệ thiếu, dữ liệu nhạy cảm, nhóm người dùng và nghiệp vụ đặc thù.
- Đọc các ghi chú hoặc báo cáo so sánh đã có trong memory, wiki hoặc projects.

## Cách chạy
- Tách câu hỏi thành các tầng: bảo mật dữ liệu, kiến trúc kỹ thuật, nghiệp vụ lõi, tính năng thiếu, vận hành triển khai, chi phí, chủ quyền phát triển.
- Với mỗi tầng, viết câu hỏi buộc đối tác trả lời bằng trạng thái hiện có, bằng chứng demo, tài liệu hoặc cam kết bằng văn bản.
- Gắn thêm tiêu chí nghiệm thu để tránh câu trả lời kiểu 'sẽ phát triển sau'.

## Quy trình
1. Chốt mục tiêu của cuộc họp: nghiệm thu, phản biện, lựa chọn hệ thống, hay yêu cầu bổ sung.
2. Liệt kê nghiệp vụ không thể gián đoạn.
3. Chuyển từng nghiệp vụ thành câu hỏi 'đã có chưa, demo ở đâu, dữ liệu nằm bảng nào, ai vận hành, ai chịu trách nhiệm'.
4. Với dữ liệu nhạy cảm, hỏi rõ Data Controller, Data Processor, nơi lưu trữ, backup, audit log, quyền truy cập kỹ sư và cơ chế xuất dữ liệu.
5. Với phát triển tương lai, hỏi rõ quyền roadmap, SLA phát triển, API, webhook, export schema, sandbox, môi trường test và quyền tự tích hợp.
6. Với tính năng thiếu, yêu cầu phân loại: đã có trên production, có trên staging, đang phát triển, hay mới là ý tưởng.
7. Kết thúc bằng bảng điều kiện: dùng ngay, dùng song song, pilot có giới hạn, hoặc chưa dùng.

## Bẫy
- Không dùng câu hỏi cảm tính như 'có tốt không'. Hỏi bằng điều kiện kiểm chứng.
- Không biến lời hứa roadmap thành năng lực hiện có.
- Không bỏ qua pháp lý dữ liệu cá nhân, dữ liệu học sinh, phụ huynh và cán bộ.
- Không chỉ hỏi tính năng màn hình. Phải hỏi cả dữ liệu, phân quyền, backup, log, API và trách nhiệm khi sự cố.

## Kiểm chứng
- Mỗi câu hỏi quan trọng phải có dạng câu trả lời mong đợi hoặc bằng chứng cần cung cấp.
- Bộ câu hỏi phải bao phủ ít nhất 4 nhóm: kỹ thuật, nghiệp vụ, bảo mật dữ liệu, lộ trình phát triển.
- Nếu đang so sánh thay thế hệ thống, phải có tiêu chí 'không được làm mất nghiệp vụ hiện đang chạy'.
