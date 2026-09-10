---
name: Bài giảng slide
description: "Deck slide ấn tượng: 1 ý/slide, speaker note dài, nhấn visual, ảnh/biểu đồ, xuất md/HTML."
description_en: "Impressive slide decks: one idea/slide, long speaker notes, visual emphasis, charts/images."
group: Nội dung
---

# Bài giảng slide

## Khi nào dùng

User chọn đầu ra **slide** / PowerPoint-style deck / trình chiếu.

**Chuẩn:** slide để NHÌN; **speaker note** mới là bài giảng (thường 45–90 giây nói /
slide then chốt). Có ảnh hoặc biểu đồ; có điểm nhấn visual (kiểu Remotion).

## Quy trình

1. Brief: chủ đề, đối tượng, số slide (mặc định 10-16), ngôn ngữ.
2. Research ngắn nếu thiếu fact (`deep-research`).
3. Outline: 1 slide = 1 ý; hook đầu; tóm tắt cuối; CTA.
4. Mỗi slide ghi đủ:
   - Tiêu đề + 3-5 bullet ngắn
   - **Emphasis:** yếu tố phóng to / highlight / thứ tự hiện (xem tinh thần
     `bai-giang-lop-hoc/references/visual-motion.md`)
   - **Ảnh hoặc biểu đồ:** `javis_generate_image` / `diagram-design` khi sẵn; embed path
   - **Speaker note** đoạn văn dài: giải thích + ví dụ + chi tiết (không 2 câu rỗng)
5. Palette 1 câu; tránh tường chữ.
6. Xuất `exports/bai-giang/<slug>/slides.md` (+ HTML tuỳ chọn; Webcake qua `html-to-webcake`).
7. User muốn video nhấn motion → `lam-video` / `remotion-best-practices` từ cùng outline.

## Liên kết

Lớp OpenMAIC tương tác → `bai-giang-lop-hoc`. Điều phối → `tao-bai-giang`.

## Bẫy

Không nhồi >6 bullet/slide. Không bịa số trên biểu đồ. Không speaker note chỉ đọc bullet.
