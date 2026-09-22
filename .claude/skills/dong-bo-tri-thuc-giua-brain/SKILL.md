---
name: "Đồng bộ tri thức giữa brain"
description: "Đồng bộ có chọn lọc wiki, sources, skills và memory liên quan từ một brain sang brain khác."
description_en: "Selectively sync wiki, sources, skills, and related memory across brains."
group: "AI"
origin: javis-learned
status: active
created: 2026-09-11
---
## Khi nào dùng
Dùng khi người dùng muốn mang một nhóm tri thức đã có ở brain này sang brain khác, ví dụ sách kỹ năng, wiki chuyên đề, skill tư vấn hoặc memory liên quan.

## Chuẩn bị
- Xác định brain nguồn và brain đích.
- Xác định phạm vi đồng bộ: `sources/`, `wiki/`, `skills/`, `memory/facts/` hoặc chỉ một chủ đề cụ thể.
- Đọc index của brain nguồn để tránh lấy thiếu hoặc lấy lan man.
- Kiểm tra brain đích đã có nội dung tương tự chưa để tránh ghi đè nhầm.

## Cách chạy
- Chỉ đọc trước các index chính: `memory/MEMORY.md`, `wiki/index.md`, `Javis/index.md` nếu có.
- Với từng nhóm tri thức, chọn đúng file hoặc thư mục liên quan.
- Sao chép sang cùng cấu trúc ở brain đích nếu người dùng đã yêu cầu thực hiện ghi file.
- Nếu là vòng học read-only, chỉ đề xuất manifest, không ghi file.

## Quy trình
1. Ghi rõ yêu cầu: đồng bộ từ brain nào sang brain nào, chủ đề gì.
2. Kiểm tra trùng lặp trong brain đích.
3. Đồng bộ `sources/` nếu cần giữ tài liệu gốc.
4. Đồng bộ `wiki/` và cập nhật `wiki/index.md` nếu có quyền ghi.
5. Đồng bộ `skills/` nếu tri thức cần dùng như quy trình thao tác.
6. Đồng bộ `memory/facts/` chỉ với ký ức thật sự phù hợp cho brain đích, tránh mang ngữ cảnh riêng không liên quan.
7. Báo cáo ngắn: đã đồng bộ gì, đặt ở đâu, còn thiếu gì.

## Bẫy
- Không đồng bộ toàn bộ memory cá nhân nếu brain đích là dự án khác và không cần ngữ cảnh đó.
- Không dùng link `file://` trong câu trả lời dashboard, dùng đường dẫn tương đối trong vault khi cần hiển thị.
- Không tạo bản sao skill nếu brain đích đã có skill cùng vai trò.
- Không biến tri thức chỉ áp dụng cho APC.HN thành quy tắc chung cho School of Art nếu chưa được người dùng xác nhận.

## Kiểm chứng
- Brain đích có đủ file nguồn được yêu cầu.
- `wiki/index.md` của brain đích có liên kết đến trang wiki mới nếu đã đồng bộ wiki.
- Skill mới có `description` dưới 150 ký tự và có `group`.
- Memory mới không trùng với memory đã có và đúng ngữ cảnh brain đích.
