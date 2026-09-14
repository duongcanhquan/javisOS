---
name: doc-hoa-don
description: "Đọc PDF/ảnh hóa đơn ra vendor, dòng, thuế, tổng; cờ lệch cộng dòng / hạn / thuế bất thường."
description_en: "Parse invoice PDF/image to vendor, lines, tax, total; flag line-sum, due-date, and tax anomalies."
group: Tài chính
license: MIT
metadata:
  version: "1.0"
  upstream: "https://github.com/DylanMerigaud/ai-invoice-parser"
---

# Đọc hóa đơn (schema + cờ bất thường)

## Dùng để làm gì

Từ PDF/ảnh hóa đơn ra **object có schema** rồi chạy **cờ đối soát** (cộng dòng, thuế, hạn).
Rút từ [DylanMerigaud/ai-invoice-parser](https://github.com/DylanMerigaud/ai-invoice-parser) (MIT). Không deploy app Next.js của họ; Javis đọc file bằng tool sẵn.

Schema và cờ: `references/schema-hoa-don.md`.

## Khi nào dùng

- «đọc hóa đơn», «parse invoice», «hóa đơn PDF», «đối soát tổng tiền»
- Bước đầu workflow `ke-toan-chuan`

**Không dùng** cho hợp đồng pháp lý dài (`phap-che`) hay BCTC năm (`doc-bao-cao-tai-chinh`).

## Chuẩn bị

1. File PDF/ảnh trong vault hoặc user đính. Không phải PDF thì nói rõ.
2. Tiền tệ ISO 3 chữ nếu đọc được.
3. Nhiều hóa đơn: mỗi cái một khối, không trộn.

## Quy trình

Với mỗi hóa đơn, điền schema (thiếu thì `null`, không bịa):

- vendor.name / address / taxId
- invoiceNumber, issueDate, dueDate, currency
- lineItems[]: description, qty, unitPrice, amount
- subtotal, tax, total

Rồi cờ (mã máy + mức):

| Mã | Mức | Khi nào |
|---|---|---|
| line_items_sum_mismatch | error | Cộng dòng ≠ subtotal (nới 1 đơn vị tiền/dòng) |
| subtotal_tax_ne_total | error | subtotal + tax ≠ total |
| implausible_tax_rate | warning | thuế âm hoặc > 40% |
| due_before_issue | error | dueDate < issueDate |
| missing_currency_or_total | error | thiếu currency hoặc total |
| duplicate_line_items | warning | hai dòng giống hệt |

Lưu `sources/accounting/<slug>/01-invoices.md`. Chat: bảng ngắn + số error.

## Bẫy

- Không tin Content-Type; nếu tool đọc được chữ thì dùng chữ. Ảnh mờ: nói «OCR yếu», không bịa số.
- Không gọi demo https://invoice-parser.merigaud.com trừ khi user xin.
- Hóa đơn tiếng Việt / hóa đơn GTGT: map MST vào taxId; không đổi schema.

## Kiểm chứng

- [ ] Mỗi HĐ có total hoặc cờ missing
- [ ] Có danh sách anomalies (kể cả rỗng)
- [ ] File `01-invoices.md`
