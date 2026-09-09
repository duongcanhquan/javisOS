---
type: workflow
name: Kế hoạch KD & Marketing từ nghiên cứu
slug: ke-hoach-kd-mkt-tu-nghien-cuu
status: active
group: Marketing
description: "Từ gói nghiên cứu (01/05): tài chính → kế hoạch KD → kế hoạch MKT → playbook vận hành → kiểm chứng → xuất gói."
steps:
  - agent: phan-tich-tai-chinh-marketing
    task: "Brief/slug: {{input}}. BẮT BUỘC có sources/research/<slug>/01-research-findings.md (slug lấy từ brief hoặc SLUG=). Nếu thiếu 01 → DỪNG, bảo chạy workflow nghien-cuu-thi-truong-chuyen-sau trước. Nạp skill `phan-tich-tai-chinh-mkt`. Đọc 01 (+ 05 nếu có). Viết 09-finance-model.md. Cuối ghi SLUG=..."
  - agent: soan-ke-hoach-kinh-doanh
    task: "Từ {{input}} + {{prev}}: Nạp skill `ke-hoach-kinh-doanh`. Đọc 01, 09 (và 03/05 nếu có). Viết 06-business-plan.md neo SOM base + số tài chính."
  - agent: soan-ke-hoach-marketing
    task: "Từ {{prev}}: Nạp skill `ke-hoach-marketing`. Đọc 01, 03, 06, 09. Viết 07-marketing-plan.md (lịch 90 ngày, ngân sách ≤ trần 09, funnel JTBD)."
  - agent: soan-quy-trinh-van-hanh
    task: "Từ {{prev}}: Nạp skill `quy-trinh-van-hanh-kd-mkt`. Đọc 06, 07, 09. Viết 08-ops-playbook.md (RACI, SOP, cổng duyệt)."
  - agent: kiem-chung-ke-hoach-kd-mkt
    task: "Nạp skill `ke-hoach-kinh-doanh`, `ke-hoach-marketing`, `phan-tich-tai-chinh-mkt`, `quy-trinh-van-hanh-kd-mkt`. Kiểm chứng 06–09 (+01). Trả ĐẠT/CHƯA ĐẠT + lỗi cụ thể."
  - agent: soan-ke-hoach-kinh-doanh
    task: "Nếu {{prev}} CHƯA ĐẠT: sửa đúng file bị lỗi (ưu tiên 06; nếu lỗi ở 09/07/08 thì ghi rõ cần bước sau). Nếu ĐẠT: xác nhận path + 5 quyết định."
  - agent: soan-ke-hoach-marketing
    task: "Áp lỗi MKT còn lại từ kiểm chứng vào 07-marketing-plan.md. Đồng bộ chỉ tiêu với 06."
  - agent: soan-quy-trinh-van-hanh
    task: "Áp lỗi vận hành còn lại vào 08-ops-playbook.md. Nếu kiểm chứng ĐẠT và không lỗi ops: xác nhận 08 ổn."
  - agent: xuat-goi-bao-cao
    task: "Nạp skill `xuat-goi-nghien-cuu`. Cập nhật 00-index.md liệt kê đủ 01–09 (đánh dấu thiếu nếu có). Xuất exports/research/<slug>/. Báo path. Title từ {{input}}."
updated: 2026-09-06
---

# Kế hoạch KD & Marketing từ nghiên cứu

## Chuỗi chuẩn

1. Trước đó: **`nghien-cuu-thi-truong-chuyen-sau`** → ít nhất `01-research-findings.md` (nên có `05-proposal.md`).
2. **Workflow này** → `09` → `06` → `07` → `08` → kiểm chứng → xuất.

## Skill gắn agent

| Bước | Agent | Skill |
|------|-------|-------|
| Tài chính | `phan-tich-tai-chinh-marketing` | `phan-tich-tai-chinh-mkt` |
| Kế hoạch KD | `soan-ke-hoach-kinh-doanh` | `ke-hoach-kinh-doanh` (+ `proposal-chien-luoc`) |
| Kế hoạch MKT | `soan-ke-hoach-marketing` | `ke-hoach-marketing` (+ `proposal-chien-luoc`) |
| Vận hành | `soan-quy-trinh-van-hanh` | `quy-trinh-van-hanh-kd-mkt` |
| Kiểm chứng | `kiem-chung-ke-hoach-kd-mkt` | cả bốn skill kế hoạch |
| Xuất | `xuat-goi-bao-cao` | `xuat-goi-nghien-cuu` |

## Cách chạy

1. Studio → **Kế hoạch KD & Marketing từ nghiên cứu** → ▶ Chạy.
2. Input: `Slug: <slug-nghien-cuu>. Chi phí cố định ước ... (giả định nếu thiếu).`
3. `/run ke-hoach-kd-mkt-tu-nghien-cuu Slug: ...`

## Đầu ra

```
sources/research/<slug>/
  06-business-plan.md
  07-marketing-plan.md
  08-ops-playbook.md
  09-finance-model.md
  00-index.md   # cập nhật đủ 01–09
exports/research/<slug>/
```

School of Art: pipeline riêng `marketing-business-plan-pipeline` (art-*) vẫn dùng cho case tuyển sinh/học phí; bản này là **chuẩn generic** mọi brain.

Không dùng em dash.
