---
name: Xuất gói nghiên cứu
description: "Gom Markdown+ảnh nghiên cứu/kế hoạch (01–09) thành index, HTML, PDF (Chrome) và PPTX."
description_en: "Pack research/plan Markdown+images (01–09) into index, HTML, PDF (Chrome) and simple PPTX."
group: Marketing
---

# Xuất gói nghiên cứu & kế hoạch (PDF / PPTX)

## Khi nào dùng

- Đã có thư mục `sources/research/<slug>/` với các file nghiên cứu `01`–`05` và/hoặc kế hoạch `06`–`09`.
- Cần giao nộp PDF báo cáo dài và/hoặc PPTX trình bày ngắn.

## Chuẩn bị

1. Xác định `slug` dự án (ASCII, gạch ngang).
2. Vault root = gốc brain đang làm việc.
3. Có **Google Chrome** (hoặc Chromium) trên máy để in PDF. Không có thì vẫn xuất HTML.
4. Ảnh minh họa nên nằm dưới `attachments/research/<slug>/` và đã nhúng relative path trong Markdown.

## File chuẩn trong pack

| File | Nội dung |
|------|----------|
| `00-index.md` | Mục lục toàn gói |
| `01-research-findings.md` | Nghiên cứu thị trường |
| `02-survey-plan.md` | Khung khảo sát |
| `03-competitors-personas.md` | Đối thủ + persona |
| `04-visual-brief.md` | Brief đồ họa |
| `05-proposal.md` | Proposal chiến lược |
| `06-business-plan.md` | Kế hoạch kinh doanh |
| `07-marketing-plan.md` | Kế hoạch marketing |
| `08-ops-playbook.md` | Playbook vận hành |
| `09-finance-model.md` | Mô hình tài chính / ngân sách MKT |

Thiếu file nào thì ghi rõ trong `00-index.md` (không bịa nội dung). Script gom **mọi** `*.md` trong thư mục slug.

## Quy trình

1. Viết / cập nhật `00-index.md` (mục lục + đường dẫn + đánh dấu file nào đã có).
2. Chạy script từ **gốc vault** (hoặc truyền `--vault`):

```bash
python3 skills/xuat-goi-nghien-cuu/scripts/export_pack.py \
  --slug <slug> \
  --formats pdf,pptx,html \
  --title "Nghiên cứu & kế hoạch - <tên>"
```

3. Kết quả mặc định: `exports/research/<slug>/`
   - `report.html` - xem / in tay
   - `report.pdf` - nếu Chrome có
   - `deck.pptx` - slide từ tiêu đề `##` / `###`
   - `manifest.json` - danh sách file đã gom

4. Báo user đường dẫn; nhúng link markdown nếu chat dashboard.

## Pipeline liên quan

- Sau nghiên cứu: workflow **`nghien-cuu-thi-truong-chuyen-sau`** (01–05).
- Sau kế hoạch: workflow **`ke-hoach-kd-mkt-tu-nghien-cuu`** (06–09 + cập nhật index).

## Bẫy

- Đường dẫn ảnh trong MD phải relative so với vault (`attachments/...`), không dùng absolute máy.
- PPTX là deck tóm tắt, không thay PDF đầy đủ.
- Không có Chrome: đừng giả PDF đã tạo - chỉ giao HTML + MD.
- Script không gọi mạng; không cần API key.
