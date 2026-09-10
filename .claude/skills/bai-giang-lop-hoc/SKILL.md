---
name: Bài giảng lớp học
description: "Gói lớp học ấn tượng: kịch bản chi tiết ~1 phút/cảnh, nhấn visual kiểu Remotion, ảnh/biểu đồ, OpenMAIC."
description_en: "Impressive class pack: ~1min scripts/scene, Remotion-style emphasis, charts/images, OpenMAIC."
group: Nội dung
---

# Bài giảng lớp học (ấn tượng, không chỉ chữ)

## Khi nào dùng

User chọn đầu ra **lớp học** / classroom / interactive lesson / OpenMAIC.

**Chuẩn vàng:** mỗi cảnh = **slide sinh động** (ảnh/biểu đồ/nhấn visual) + **lời giảng dài**
(thường **45–75 giây**, cảnh then chốt có thể **~60–90 giây**) gồm giải thích, ví dụ,
chi tiết - **không** đọc to mấy bullet. Kịch bản phải viết đủ trước khi bấm OpenMAIC.

## Chuẩn bị

1. Brief: chủ đề, đối tượng, mục tiêu, thời lượng, ngôn ngữ.
2. Đọc file đính kèm; thiếu fact → `deep-research`.
3. Đọc `references/scene-template.md` (khuôn mỗi cảnh) và `references/visual-motion.md`
   (nhấn kiểu Remotion + ảnh/chart).
4. Tool ảnh: `javis_generate_image` nếu ChatGPT OAuth sẵn; biểu đồ/sơ đồ →
   **`diagram-design`** (HTML/SVG) hoặc mô tả chart có số thật.
5. Motion video riêng (không bắt buộc OpenMAIC): skill **`remotion-best-practices`** /
   **`lam-video`** khi user muốn clip nhấn hiệu ứng ngoài classroom.

## Quy trình (bắt buộc theo thứ tự)

### 1. Outline 8–15 cảnh

Mỗi dòng outline: mục tiêu học + **1 ý then chốt** + loại visual (ảnh / chart / sơ đồ /
so sánh 2 cột / timeline).

### 2. Quiz + PBL

Quiz 4–8 câu; 1 task thực hành ngắn.

### 3. Kịch bản chi tiết từng cảnh (trái tim bài giảng)

Với **mỗi** cảnh dạy, ghi đủ khối trong `scene-template.md`:

| Khối | Yêu cầu |
|------|---------|
| `## Slide` | Tiêu đề + ≤5 bullet ngắn (để NHÌN, không phải để ĐỌC to) |
| `## Visual` | Layout + **emphasis** (phần nào phóng to / highlight / xuất hiện sau) kiểu Remotion |
| `## Ảnh / biểu đồ` | Prompt ảnh hoặc dữ liệu chart; nếu tạo được → lưu `attachments/bai-giang/<slug>/` và embed |
| `## Script giảng` | **45–90 giây** nói: nối cảnh trước → giải thích → ví dụ → chi tiết slide → lỗi hay gặp → takeaway → nối sau |

Luật script:

- Tiếng Việt đủ dấu; không Pinyin / chữ Hán.
- **Chỉ cảnh 1** chào lớp. Cảnh 2+: cấm «Xin chào các em».
- **Dẫn giải slide:** nói theo thứ tự mắt nhìn (bullet 1 → 2 → hình); không chỉ đọc tiêu đề.
- Slide đơn giản vẫn có thể cần **~1 phút** nếu ý cần ví dụ + phản ví dụ + ứng dụng.
- Cấm script mỏng («như trên slide», «xem tiếp»).

### 4. Sinh media (làm trong cùng lượt khi tool sẵn)

- Ảnh minh họa then chốt: `javis_generate_image` → `attachments/bai-giang/<slug>/scene-NN.png`
- Biểu đồ/sơ đồ quan hệ: `diagram-design` → `exports/bai-giang/<slug>/charts/` hoặc `attachments/`
- Ghi đường dẫn vào mục Visual của cảnh tương ứng để OpenMAIC / giảng viên dùng lại.

Thiếu tool → ghi prompt + «cần sinh khi có ChatGPT/diagram»; **không** bỏ mục Visual.

### 5. Ghi file

- `exports/bai-giang/<slug>/lop-hoc.md` (đủ template)
- `exports/bai-giang/<slug>/quiz.md`
- (tuỳ) `motion-notes.md` - danh sách beat nhấn Remotion nếu user muốn làm video sau

### 6. Handoff OpenMAIC

1. **Việc → Bài giảng → Lớp học** → **Tạo lớp OpenMAIC**.
2. Server ép liên mạch + narration dài + visual (xem prompt `/openmaic/generate`).
3. Lớp cũ mỏng / chào lại → **tạo lại** sau khi `lop-hoc.md` đã đủ chi tiết.

| Mục | Giá trị |
|-----|---------|
| API `language` | `en-US` (không gửi `vi`) |
| Nội dung | VI trong requirement; 8–15 scene; script dài |
| TTS | Edge VI qua proxy Javis |
| Ảnh | `enableImageGeneration` nếu health cho phép + ảnh đã gắn trong plan |
| Model | Tránh mini nếu muốn slide/ảnh dày |

## Liên kết

- Điều phối đầu ra → `tao-bai-giang`
- Deck chiếu thuần → `bai-giang-slide` (cùng chuẩn visual + speaker note dài)
- Video explainer → `lam-video` + `remotion-best-practices`
- Sơ đồ editorial → `diagram-design`

## Bẫy

- Không giao lớp chỉ có bullet + TTS đọc bullet.
- Không bịa số trên chart.
- Không em dash.
- OpenMAIC không phải Remotion player: «Remotion» ở đây = **chỉ dẫn nhấn visual** trong
  kịch bản + tùy chọn làm clip Remotion riêng nếu user yêu cầu.

## Kiểm chứng

- [ ] ≥8 cảnh; mỗi cảnh dạy có Script ≥ ~120 từ hoặc rõ 45–90s
- [ ] Cảnh 2+ không chào lại
- [ ] Mỗi cảnh có Visual + (ảnh hoặc chart hoặc mô tả emphasis)
- [ ] Có ví dụ thật trong script, không chỉ định nghĩa
- [ ] File trong `exports/bai-giang/<slug>/`
