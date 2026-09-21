---
name: subagent-creator
description: "Hướng dẫn thiết kế và tối ưu subagent: cô lập ngữ cảnh, kịch bản kích hoạt, quy trình thực thi và kiểm định chất lượng."
description_en: "Guide for creating and optimizing AI subagents: isolated context, triggering conditions, execution flow, and quality verification."
group: AI
metadata:
  version: "1.0"
  upstream: "https://github.com/tech-leads-club/agent-skills/tree/main/subagent-creator"
---

# Subagent Creator

Kỹ năng chuẩn hoá và tối ưu hoá các Agent / Subagent chuyên trách trong hệ thống Javis OS và Antigravity.

## Khi nào dùng

- Khi người dùng yêu cầu: "tạo subagent mới", "chuẩn hoá agent hiện có", "tối ưu vai trò agent", "nâng cấp prompt cho agent".
- Khi cần tách một quy trình phức tạp thành các vai trò chuyên biệt có ngữ cảnh độc lập (isolated context).
- Khi điều chỉnh các agent đang có trong `/brains/APC.HN/agents/` để hoạt động chính xác theo metaprompt.

## Chuẩn cấu trúc Agent Javis OS

Một agent chuẩn cần tuân thủ đầy đủ 6 thành phần:

1. **Frontmatter chuẩn:**
   - `type: agent`
   - `name`: Tên tiếng Việt rõ ràng.
   - `slug`: Mã định danh ASCII không dấu, ngăn cách bằng gạch nối.
   - `group`: Nhóm nghiệp vụ (Hợp tác đào tạo, Marketing, Chiến lược, Vận hành, Video...).
   - `skills`: Danh sách slug kỹ năng thực sự cần dùng.
   - `updated`: Ngày cập nhật YYYY-MM-DD.

2. **Khung Metaprompt trong thân file:**
   - **Vai trò & Mục tiêu:** 1 câu nêu vai, 1 câu định nghĩa kết quả tốt nhất.
   - **Bối cảnh nghiệp vụ:** Gắn chặt với APC HN, đối tác, sinh viên, cơ sở Trịnh Văn Bô.
   - **Điều kiện kích hoạt (When to invoke):** Nêu rõ ngữ cảnh tự động giao việc hoặc lệnh trực tiếp.
   - **Quy trình thực thi từng bước (Analysis & Action Process):** Bước 1 -> Bước 2 -> Bước 3.
   - **Định dạng đầu ra chuẩn (Output Format):** Cấu trúc file, biểu đồ, số liệu, link nội bộ.
   - **Rào chắn & Trường hợp ngoại lệ (Guardrails & Edge Cases):** Không bịa số liệu, không em dash, tra soát nguồn thật từ CIS/CMS/Meta.

## Quy trình điều chỉnh Agent

1. **Rà soát danh sách:** Đọc toàn bộ các file `.md` trong `agents/`.
2. **Kiểm tra Frontmatter:** Bổ sung `type: agent`, chuẩn hóa `skills` đúng thực tế, loại bỏ skill thừa.
3. **Nâng cấp Thân Prompt:** Bổ sung điều kiện kích hoạt, quy trình các bước đánh số và định dạng đầu ra.
4. **Kiểm tra Rào chắn:** Tuyệt đối không dùng ký tự em dash, bảo đảm tính thực thi.
