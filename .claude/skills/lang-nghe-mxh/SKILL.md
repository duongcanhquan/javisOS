---
name: lang-nghe-mxh
description: "Lắng nghe MXH theo chủ đề: XHS/X/Reddit/FB… → chủ đề, cảm xúc, quote + nguồn; exports/research."
description_en: "Social listening by topic: XHS/X/Reddit/FB… → themes, sentiment, quotes + sources; exports/research."
group: Marketing
---

# Lắng nghe mạng xã hội

Thu thập **chủ đề / cảm xúc / câu nói điển hình** trên MXH về một topic, có nguồn.
Dựa trên [Agent-Reach](https://github.com/Panniantong/Agent-Reach) khi có; không thay
báo cáo Page/Ads Meta chính thức.

## Khi nào dùng

- «Mọi người nói gì về X», «trend XHS», «Reddit nghĩ sao», «lắng nghe MXH»
- Voice khách cho nghiên cứu thị trường / content / báo cáo tháng (phần cảm nhận)

**Không dùng** cho số Ads/Page chính thức (`bao-cao-facebook-ads`, `tong-ket-facebook`).

## Chuẩn bị

1. Nạp **`agent-reach`**: doctor nhanh; ghi kênh dùng được.
2. Chốt: **chủ đề**, **kỳ** (vd 7/30 ngày hoặc «hiện tại»), **nền tảng ưu tiên**
   (VN mặc định nghiêng XHS/FB cảm nhận; global: Reddit/X/YT comment).
3. Không có Reach/shell → Tavily + WebFetch + nói rõ thiếu MXH gốc.

## Quy trình

1. **Fan-out tìm** trên 2–4 kênh còn sống (không mở hết 15). Mỗi kênh ≥3 URL/bài hữu ích
   hoặc ghi «kênh lỗi: …».
2. **Rút signal** (không đếm like bịa):
   - Chủ đề lặp (theme)
   - Cảm xúc chủ đạo + ngoại lệ
   - Pain / desire / objection
   - 5–10 quote ngắn kèm link
3. **Ghi file** `exports/research/<slug>/social-listening.md` theo mẫu
   `references/report-template.md`.
4. Chat: tóm tắt 8–12 dòng + link file + 1–3 việc gợi ý (content / sản phẩm / CSKH).
5. Nếu user đang làm nghiên cứu thị trường → đề xuất nạp/merge vào
   `nghien-cuu-thi-truong` mục voice khách.

## Liên kết

- Doctor kênh → `agent-reach`
- Đào sâu web song song → `deep-research`
- Trend → lịch bài → `y-tuong-noi-dung-tu-trend`
- Video liên quan → `tom-tat-video`

## Bẫy

- Không bịa số view/like/share.
- Không kết luận «toàn dân ghét» từ 5 comment.
- Không đăng / trả lời hộ user trên MXH.

## Kiểm chứng

- [ ] Có mục Sources (URL)
- [ ] Có ghi kênh Reach/Tavily nào dùng
- [ ] File nằm trong `exports/research/<slug>/`
