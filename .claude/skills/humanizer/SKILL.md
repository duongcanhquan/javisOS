---
name: Humanizer
description: "Chấm điểm dấu viết AI (0-100), liệt kê pattern, viết lại cho giống người (EN/VI)."
description_en: "Score AI-writing tells (0-100), list patterns, rewrite so it reads human (EN/VI)."
group: Nội dung
metadata:
  version: "1.0"
  upstream: "https://github.com/Aboudjem/humanizer-skill (MIT; rewritten for Javis)"
---

# Humanizer - check AI + viết lại

Cherry-pick từ [Aboudjem/humanizer-skill](https://github.com/Aboudjem/humanizer-skill)
(MIT). Bản Javis **viết lại** ngắn; không import cả repo / CLI.

## Khi nào dùng

- «check AI», «có dấu AI không», «đoạn này giống ChatGPT»
- «humanize», «bớt giọng AI», «viết lại cho tự nhiên»
- Soát bài SEO / LinkedIn / README / proposal trước khi đăng
- Sửa file `.md` trong vault cho bớt pattern AI

## Chuẩn bị

1. Lấy **đoạn văn** (dán chat) hoặc **đường dẫn file** trong brain.
2. Chọn mode: `detect` (chỉ chấm) / `rewrite` (mặc định) / `edit` (sửa file tại chỗ).
3. Giọng (khi rewrite): `casual` | `professional` | `technical` | `warm` | `blunt`.
   Thiếu → suy từ ngữ cảnh (báo cáo → professional; chat → casual).
4. Nạp `references/patterns.md` khi cần danh sách đầy đủ P1-P55.

## Cách chạy

### Mode `detect` (check AI)

1. Nếu dưới ~40 từ: báo **không đủ tín hiệu**, không chấm số.
2. Quét cluster pattern (không bắt một từ lẻ). Ưu tiên P7, P9, P13, P19, P29, P30, P34.
3. Tính điểm **0-100** (thấp = giống người hơn):

   `score ≈ 4×patterns_hit + 25×(1 - burstiness) + 15×vocab_blacklist_ratio` (kẹp 0-100)

   Burstiness = độ lệch độ dài câu (người cao, AI thấp). Chuẩn hoá thô 0-1 theo cảm nhận đoạn.
4. Trả lời:

```
Điểm AI-tell: NN/100 (Pristine | Mostly human | Mixed | AI-leaning | Pure AI)
Pattern: P7, P9, … (vị trí ngắn)
Lưu ý: ước lượng pattern, không chứng minh ai viết.
```

Thang: 0-20 Pristine · 21-40 Mostly human · 41-60 Mixed · 61-80 AI-leaning · 81-100 Pure AI.

### Mode `rewrite`

1. Detect trước (bước trên).
2. Viết lại: cắt filler, phá triad/parallelism, đổi nhịp câu, giữ **mọi** số/tên/ngày/trích dẫn nguồn.
3. **Không bịa** fact. Thiếu chi tiết cụ thể → hỏi hoặc giữ nguyên chỗ mơ hồ.
4. Self-check 1 lần: còn pattern nào? Sửa đúng chỗ đó.
5. Xuất bản rewrite + (tuỳ chọn) điểm trước/sau. Không dùng em dash (U+2014).

### Mode `edit`

Đọc file vault → sửa prose tại chỗ (giữ code fence, frontmatter, URL, bảng dữ liệu).
Báo diff ngắn: đã đụng mục nào.

## Pattern lõi (nhớ khi detect)

| Nhóm | ID | Dấu hiệu ngắn |
|------|----|----------------|
| Nội dung | P1-P8 | thổi tầm quan trọng, -ing giả sâu, từ AI (delve/leverage/landscape), tránh "là/có" |
| Phong cách | P9-P18 | "không chỉ… mà còn", rule-of-three, em dash, bold trang trí |
| Chatbot | P19-P21 | "I hope this helps", cutoff, "Great question!" |
| Filler | P22-P30 | hedging chồng, kết luận sáng sủa chung, mở "comprehensive overview", câu đều đều |
| Mới | P31-P43 | placeholder `[Your Name]`, markup `citeturn0`, utm chatgpt, treadmill |
| Forensic | P44-P55 | false agency, CoT leak, unicode obfuscation |

Chi tiết + tiếng Việt: `references/patterns.md`.

## Tiếng Việt (thêm)

Cùng rubric; bổ sung cluster hay gặp bản dịch máy / LLM Việt:

- «Trong bối cảnh hiện nay», «Không thể phủ nhận rằng», «Đáng chú ý là»
- «Không chỉ A mà còn B» lặp nhiều lần
- Song song cứng: ba cụm danh từ trừu tượng liên tiếp
- Kết đoạn «Tóm lại, … mở ra nhiều cơ hội»
- Lẫn giọng Anh cứng (Moreover, Furthermore) trong bài Việt

Đừng chấm «sai» chỉ vì tiếng Việt trang trọng / người viết L2.

## Bẫy

- Một từ / một gạch ngang ≠ AI. Chỉ flag **cụm**.
- Đoạn ngắn, văn kỹ thuật lặp thuật ngữ, hoặc văn trước 2022: đừng "sửa cho mới".
- Detector tiếng Anh dễ **false positive** với người không bản ngữ - nêu caveat.
- Điểm tự chấm trong cùng lượt dễ thiên vị: nói rõ là tín hiệu, không phải án.
- Không đụng quote / code / tiêu đề sách khi rewrite.

## Kiểm chứng

- [ ] Mode đúng (detect không viết lại)
- [ ] Có điểm + danh sách pattern hoặc lý do "không đủ chữ"
- [ ] Rewrite giữ fact; không em dash
- [ ] Có câu disclaimer ước lượng
