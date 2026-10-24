---
name: Tử Vi Ziwei
description: "Lập lá số Tử Vi (iztro/ziwei-doushu), tra cổ thư, luận giải chuyên nghiệp."
description_en: "Cast Zi Wei Dou Shu charts (iztro/ziwei-doushu), search classics, professional reading."
group: Nghiên cứu
license: MIT
metadata:
  version: "1.0"
  upstream: "https://github.com/Renhuai123/ziwei-doushu"
---

# Tử Vi Ziwei

Adapter Javis cho [Renhuai123/ziwei-doushu](https://github.com/Renhuai123/ziwei-doushu) (MIT):
lập lá số, tra cổ thư công cộng, luận giải theo quy trình chuyên nghiệp.

Skill giữ hướng dẫn + script. Engine/cổ thư clone ngoài image (`$JAVIS_STATE_DIR/vendor/`).

## Khi nào dùng

- User muốn **lập lá số / tử vi / ziwei / đẩu số / xem mệnh / đại hạn / lưu niên**.
- Đọc và phân tích lá số đã có (JSON hoặc bảng cung).
- Tra khẩu quyết cổ thư (骨髓赋 / 全集 / 全书) làm căn cứ bình giải.

**Không dùng** khi chỉ hỏi khái niệm chung không cần lá số cụ thể (trả lời thẳng),
hay khi user muốn Bát tự / Kỳ môn / Phong thủy thuần (skill khác nếu có).

## Bản quyền (đọc trước khi trích dẫn)

| Nguồn | Giấy phép | Dùng trong Javis |
|-------|-----------|------------------|
| Mã lập lá số upstream + `iztro` | MIT | Được, mọi tenant |
| 骨髓赋 / 紫微全集 / 紫微全书 trong vendor | Công cộng | Được trích kèm tên sách |
| Trích dẫn 倪师《天纪》 (`docs/tianji-ziwei/`) | CC BY-NC-SA 4.0 | Chỉ học tập / phi thương mại; **không** đưa nguyên văn vào sản phẩm bán hoặc báo cáo thương mại |
| Dataset v4.0 (~56GB) | CC BY 4.0 | Không clone mặc định; chỉ khi user yêu cầu rõ |

Chi tiết: `references/ban-quyen.md`.

## Chuẩn bị (mọi VPS / tenant)

1. Engine có Bash + `node` ≥18.
2. `bash .claude/skills/tu-vi-ziwei/scripts/ensure-ziwei.sh` → in `LIB=...` và `RUNTIME=...`.
3. Lần đầu script cài `iztro` vào runtime (nhẹ). Không cài cả Next.js của upstream.

Thiếu Node → báo user, không tự cài system package.

## Cách làm (thứ tự bắt buộc)

### 1. Thu thập đủ dữ liệu sinh

Cần: **năm-tháng-ngày dương lịch**, **giờ sinh** (đồng hồ hoặc giờ chi), **giới tính**,
tên (tuỳ chọn), nơi sinh (tuỳ chọn - ghi chú, chưa hiệu chỉnh chân dương lịch trong CLI).

Thiếu giờ: hỏi 1 lần; nếu chỉ biết khoảng, nêu giả định giờ chi rồi lập.
Bảng giờ chi: `references/gio-sinh.md`.

### 2. Lập lá số (CLI)

```bash
bash .claude/skills/tu-vi-ziwei/scripts/ensure-ziwei.sh
node .claude/skills/tu-vi-ziwei/scripts/lap-la-so.mjs \
  --date 1990-05-15 --hour 14 --minute 30 --gender female \
  --name "Nguyen A" --lang vi-VN \
  --out exports/tu-vi/<slug>/la-so.json
```

- `--hour` + `--minute`: giờ đồng hồ (24h); script đổi sang giờ chi.
- Hoặc `--branch 0..11` (0=Tý … 11=Hợi) nếu user đã biết giờ chi.
- `--lang vi-VN` (mặc định) hoặc `zh-CN`.
- In JSON ra stdout; có `--out` thì ghi file trong vault.

Đọc file JSON trước khi luận. **Không bịa** sao/cung khi chưa có output CLI.

### 3. Tra cổ thư (căn cứ)

```bash
node .claude/skills/tu-vi-ziwei/scripts/tra-co-thu.mjs --query "紫微" --limit 8
node .claude/skills/tu-vi-ziwei/scripts/tra-co-thu.mjs --query "命宫" --book gusuifu
```

Từ khoá nên là **chữ Hán** (tên sao/cung cổ). Map Việt↔Hán: `references/sao-cung-map.md`.

Tianji (NC) chỉ khi user học tập / phi thương mại:

```bash
node .claude/skills/tu-vi-ziwei/scripts/tra-tianji.mjs --query "化忌" --limit 5
```

### 4. Luận giải

Làm theo `references/quy-trinh-luan.md` (Mệnh → tam phương tứ chính → Thân →
tứ hóa → đại hạn/lưu niên nếu hỏi vận). Mỗi nhận định lớn nên gắn 1 trích cổ thư
(sách + đoạn) hoặc nói rõ là suy luận cấu trúc từ lá số.

Giọng: trung thực, không đảm bảo tuyệt đối; không khuyến khích quyết định y tế/pháp lý
chỉ từ lá số. Không em dash.

### 5. Giao kết quả

- Lá số: `[la-so.json](exports/tu-vi/<slug>/la-so.json)` + bảng/tóm tắt 12 cung trong chat.
- Bản luận: `exports/tu-vi/<slug>/luan-giai.md` (khi user muốn lưu).
- Embed đường dẫn relative vault; không `file://`.

## Bẫy

- Đừng vendor dataset 56GB hay cả app Next vào image/vault.
- Đừng `npm install` full upstream (kéo Next) - chỉ runtime `iztro`.
- Đừng trích nguyên văn Tianji vào nội dung thương mại.
- Đừng hứa "em sẽ xem rồi báo lại" - lập và luận **trong lượt này**, hoặc xếp việc nền rõ ràng.
- Description skill ≤150 đã cắt; trigger dài nằm ở mục "Khi nào dùng".

## Kiểm chứng

- [ ] `ensure-ziwei.sh` in `LIB=` và `RUNTIME=`
- [ ] `lap-la-so.mjs` ra JSON có 12 cung
- [ ] Luận có cấu trúc theo quy trình + ít nhất một căn cứ cổ thư khi bình giải sâu
