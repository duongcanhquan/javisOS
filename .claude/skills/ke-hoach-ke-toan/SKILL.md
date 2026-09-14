---
name: ke-hoach-ke-toan
description: "Kế hoạch kỳ kế toán: đóng sổ, tiền mặt, tuổi nợ, lịch thuế; neo số từ sổ chứ không bịa."
description_en: "Accounting-period plan: close, cash, AR/AP aging, tax calendar; numbers from the books only."
group: Tài chính
---

# Kế hoạch kỳ kế toán

## Dùng để làm gì

Từ sổ đã có, lập **kế hoạch 30-90 ngày**: đóng sổ, tiền, thu nợ, trả nợ, mốc thuế. Không phải kế hoạch KD/MKT (`ke-hoach-kinh-doanh`).

## Khi nào dùng

- «kế hoạch kế toán», «đóng sổ tháng», «dòng tiền», «lịch VAT», «ưu tiên đòi nợ»
- Bước kế hoạch workflow `ke-toan-chuan`

## Chuẩn bị

1. Đọc `02-ledger.md` + `03-statements.md` (và `01-invoices.md` nếu có). Thiếu sổ thì bảo chạy `so-ke-toan-kep` trước.
2. Quốc gia mặc định **Việt Nam** trừ khi user nói khác. Không bịa hạn nộp - nêu mốc *cần đối chiếu* với lịch cục thuế / kế toán công ty.

## Quy trình

Lưu `sources/accounting/<slug>/05-plan.md`:

```markdown
## 0. Tóm tắt 8-12 dòng
## 1. Đóng sổ kỳ (checklist: cắt kỳ, DT/CP đúng kỳ, đối trừ, khấu hao nếu có số)
## 2. Dòng tiền 4-8 tuần (thu AR, trả AP, cố định đã biết)
## 3. Tuổi nợ: việc đòi / trả theo bucket Current, 31-90, 91-180, >180
## 4. Lịch thuế / báo cáo (VAT, TNCN, TNDN nếu user nêu ngành) - ghi «cần xác nhận hạn»
## 5. Rủi ro sổ (lệch CĐKT, hóa đơn cờ error)
## 6. Việc 14 ngày (checkbox, chủ, hạn)
```

Mọi số phải truy về 02/03/01 hoặc **Giả định:**.

## Bẫy

- Không lấy SOM/CAC từ skill marketing.
- Không hứa hạn thuế tuyệt đối nếu chưa có lịch công ty.
- Không lên kế hoạch đầu tư chứng khoán.

## Kiểm chứng

- [ ] Có việc 14 ngày
- [ ] Tiền/AR/AP có nguồn sổ
- [ ] File `05-plan.md`
