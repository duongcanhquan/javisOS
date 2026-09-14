---
type: workflow
name: Kế toán chuẩn (hóa đơn, sổ, báo cáo, kế hoạch)
slug: ke-toan-chuan
status: active
group: Tài chính
description: "Hóa đơn → sổ kép → BCTC/tỷ số → kế hoạch kỳ → kiểm chứng → xuất gói accounting."
steps:
  - agent: trich-hoa-don
    task: "Brief/slug: {{input}}. Nạp skill `doc-hoa-don`. Trích mọi PDF/ảnh/hóa đơn trong brief thành sources/accounting/<slug>/01-invoices.md (schema + cờ). Không có file hóa đơn: ghi 01 với «không có chứng từ ảnh/PDF, chờ số user» rồi đi tiếp nếu user đã dán bảng số. Cuối SLUG=."
  - agent: ghi-so-ke-toan
    task: "Từ {{input}} + {{prev}}: nạp `so-ke-toan-kep`. Đọc 01-invoices.md. Viết 02-ledger.md (Nợ=Có) và 03-statements.md (P&L, CĐKT, LCTT, aging nếu có). Không pip install. Cuối SLUG=."
  - agent: phan-tich-bao-cao-tai-chinh
    task: "Từ {{prev}}: nạp `doc-bao-cao-tai-chinh`. Đọc 03-statements.md. Viết 04-analysis.md (5 tỷ số, cờ rủi ro, briefing). Chỉ nạp `tro-ly-thi-truong-chung-khoan` nếu brief có mã niêm yết. Cuối SLUG=."
  - agent: lap-ke-hoach-ke-toan
    task: "Từ {{prev}}: nạp `ke-hoach-ke-toan`. Đọc 02-05. Viết 05-plan.md (đóng sổ, tiền, tuổi nợ, lịch thuế cần xác nhận, việc 14 ngày). Cuối SLUG=."
  - agent: kiem-chung-ke-toan
    task: "Nạp `doc-hoa-don`, `so-ke-toan-kep`, `doc-bao-cao-tai-chinh`, `ke-hoach-ke-toan`. Kiểm 01-05. Trả ĐẠT/CHƯA ĐẠT. Ghi 06-kiem-chung.md."
  - agent: ghi-so-ke-toan
    task: "Nếu {{prev}} CHƯA ĐẠT vì sổ/CĐKT: sửa 02/03 đúng lỗi. Nếu ĐẠT: xác nhận path 02/03."
  - agent: lap-ke-hoach-ke-toan
    task: "Áp lỗi kế hoạch còn lại vào 05-plan.md. Nếu ĐẠT: xác nhận 05."
  - agent: xuat-goi-bao-cao
    task: "Nạp `xuat-goi-nghien-cuu` nhưng gói nằm ở sources/accounting/<slug>/ (01-06), không phải research 01-09. Viết 00-index.md. Xuất exports/accounting/<slug>/ nếu script nhận path; không thì copy MD + nói rõ. Title từ {{input}}."
updated: 2026-09-14
---

# Kế toán chuẩn

Chuỗi cho vấn đề **kế toán**: đọc chứng từ, ghi sổ, đọc báo cáo, lên kế hoạch kỳ.

Không thay workflow `ke-hoach-kd-mkt-tu-nghien-cuu` (đó là SOM/CAC/MKT).

## Skill gắn agent

| Bước | Agent | Skill |
|------|-------|-------|
| Hóa đơn | `trich-hoa-don` | `doc-hoa-don` |
| Sổ | `ghi-so-ke-toan` | `so-ke-toan-kep` |
| Phân tích BCTC | `phan-tich-bao-cao-tai-chinh` | `doc-bao-cao-tai-chinh` (+ thị trường nếu có ticker) |
| Kế hoạch kỳ | `lap-ke-hoach-ke-toan` | `ke-hoach-ke-toan` |
| Kiểm chứng | `kiem-chung-ke-toan` | bốn skill kế toán |
| Xuất | `xuat-goi-bao-cao` | `xuat-goi-nghien-cuu` |

## Cách chạy

1. Studio → **Kế toán chuẩn** → Chạy.
2. Input ví dụ: `Slug: thang-09-2026. Đính hóa đơn PDF + số dư đầu kỳ nếu có.`
3. `/run ke-toan-chuan Slug: ...`

## Đầu ra

```
sources/accounting/<slug>/
  00-index.md
  01-invoices.md
  02-ledger.md
  03-statements.md
  04-analysis.md
  05-plan.md
  06-kiem-chung.md
exports/accounting/<slug>/
```

Repo gốc chỉ là phương pháp (không ship app Streamlit/Next/`pip install python-accounting`).

Không dùng em dash.
