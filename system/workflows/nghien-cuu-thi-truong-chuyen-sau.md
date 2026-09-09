---
type: workflow
name: Nghiên cứu thị trường chuyên sâu
slug: nghien-cuu-thi-truong-chuyen-sau
status: active
group: Marketing
description: "Nghiên cứu (JTBD/STEEPLE/SOM) → khảo sát → đối thủ → đồ họa → proposal → kiểm chứng → PDF/PPTX. Tiếp: ke-hoach-kd-mkt-tu-nghien-cuu."
steps:
  - agent: nghien-cuu-thi-truong-sau
    task: "Brief: {{input}}. Tạo slug ASCII. Nạp skill `nghien-cuu-thi-truong` + `deep-research`. Viết 01-research-findings.md đủ: giả định, TAM/SAM/SOM (triangulation + 3 kịch bản nếu mới), JTBD 4 lực, Hệ thống 1/2, văn hóa vùng miền nếu có, đối thủ+white space, STEEPLE/pháp lý, SWOT, 5-7 insight then chốt + nguồn. Lưu sources/research/<slug>/01-research-findings.md. Cuối ghi SLUG=..."
  - agent: thiet-ke-khao-sat
    task: "Từ brief {{input}} và {{prev}}: Nạp skill `nghien-cuu-thi-truong`. Thiết kế khảo sát giảm Say-Do gap, đo lo âu/sức ỳ/JTBD. Lưu sources/research/<slug>/02-survey-plan.md (đúng slug)."
  - agent: phan-tich-doi-thu-persona
    task: "Từ {{prev}} + 01-research-findings: Nạp skill `nghien-cuu-thi-truong` + `deep-research`. Đối thủ positioning/white space + persona vùng miền + JTBD 4 lực. Lưu sources/research/<slug>/03-competitors-personas.md."
  - agent: thiet-ke-do-hoa-minh-hoa
    task: "Từ insight {{prev}} + file research: visual SOM, bản đồ cạnh tranh, JTBD, funnel, cover proposal. Tạo ảnh nếu được phép. Lưu sources/research/<slug>/04-visual-brief.md."
  - agent: soan-proposal-chien-luoc
    task: "Nạp skill `proposal-chien-luoc`. Chưng cất 01–04 + brief {{input}} thành proposal đủ mục (Exec Summary ≤200 từ; KPI neo SOM base case; KD+MKT; rủi ro pháp lý NĐ13; consent). Lưu sources/research/<slug>/05-proposal.md."
    verify_agent: kiem-chung-nghien-cuu
    max_retries: 1
  - agent: kiem-chung-nghien-cuu
    task: "Nạp skill `nghien-cuu-thi-truong` + `proposal-chien-luoc`. Kiểm chứng 01–05 theo checklist. Liệt kê FAIL + đoạn sửa cụ thể."
  - agent: soan-proposal-chien-luoc
    task: "Áp dụng chỉnh từ {{prev}} vào 05-proposal.md (và 01–03 nếu được chỉ). Giữ file sạch để xuất."
  - agent: xuat-goi-bao-cao
    task: "Nạp skill `xuat-goi-nghien-cuu`. Viết 00-index.md (01–05; ghi rõ bước tiếp theo là workflow ke-hoach-kd-mkt-tu-nghien-cuu cho 06–09). Xuất html+pdf+pptx vào exports/research/<slug>/. Báo đường dẫn + nhắc chạy /run ke-hoach-kd-mkt-tu-nghien-cuu với SLUG=... Title từ {{input}}."
updated: 2026-09-06
---

# Nghiên cứu thị trường chuyên sâu (gói giao nộp)

## Chuỗi chuẩn (2 workflow)

1. **Workflow này** → file `01`–`05` + xuất gói.
2. **`ke-hoach-kd-mkt-tu-nghien-cuu`** → `09` tài chính → `06` KD → `07` MKT → `08` vận hành → xuất lại.

Skills: `nghien-cuu-thi-truong` ↔ `proposal-chien-luoc` → (`phan-tich-tai-chinh-mkt`, `ke-hoach-kinh-doanh`, `ke-hoach-marketing`, `quy-trinh-van-hanh-kd-mkt`) → `xuat-goi-nghien-cuu`.

## Cách chạy

1. Studio → Workflows → **Nghiên cứu thị trường chuyên sâu** → ● Sẵn sàng → ▶ Chạy.
2. Brief ví dụ: ngành, địa bàn, sản phẩm, mục tiêu proposal, ràng buộc ngân sách.
3. Sau khi xong: chạy **Kế hoạch KD & Marketing từ nghiên cứu** với cùng `SLUG=...`.
4. Telegram/Zalo: `/run nghien-cuu-thi-truong-chuyen-sau <brief>` rồi `/run ke-hoach-kd-mkt-tu-nghien-cuu Slug: ...`.

## Cấu trúc thư mục

```
sources/research/<slug>/
  00-index.md
  01-research-findings.md … 05-proposal.md     # workflow này
  06-business-plan.md … 09-finance-model.md   # workflow kế tiếp
attachments/research/<slug>/
exports/research/<slug>/
```

## Agent → skill

| Agent | Skill chính |
|-------|-------------|
| `nghien-cuu-thi-truong-sau` | `nghien-cuu-thi-truong`, `deep-research` |
| `thiet-ke-khao-sat` | `nghien-cuu-thi-truong` |
| `phan-tich-doi-thu-persona` | `nghien-cuu-thi-truong`, `deep-research` |
| `soan-proposal-chien-luoc` | `proposal-chien-luoc` |
| `kiem-chung-nghien-cuu` | `nghien-cuu-thi-truong`, `proposal-chien-luoc` |
| `xuat-goi-bao-cao` | `xuat-goi-nghien-cuu` |

Không dùng em dash trong đầu ra. PDF cần Chrome.
