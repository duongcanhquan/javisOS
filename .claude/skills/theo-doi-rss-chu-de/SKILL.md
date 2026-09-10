---
name: theo-doi-rss-chu-de
description: "Theo dõi RSS/Atom theo chủ đề: gom feed, digest kỳ, lưu exports/research; bổ sung tong-hop-bao-chi."
description_en: "Track topic RSS/Atom feeds: collect, period digest, save exports/research; complements press digest."
group: Nội dung
---

# Theo dõi RSS theo chủ đề

Gom nhiều feed RSS/Atom quanh **một topic** (đối thủ, ngành, luật, công nghệ) → digest
kỳ. Dùng feedparser / Agent-Reach. **Khác** `tong-hop-bao-chi` (danh mục báo cố định
trong `Javis/bao-chi-cau-hinh.md`).

## Khi nào dùng

- «Theo dõi RSS chủ đề X», «digest tuần về đối thủ Y»
- Bổ sung nghiên cứu bằng nguồn blog/newsletter/chuẩn hóa Atom

**Không thay** brief báo chí sáng theo danh mục giáo dục/tài chính có sẵn →
`tong-hop-bao-chi`.

## Chuẩn bị

1. Nạp **`agent-reach`** nếu cần doctor RSS; không bắt buộc nếu parse feed bằng Python
   chuẩn / WebFetch XML.
2. Chốt: chủ đề, danh sách URL feed (hoặc tìm feed từ site), cửa sổ thời gian
   (24h / 7 ngày / tùy).
3. Lưu cấu hình topic (tuỳ chọn) vào
   `exports/research/<slug>/rss-feeds.md` để lần sau tái dùng.

## Quy trình

1. Fetch từng feed; bỏ item ngoài cửa sổ; dedupe theo link/title.
2. Chọn tối đa **15** item đáng đọc (ưu tiên mới + đúng topic).
3. Với mỗi item: title, nguồn, thời gian, link, **1–2 câu** tóm tắt (đọc body khi cần
   qua Jina/WebFetch - không chỉ title nếu user cần chất lượng).
4. Viết digest `exports/research/<slug>/rss-digest-<YYYY-MM-DD>.md`
   (`references/digest-template.md`).
5. Chat: bullet Tin mới + link file. Đề xuất reminder/cron nếu user muốn định kỳ
   (qua `javis_schedule`, kênh báo cáo đủ điều kiện).

## Liên kết

- Báo chí danh mục VN cố định → `tong-hop-bao-chi`
- Đào sâu 1 bài → `deep-research` / WebFetch
- MXH song song → `lang-nghe-mxh`

## Bẫy

- Không bịa giờ xuất bản.
- Feed chết → ghi rõ, không im.
- Tránh dump 100 item không lọc.

## Kiểm chứng

- [ ] Mỗi tin có link đọc được
- [ ] Có ghi cửa sổ thời gian + số feed OK/fail
