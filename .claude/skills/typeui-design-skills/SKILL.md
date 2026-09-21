---
name: typeui-design-skills
description: "Kho 67 phong cách thiết kế TypeUI (Bento, Sleek, Brutalism...) định hình visual cho landing page, website và slide trình chiếu."
group: Frontend & Design
---

# TypeUI Design Skills

Hệ thống 67 bộ nhận diện và phong cách thiết kế chuẩn (design systems) từ TypeUI (`typeui.sh`), tích hợp sẵn bộ tokens (màu sắc, typography, khoảng cách, bo góc, bóng đổ) và quy tắc thiết kế (do/don't, WCAG 2.2 AA) cho AI agents.

## Khi nào dùng

- Xây dựng **Landing Page / Website**: Khi tạo giao diện bằng Tailwind CSS / HTML qua skill `landing-page`, `htmlanything`, hoặc `frontend-design`.
- Thiết kế **Slide trình chiếu / PDF**: Khi làm pitch deck, slide đề án qua `slide-wright` hoặc văn bản tài liệu cần chuẩn visual định vị cao cấp.
- Chốt **Visual Style / Design Tokens**: Khi user yêu cầu định hình phong cách giao diện (Bento, Brutalism, Sleek, Glassmorphism, Minimal, Darkmode, Cyberpunk, Neo-brutalism, v.v.).

## Cấu trúc thư viện tại chỗ

Mỗi style nằm tại `styles/<slug>/` gồm 2 file chuẩn:
- `DESIGN.md`: Chứa design tokens chi tiết dạng YAML frontmatter (màu sắc hex, font chữ, kích thước, spacing, radius) và tổng quan thiết kế.
- `SKILL.md`: Chứa chỉ dẫn sâu cho AI agent: Brand mission, style foundations, accessibility (WCAG AA), component specs, quy tắc Do/Don't và quality gates.

## Danh mục 67 phong cách theo nhóm

1. **Hiện đại & Tối giản (Modern & Clean)**:
   - `minimal`, `clean`, `modern`, `sleek`, `spacious`, `bento`, `basic`, `square`, `contemporary`
2. **Công nghệ & Tương lai (Tech & Futuristic)**:
   - `agentic`, `claude`, `codex`, `futuristic`, `matrix`, `pulse`, `cosmic`, `levels`, `power`
3. **Mạnh mẽ & Đột phá (Bold & Avant-garde)**:
   - `bold`, `brutalism`, `neobrutalism`, `dramatic`, `expressive`, `industrial`
4. **Hiệu ứng thị giác & Chiều sâu (Visual Effects & Depth)**:
   - `glassmorphism`, `claymorphism`, `neumorphism`, `gradient`, `neon`, `glow`, `perspective`, `immersive`
5. **Biên tập & Xuất bản (Editorial & Premium)**:
   - `editorial`, `storytelling`, `refined`, `premium`, `luxury`, `monochrome`, `mono`
6. **Doanh nghiệp & B2B (Corporate & Enterprise)**:
   - `corporate`, `enterprise`, `professional`, `ant`, `material`, `shadcn`, `roku`
7. **Nghệ thuật & Cổ điển (Artistic, Retro & Playful)**:
   - `artistic`, `cafe`, `colorful`, `creative`, `dithered`, `doodle`, `fantasy`, `fiction`, `flat`, `friendly`, `handdrawn`, `lingo`, `pacman`, `paper`, `retro`, `riso`, `sega`, `sketch`, `skeumorphism`, `stitch`, `terracotta`, `tetris`, `vibrant`, `vintage`

## Quy trình áp dụng

1. **Khảo sát & Chọn phong cách**:
   - Xác định mục tiêu: Trang landing tuyển sinh, slide B2B, hay dashboard học vụ.
   - Chọn phong cách phù hợp trong danh mục trên.
2. **Đọc Tokens từ file tương ứng**:
   - Đọc trực tiếp `styles/<slug>/DESIGN.md` và `styles/<slug>/SKILL.md`.
   - Lấy chính xác bảng màu (primary, neutral, surface, text) và thông số font (display, body, mono).
3. **Áp dụng vào code**:
   - **Landing Page / HTML**: Cấu hình Tailwind config hoặc CSS variables đúng mã màu và font-family trong `DESIGN.md`. Tránh dùng màu ngẫu nhiên hoặc phong cách AI generic.
   - **Slide Wright (16:9 PDF/HTML)**: Đưa bảng màu và tỷ lệ tương phản vào CSS custom slide, bảo đảm chữ to rõ full trang, bố cục card khối mạch lạc.
4. **Kiểm tra chuẩn chất lượng (Quality Gate)**:
   - Độ tương phản đạt WCAG 2.2 AA (tối thiểu 4.5:1 cho text thường).
   - Nhịp điệu khoảng cách (spacing rhythm) nhất quán theo scale.
   - Tuyệt đối không sinh giao diện AI chung chung (generic AI-slop).
