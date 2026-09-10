---
name: landing-page
description: "Landing SaaS HTML/Tailwind: brief hoặc chủ đề → copy, chọn layout, xuất exports/landing + preview chat."
description_en: "SaaS landing HTML/Tailwind: brief or topic → copy, pick layout, write exports/landing + chat preview."
group: Marketing
license: MIT
metadata:
  version: "1.0"
  inspired_by: "https://github.com/cruip/tailwind-landing-page-template"
---

# Landing page (HTML/Tailwind)

Skill hệ thống để **dựng landing từ chat Javis**: nhận brief đầy đủ hoặc chỉ chủ đề,
viết/sửa copy, **chọn layout có chọn lọc** từ catalog, xuất HTML Tailwind standalone,
rồi giao trong vault + xem trước trong chat.

Cảm hứng thẩm mỹ từ [Cruip Simple Light](https://github.com/cruip/tailwind-landing-page-template)
([demo](https://simple.cruip.com/)). **Không** nhúng code GPL của Cruip vào skill này.
Template trong `assets/` là bản MIT gốc của Javis. Chế độ Next.js Cruip chỉ khi user
yêu cầu rõ - xem `references/next-cruip.md`.

## Khi nào dùng

- «làm landing», «trang giới thiệu sản phẩm», «sales page HTML», «landing Tailwind»
- Đưa brief đầy đủ (sản phẩm, đối tượng, CTA, màu) **hoặc** chỉ chủ đề rồi nhờ AI viết
- Sửa / đổi layout / đóng gói zip / chuyển Webcake từ landing vừa tạo

**Không dùng** khi: UI app/dashboard sản phẩm (`frontend-design`), sơ đồ
(`diagram-design`), chỉ bài SEO (`viet-bai-seo`), chỉ audit SEO (`kiem-tra-seo`).

## Chuẩn bị

Đọc đúng file khi tới bước (đừng nạp hết một lần):

| Bước | File |
|------|------|
| Thu thập / giả định brief | `references/intake.md` |
| Viết copy | `references/copy-framework.md` |
| Chọn layout | `references/design-catalog.md` |
| Build HTML | `references/build-html.md` + `assets/starter-simple-light.html` |
| Giao / zip / Webcake | `references/delivery.md` |
| Next.js Cruip (nâng cao) | `references/next-cruip.md` |

Đầu ra mặc định: `exports/landing/<slug>/` trong vault đang chọn.

## Quy trình (bắt buộc đủ cổng duyệt)

### 1. Intake

- Brief đủ → chuẩn hoá thành `BRIEF.md` (mục trong intake).
- Chỉ chủ đề → draft copy theo `copy-framework.md`, ghi giả định rõ, hỏi **tối đa 1–3**
  điểm thiếu nếu đoán sai sẽ hại (giá, CTA, pháp lý). Còn lại nêu giả định rồi làm tiếp.
- Lấy brand/memory nếu có (logo, màu, tên).

### 2. Chọn thiết kế (cổng bắt buộc)

Mở `design-catalog.md`. Đề xuất **2–3** layout khớp brief (không liệt kê cả catalog).
Mỗi option: 1 câu vì sao + 1 rủi ro. Dùng `<!-- JAVIS_ASK -->` nếu ≤4 lựa chọn rõ.

**DỪNG** đến khi user chọn (hoặc nói «bạn chọn giúp» → lấy option khuyến nghị).

### 3. Copy + token thị giác

Ghi trong `exports/landing/<slug>/`:

- `BRIEF.md` - brief chuẩn hoá
- `COPY.md` - headline, sub, features, social proof, FAQ, CTA, meta SEO
- Hiện bản copy ngắn trong chat; sửa theo feedback trước khi build nếu user muốn.

### 4. Build HTML

- Copy `assets/starter-simple-light.html` → `exports/landing/<slug>/index.html` rồi
  **đổi nội dung + token** theo layout đã chọn (`build-html.md`).
- Không để placeholder «Lorem» / «Your Company».
- Mobile-first; 1 CTA chính lặp 2–3 lần; meta title/description/OG cơ bản.
- Ảnh: dùng URL ổn định hoặc `attachments/` + đường dẫn tương đối; thiếu ảnh →
  khối SVG/gradient, **không** bịa stock giả là ảnh thật của khách.

### 5. Giao (mặc định đủ cả ba lớp khi làm được)

Theo `delivery.md`:

1. **Vault** - `index.html` (+ `BRIEF.md`, `COPY.md`); nhúng link markdown vault-relative.
2. **Chat preview** - artifact HTML hoặc nhắc mở `/files/raw` / trình sửa (iframe).
3. **Zip** - `python3 scripts/pack_landing.py <vault>/exports/landing/<slug>` →
   `landing-<slug>.zip` cạnh folder; link tải.
4. **Webcake** (nếu có Node) - nạp `html-to-webcake`, xuất `.pke` cạnh HTML.
5. Báo cáo ngắn: slug, layout đã chọn, đường dẫn, cách mở/tải; hỏi có muốn sửa section nào.

### 6. Chế độ nâng cao Next.js

Chỉ khi user nói rõ «Next.js / Cruip / Vercel». Làm theo `next-cruip.md` (clone vào
`$JAVIS_STATE_DIR/vendor/`, GPL, không ship trong image).

## Liên kết skill khác

| Việc | Skill |
|------|--------|
| Polish spacing sau build | `baseline-ui` |
| A11y / meta sâu | `fixing-accessibility` / `fixing-metadata` |
| HTML → `.pke` | `html-to-webcake` |
| UI app (không phải landing) | `frontend-design` |
| Điều phối MKT | `marketing-hub` |
| Router UI | `ui-skills-root` |

## Bẫy

- Không vendor / copy nguyên component Cruip GPL vào vault hay skill.
- Không bỏ cổng chọn layout rồi tự dựng layout «AI generic».
- Không hứa host public URL trừ khi user đã có hosting; Javis chỉ lưu trong vault.
- Không em dash. Không bịa số liệu khách hàng / chứng chỉ.
- API engines: trả HTML qua file vault, không phụ thuộc shell zip nếu không có - vẫn
  giao `index.html` + hướng dẫn zip tay.

## Kiểm chứng

- [ ] User đã chọn (hoặc ủy quyền) layout từ catalog
- [ ] `exports/landing/<slug>/index.html` mở được, không Lorem
- [ ] Có link markdown trong câu trả lời cuối
- [ ] Zip và/hoặc `.pke` nếu môi trường cho phép; nếu không thì nói rõ thiếu gì
