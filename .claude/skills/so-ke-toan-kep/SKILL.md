---
name: so-ke-toan-kep
description: "Sổ kép IFRS/GAAP: định khoản, P&L, CĐKT, LCTT, tuổi nợ; cân Nợ=Có. Không bịa số dư."
description_en: "Double-entry IFRS/GAAP: journal, P&L, balance sheet, cash flow, aging; Debit=Credit. No invented balances."
group: Tài chính
license: MIT
metadata:
  version: "1.0"
  upstream: "https://github.com/ekmungai/python-accounting"
---

# Sổ kế toán kép (báo cáo IFRS/GAAP)

## Dùng để làm gì

Ghi **bút toán 2 bên**, lập **KQKD (P&L), CĐKT, LCTT**, sao kê phải thu/phải trả và **tuổi nợ**.
Rút mô hình từ [ekmungai/python-accounting](https://github.com/ekmungai/python-accounting) (MIT, IFRS/GAAP). Javis **không** nhúng library; có thể gọi `python-accounting` nếu user đã cài.

## Khi nào dùng

- «định khoản», «sổ cái», «P&L», «bảng cân đối», «cash flow», «aging», «công nợ»
- Sau khi đã có hóa đơn đã trích (`doc-hoa-don`) hoặc số user đưa

**Không dùng** để viết kế hoạch MKT (`phan-tich-tai-chinh-mkt`).

## Chuẩn bị

1. Đơn vị tiền (VND mặc định), kỳ báo cáo, tên entity.
2. Hệ tài khoản tối thiểu (đúng tên loại library): Bank, Receivable, Payable, Operating Revenue, Operating Expense, Direct Expense, Non Current Asset, Control (thuế).
3. `command -v python` rồi `python -c "import python_accounting"` - có thì được phép `post()` ledger; **không tự pip install**.

Loại giao dịch đã thấy trong README: `CashSale`, `ClientInvoice`, `CashPurchase`, `SupplierBill`, `JournalEntry`, `ClientReceipt` + `Assignment` (cấn trừ). Báo cáo: `IncomeStatement`, `BalanceSheet`, `CashflowStatement`.

## Quy trình

Lưu `sources/accounting/<slug>/02-ledger.md` và `03-statements.md`.

1. Mỗi chứng từ: ngày, diễn giải, Nợ TK / Có TK / số tiền / thuế (nếu có). Tổng Nợ = tổng Có.
2. Không sửa sổ bằng tay kiểu «đổi số dư» - thêm bút toán điều chỉnh.
3. P&L: doanh thu hoạt động, chi phí hoạt động, lãi gộp, chi phí khác, LN.
4. CĐKT: TSNH/Dài hạn, nợ, VCSH; **Tài sản = Nợ + VCSH** (hoặc nêu lệch).
5. LCTT: hoạt động / đầu tư / tài trợ; đối chiếu số dư tiền.
6. Tuổi nợ (nếu có hạn): Current, 31-90, 91-180, >180.

Không có library: làm bảng Markdown cân bằng như trên. Có library: in report rồi dán/tóm vào file (không dump session SQL).

## Bẫy

- Không bịa số dư đầu kỳ.
- Không ghi một bên. Thiếu tài khoản đối ứng thì hỏi.
- VAS Việt Nam khác IFRS ở một số khoản: ghi «trình bày theo IFRS/GAAP library, đối chiếu VAS nếu user yêu cầu».

## Kiểm chứng

- [ ] Tổng Nợ = tổng Có trên journal
- [ ] CĐKT cân hoặc ghi rõ lệch
- [ ] Có `02-ledger.md` + `03-statements.md`
