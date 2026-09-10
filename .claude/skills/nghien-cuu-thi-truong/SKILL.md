---
name: Nghiên cứu thị trường chuyên sâu
description: "Nghiên cứu thị trường chuyên sâu: tâm lý JTBD, pháp lý STEEPLE, văn hóa; TAM/SAM/SOM chéo; insight cho proposal."
description_en: "Deep market research: JTBD psychology, STEEPLE/legal, culture; triangulated TAM/SAM/SOM; insights for proposals."
group: Marketing
---

# Nghiên cứu thị trường chuyên sâu cho chiến lược & proposal

## Khi nào dùng

- User cần proposal, kế hoạch kinh doanh hoặc marketing có số liệu thị trường kết hợp với phân tích tâm lý, pháp lý và văn hóa sâu sắc.
- Cần thiết kế khung nghiên cứu đa chiều trước khi lập chiến lược.
- Cần tổng hợp đối thủ, xu hướng, phân khúc khách hàng không chỉ ở bề mặt mà chạm tới động lực ngầm hiểu và tiềm thức ra quyết định.

## Chuẩn bị

1. Đọc `memory/MEMORY.md` và facts liên quan (ngành, sản phẩm, mục tiêu user).
2. Nếu user đã gửi tài liệu nội bộ → đọc trong vault trước khi tra web để bảo vệ lợi thế cạnh tranh và làm mỏ neo dữ liệu.
3. Có **Tavily** hoặc WebSearch → dùng tra tin mới, báo cáo ngành, đối thủ theo mô hình **Phân tán (Fan-out)** để tối ưu thời gian.
4. Có MCP bán hàng/quảng cáo → lấy số thật nội bộ (doanh thu, kênh, CAC, LTV) nếu liên quan.
5. Nạp skill **`deep-research`** để đào sâu web theo breadth 3-5, depth 2 trước khi viết khung.
6. Cần **voice khách / cộng đồng / “đang nói gì trên MXH”** → nạp **`lang-nghe-mxh`**
   (và `agent-reach` nếu dùng CLI). RSS ngành tùy chọn: **`theo-doi-rss-chu-de`**.
   Đưa quote + theme vào mục JTBD / objection; **không** thay số nội bộ bằng like MXH.

## Quy trình

### Bước 0 - Deep research (bắt buộc khi cần số/nguồn ngoài)

Chạy `deep-research` trên câu hỏi nghiên cứu. Lấy learnings + Sources làm nguyên liệu cho các bước dưới. Tuyệt đối không để dữ liệu này phá vỡ khung phân tích - dùng nó để **đổ đầy** các luận điểm.

### Bước 1 - Làm rõ phạm vi (30 giây suy nghĩ, không hỏi lan man)

Ghi vào đầu báo cáo:

- **Sản phẩm/dịch vụ** và **thị trường mục tiêu** (địa lý, đặc tính văn hóa, B2B/B2C).
- **Mục tiêu nghiên cứu** (vd: ra proposal, mở segment mới, định giá).
- **Giả định & Khoảng trống dữ liệu:** minh bạch hóa 3-5 giả định cốt lõi. Nêu thẳng những gì chưa rõ, không im lặng.

### Bước 2 - Thiết kế khung nghiên cứu

Chọn mục phù hợp (bỏ mục không liên quan):

| Khối | Nội dung |
|---|---|
| Quy mô thị trường | TAM / SAM / SOM. Bắt buộc **Đối chiếu chéo (Triangulation)** giữa Top-down và Bottom-up. Dùng **Ước lượng Fermi** cho thị trường mới (nêu rõ 3 kịch bản: Cơ sở, Tích cực, Tiêu cực). |
| Phân khúc KH & Tâm lý | Phân tách hành vi theo **Hệ thống 1** (Cảm xúc/Nhanh) & **Hệ thống 2** (Lý trí/Chậm). Phân tích động lực chuyển đổi qua **4 Lực lượng JTBD** (Lực đẩy, Lực kéo, Sự lo âu, Sức ỳ). |
| Đặc tính Văn hóa | Mổ xẻ sự khác biệt tiêu dùng vùng miền nếu có (vd: tính tập thể, sĩ diện ở Hà Nội vs. tính cá nhân, thực dụng ở TP.HCM). |
| Đối thủ cạnh tranh | 3-5 đối thủ trực tiếp. Bóc tách rõ **Định vị (Positioning)**, chiến lược giá, và khoảng trống chiến lược (white space). |
| Xu hướng & Pháp lý | Quét **STEEPLE**. Đánh giá rủi ro tuân thủ về bảo vệ dữ liệu cá nhân (vd: Nghị định 13/2023/NĐ-CP, ràng buộc về quyền rút sự đồng ý và dữ liệu nhạy cảm). |
| Cơ hội & Rủi ro | SWOT mở rộng (tích hợp rủi ro pháp lý và điểm mù tâm lý học). |
| Insight hành động | 5-7 insight phi hiển nhiên, dùng được ngay làm đòn bẩy cho chiến lược. |

### Bước 3 - Thu thập & tổng hợp

- Ưu tiên: số liệu nội bộ (MCP) > vault > tra web.
- Tránh bẫy **"Khoảng cách Nói - Làm" (Say-Do gap):** sự đứt gãy giữa khảo sát tự báo cáo và hành vi thực tế; luôn tìm dữ liệu hành vi thực tế để đối chiếu.
- Mỗi claim quan trọng: **nguồn** (link hoặc "ước tính Fermi nội bộ").
- Không bịa số. Thiếu data → ghi "Cần bổ sung: ..." và nêu cách lấy.
- Tuân thủ nguyên tắc **một phản hồi duy nhất (Single response)** để loại bỏ trùng lặp thông tin khi tổng hợp.

### Bước 4 - Đầu ra

Viết báo cáo markdown theo cấu trúc trên. Dùng ngôn ngữ chuyên gia, tập trung vào phân tích nhân quả. Kết thúc bằng **5 insight then chốt** (bullet) cho bước chiến lược tiếp theo.

Khi user cần proposal / GTM / chiến lược KD-MKT ngay sau nghiên cứu → nạp skill **`proposal-chien-luoc`** và đưa 5 insight then chốt + SOM/STEEPLE/JTBD làm đầu vào (không dump cả báo cáo).

## Bẫy

- Nhầm Google Search Console (SEO site mình) với nghiên cứu thị trường chung.
- Liệt kê đối thủ không nói positioning → vô dụng cho chiến lược.
- Khai báo một TAM khổng lồ nhưng không thu hẹp được SAM/SOM thực tế hoặc không có phương pháp luận → bị coi là báo cáo sáo rỗng.
- Chỉ tập trung khuếch đại Lực kéo và Lực đẩy mà bỏ qua các giải pháp triệt tiêu **Sự lo âu** và **Sức ỳ** của khách hàng.

## Kiểm chứng

Trước khi nộp:

1. Mọi mục lớn có ít nhất 1 nguồn hoặc 1 giả định được ghi rõ.
2. Quy mô thị trường (nếu có) phải được tính toán chéo, không dùng một con số vô căn cứ.
3. Có ≥3 insight không có trong Wikipedia mù (phi hiển nhiên, chạm đến rào cản tiềm thức hoặc rủi ro pháp lý).

## Bước tiếp theo

- Proposal tóm tắt: skill **`proposal-chien-luoc`** / workflow **`nghien-cuu-thi-truong-chuyen-sau`**.
- Kế hoạch KD + MKT + vận hành chi tiết: workflow **`ke-hoach-kd-mkt-tu-nghien-cuu`** (skills `phan-tich-tai-chinh-mkt`, `ke-hoach-kinh-doanh`, `ke-hoach-marketing`, `quy-trinh-van-hanh-kd-mkt`).
