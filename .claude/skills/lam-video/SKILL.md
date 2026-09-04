---
name: Làm video
description: "Điều phối làm video: chọn pipeline (paperdesign/Remotion/OmmiStudio), nghiên cứu, viết kịch bản, render đúng brief."
description_en: "Orchestrate video: pick pipeline (paperdesign/Remotion/OmmiStudio), research, script, render to brief."
group: Nội dung
---

# Làm video - điều phối đa pipeline

## Khi nào dùng

User muốn làm video / short / explainer / quảng cáo / Remotion / collage Vox / paperdesign /
OmmiStudio / html-video / motion graphics. Dùng skill này TRƯỚC khi nhảy vào một pipeline cụ thể.

## Chuẩn bị

1. Đọc `references/brief-checklist.md` - cổng brief bắt buộc.
2. Đọc brief user theo checklist; thiếu mục BẮT BUỘC → DỪNG (xem bước 1).
3. Đọc `references/catalog.md` - bảng chọn pipeline.
4. Kiểm tra điều kiện chạy (API key / binary) của pipeline định chọn; thiếu thì nói thẳng và đề xuất phương án khác hoặc Manual prompt-pack.

## Quy trình

### 1. Cổng brief (BẮT BUỘC - không bỏ)

Đọc `references/brief-checklist.md`.

**Bắt buộc đủ trước khi nghiên cứu / viết beat / gen / render:** chủ đề, mục tiêu, độ dài, tỉ lệ, ngôn ngữ.

- Thiếu bất kỳ mục bắt buộc nào → **DỪNG**. Nêu lại những gì đã có. Hỏi phần thiếu (chat web: tối đa 1 khối JAVIS_ASK cho lựa chọn kín như độ dài/tỉ lệ/mục tiêu; mục mở hỏi bằng lời). Telegram: danh sách đánh số.
- **CẤM** "thiếu thì nêu giả định rồi làm tiếp" với 5 mục bắt buộc.
- Mục nên-có (audience, kênh, CTA, tone, pipeline, tài sản A/B/C-roll, cấm brand): nếu thiếu, hỏi 1 vòng hoặc nêu giả định **rõ ràng** và **chờ user xác nhận** trước khi gen tốn tiền (Atlas).
- Khi đủ: chốt brief 5-8 dòng (bullet), ghi "Brief đã chốt", rồi mới sang bước 2.

Mẫu dán nhanh cho user (copy từ checklist) nếu họ muốn chạy workflow một phát.

### 2. Nghiên cứu chủ đề (deep-research)

Chỉ sau khi brief đã chốt. Nạp skill **`deep-research`**: chạy vòng breadth/depth (mặc định 4×2) qua Tavily/WebSearch, rút learnings có nguồn, rồi chưng 5-8 insight then chốt + 3 góc hook cho video. Ghi Sources. Không bịa số.

### 3. Viết kịch bản chuẩn

Xuất `beats` hoặc outline shot-by-shot:

- Hook ≤3s (câu mở)
- Mỗi beat: narration + visual + cảm xúc + CTA nếu có
- Nhịp cắt 3-6s/shot; 30s ≈ 6-8 beat; 60s ≈ 10-12 beat
- Ghi rõ text on-screen (tiêu đề) nếu pipeline hỗ trợ

Với paperdesign: beat map là cổng duyệt thứ hai - show user trước khi gen ảnh.

### 4. Chọn pipeline (đọc catalog)

Chọn ĐÚNG MỘT pipeline chính theo catalog. Báo user vì sao chọn. Nếu user chỉ định sẵn (paperdesign / Remotion / Ommi) thì theo user. Kiểm tra key/binary; thiếu → manual hoặc đổi pipeline.

### 5. Render theo đúng skill của pipeline

- `paperdesign` → nạp skill `paperdesign`, chạy từ `.claude/skills/paperdesign/` (cần `ATLASCLOUD_API_KEY` + ffmpeg). Duyệt beat + style trước khi gen.
- `remotion` → nạp `remotion-best-practices`, tạo/sửa composition Remotion, preview rồi render.
- `ommistudio` / `html-video` → hướng dẫn hoặc gọi OmmiStudio/nexu html-video (cần Node, Playwright, ffmpeg). Ghi brief + template + brand tokens rõ ràng.
- Không đủ điều kiện render → xuất Manual pack: beat map + image prompts + motion prompts + VO script để user dán generator khác.

### 6. Kiểm chứng

Trích frame hoặc mô tả shot-list đối chiếu brief đã chốt. Lệch thì sửa đúng chỗ (ảnh/prompt/shot), không làm lại cả phim nếu không cần.

## Bẫy

- Nhảy thẳng paperdesign khi user cần motion UI/data viz → nên Remotion.
- Bỏ cổng brief / bỏ duyệt beat map / style (paperdesign) → tốn tiền gen sai.
- Đoán độ dài/tỉ lệ/ngôn ngữ rồi gen Atlas → lãng phí.
- Shot 10s một mạch trên 9:16 → chết nhịp.
- Hứa "xong sẽ báo lại" mà không giao việc nền / không làm trong lượt.

## Kiểm chứng

- Brief đã chốt (5 mục bắt buộc) trước research/render.
- Có file hoặc đường dẫn output rõ (vd `out/<project>/final.mp4`) hoặc Manual pack đủ dùng.
- Pipeline đã chọn khớp catalog + điều kiện môi trường.
- Kịch bản bám brief (hook, CTA, tỉ lệ, ngôn ngữ).
