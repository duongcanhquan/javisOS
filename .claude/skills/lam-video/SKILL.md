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

1. Đọc brief user: chủ đề, mục tiêu, ngôn ngữ, tỉ lệ (9:16|16:9|1:1), độ dài, kênh (Reels/TikTok/YT).
2. Đọc `references/catalog.md` - bảng chọn pipeline.
3. Kiểm tra điều kiện chạy (API key / binary) của pipeline định chọn; thiếu thì nói thẳng và đề xuất phương án khác hoặc Manual prompt-pack.

## Quy trình

### 1. Chốt brief (1 vòng, ngắn)

Nêu lại 4-6 dòng: chủ đề, audience, CTA, tỉ lệ, độ dài, ngôn ngữ, tone. Thiếu 1 tham số hại thì hỏi bằng JAVIS_ASK (tối đa 1 khối). Đoán được thì nêu giả định rồi làm tiếp.

### 2. Nghiên cứu chủ đề

Thu thập 5-8 insight/fact đáng tin (wiki brain + web/MCP nếu có). Ghi nguồn. Không bịa số.

### 3. Viết kịch bản chuẩn

Xuất `beats` hoặc outline shot-by-shot:

- Hook ≤3s (câu mở)
- Mỗi beat: narration + visual + cảm xúc + CTA nếu có
- Nhịp cắt 3-6s/shot; 30s ≈ 6-8 beat; 60s ≈ 10-12 beat
- Ghi rõ text on-screen (tiêu đề) nếu pipeline hỗ trợ

### 4. Chọn pipeline (đọc catalog)

Chọn ĐÚNG MỘT pipeline chính theo catalog. Báo user vì sao chọn. Nếu user chỉ định sẵn (paperdesign / Remotion / Ommi) thì theo user.

### 5. Render theo đúng skill của pipeline

- `paperdesign` → nạp skill `paperdesign`, chạy từ `.claude/skills/paperdesign/` (cần `ATLASCLOUD_API_KEY` + ffmpeg).
- `remotion` → nạp `remotion-best-practices`, tạo/sửa composition Remotion, preview rồi render.
- `ommistudio` / `html-video` → hướng dẫn hoặc gọi OmmiStudio/nexu html-video (cần Node, Playwright, ffmpeg). Ghi brief + template + brand tokens rõ ràng.
- Không đủ điều kiện render → xuất Manual pack: beat map + image prompts + motion prompts + VO script để user dán generator khác.

### 6. Kiểm chứng

Trích frame hoặc mô tả shot-list đối chiếu brief. Lệch thì sửa đúng chỗ (ảnh/prompt/shot), không làm lại cả phim nếu không cần.

## Bẫy

- Nhảy thẳng paperdesign khi user cần motion UI/data viz → nên Remotion.
- Bỏ cổng duyệt beat map / style (paperdesign) → tốn tiền gen sai.
- Shot 10s một mạch trên 9:16 → chết nhịp.
- Hứa "xong em báo lại" mà không giao việc nền / không làm trong lượt.

## Kiểm chứng

- Có file hoặc đường dẫn output rõ (vd `out/<project>/final.mp4`) hoặc Manual pack đủ dùng.
- Pipeline đã chọn khớp catalog + điều kiện môi trường.
- Kịch bản bám brief (hook, CTA, tỉ lệ, ngôn ngữ).
