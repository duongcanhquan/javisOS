---
name: Brainstorming & thiết kế hệ thống
description: "Brainstorm & thiết kế hệ thống: Spike/Bounded/Architectural; hard-gate duyệt trước code; spec rồi writing-plans."
description_en: "Brainstorm into system design: Spike/Bounded/Architectural; hard-gate before code; then writing-plans."
group: AI
---

# Brainstorming & Thiết kế Hệ thống (Từ ý tưởng đến bản thiết kế)

## Khi nào dùng

- Cần chuyển ý tưởng thô thành **bản thiết kế kiến trúc (design)** và **đặc tả (spec)** qua đối thoại tự nhiên.
- Dùng **trước khi code** để chọn hướng: kiểm tra khả thi (**Spike**), thay đổi nhỏ trên hệ thống cũ (**Bounded**), hoặc dự án/module mới (**Architectural**).

## Nguyên tắc cốt lõi & chuẩn bị

### Cổng phê duyệt tuyệt đối (HARD-GATE)

**TUYỆT ĐỐI** không gọi bất kỳ skill triển khai (implementation), không viết code sản phẩm, không khởi tạo project cho đến khi người dùng phê duyệt ý định thiết kế. Yêu cầu đơn giản chỉ làm **bản thiết kế ngắn hơn** - không bao giờ được bỏ bước duyệt.

Skill triển khai bị chặn trước cổng gồm (không đủ liệt kê): `frontend-design`, `baseline-ui`, `improve-ui`, `create-design-md` (khi dùng để *xây* UI mới), `diagram-design` (khi dùng để xuất sơ đồ sản phẩm thay vì companion brainstorm), `agent-browser` để tự click triển khai, mọi skill sinh code/video sản phẩm. Sau Architectural + duyệt spec: **chỉ** được nạp skill **`writing-plans`**.

### Đọc bối cảnh

Quét trạng thái dự án hiện tại (files, docs, commit gần nhất) trước khi đặt câu hỏi.

### Single Response Principle

Nếu điều phối đa tác tử (multi-agent) để đọc tài liệu, **parent agent** là người duy nhất tổng hợp và nói với user - tránh sub-agent gửi tin trùng/rác.

### Liên kết skill khác

| Thời điểm | Skill |
|-----------|--------|
| Cần insight thị trường / JTBD sâu trước khi thiết kế sản phẩm | Nạp **`nghien-cuu-thi-truong`** (đọc output, không thay luồng thiết kế) |
| Cần proposal kinh doanh sau khi đã có hướng sản phẩm | Nạp **`proposal-chien-luoc`** (sau khi chốt design ý định, không thay HARD-GATE code) |
| Mockup/diagram thị giác thật (companion tạm trong brainstorm) | Đọc `skills/brainstorming/visual-companion.md` (chỉ khi câu hỏi mang tính thị giác) |
| Sơ đồ editorial HTML/SVG sau khi đã duyệt hướng (xuất file) | Nạp **`diagram-design`** - vẫn sau HARD-GATE nếu đó là deliverable sản phẩm |
| Spec Architectural đã được user duyệt | **Chỉ** nạp **`writing-plans`** |

## Quy trình 3 luồng (phân loại trước khi bắt đầu)

**Thông báo rõ luồng đã chọn ngay trước câu hỏi đầu tiên.** Nếu phát hiện độ phức tạp ẩn giữa chừng: chỉ được **nâng cấp** (vd Bounded → Architectural), không bao giờ hạ cấp.

### A. Luồng Spike (nghiên cứu tính khả thi)

- **Đặc điểm:** Trả lời "Có thể làm được không?" / "Dùng thử thư viện này được không?".
- **Thực thi:** Trình bày kế hoạch thử nghiệm trong 2-3 câu.
- **Chuyển giao:** Đợi user gật đầu → thử nghiệm tốn ít chi phí nhất → báo cáo khuyến nghị.
- **Lưu ý:** Mọi code trong Spike là **nháp (throwaway)**, không đưa vào hệ thống chính. Giữ code = task mới, phân loại lại.

### B. Luồng Bounded (thay đổi có giới hạn)

- **Đặc điểm:** Sửa/thêm tính năng nhỏ vào **luồng code đã tồn tại trong repo** (vd thêm 1 endpoint, đổi 1 flag). App quen nhưng **dự án mới** thì **không** phải Bounded.
- **Thực thi:**
  1. Hỏi câu làm rõ quan trọng (từng câu một).
  2. Trình bày thiết kế ngắn trong chat (phương pháp, file sẽ chạm, cách test).
  3. **DỪNG** và chờ user "Say Yes" / đồng ý rõ.
- **Sau duyệt:** triển khai theo quy trình bình thường (không cần file spec; không bắt buộc `writing-plans`).

### C. Luồng Architectural (kiến trúc hệ thống mới)

- **Đặc điểm:** Dự án mới, module mới, đổi cấu trúc/interface ảnh hưởng rộng.
- **Thực thi:**
  1. **Phạm vi & JTBD:** Quá lớn → nhờ user chia nhỏ. Phân tích Jobs-to-be-Done; thiết kế giảm **Anxiety** và **Inertia** của người dùng hệ thống (có thể lấy metaphor từ nghiên cứu nếu đã nạp `nghien-cuu-thi-truong`).
  2. **Hỏi & đề xuất 2-3 options** kèm trade-off + khuyến nghị. Cắt thừa (YAGNI).
  3. **Visual Companion:** Chỉ đề xuất bật trình duyệt khi câu hỏi **thị giác thật**. UX/UI: nêu rõ tối ưu **Hệ thống 1** (nhanh, trực giác) hay **Hệ thống 2** (đọc kỹ, cấu hình phức tạp). Chi tiết: `visual-companion.md`.
  4. **Thiết kế cấu trúc:** Chia **Unit** độc lập. Mỗi unit trả lời: Làm gì? Input/Output? Phụ thuộc / ảnh hưởng ai nếu đổi? Trình bày từng phần và xin duyệt.
  5. **Viết Spec & rà pháp lý:** Ghi `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`. Nếu lưu dữ liệu cá nhân: bắt buộc kiến trúc có **consent**, mã hóa, API **xóa dữ liệu trong 72 giờ** (bám tinh thần NĐ 13/2023/NĐ-CP). Sửa hết TBD/TODO trong file.
  6. **Chuyển giao:** User review spec. Chỉ khi được chốt → nạp **`writing-plans`**. **Không** gọi skill triển khai nào khác.

## Bẫy (Red flags)

- "Quá đơn giản, không cần thiết kế" → sai; đơn giản = thiết kế 2 câu, vẫn phải duyệt.
- Vừa trình bày vừa bắt đầu làm → phá HARD-GATE.
- "Spike chạy tốt nên giữ code" → output Spike là câu trả lời; tích hợp = task mới.
- Một file khổng lồ ôm đồm thay vì module có interface rõ.
- Gọi `frontend-design` / viết UI production trước khi user duyệt thiết kế.

## Kiểm chứng

1. Đã **nói tên luồng** (Spike / Bounded / Architectural) thành tiếng trong tin nhắn đầu (sau phân loại).
2. Mỗi unit trả lời được 3 câu: nhiệm vụ / I-O / ảnh hưởng khi đổi.
3. Spec (Architectural) sạch, không mâu thuẫn, có bảo mật/consent nếu đụng PII, **đã được user review** trước `writing-plans`.
