# Schema hóa đơn + cờ (chuẩn skill)

Object (thiếu = null, không bịa):

```text
vendor.name, vendor.address?, vendor.taxId?
invoiceNumber, issueDate, dueDate?, currency (ISO 3)
lineItems[]: description, qty, unitPrice, amount
subtotal, tax?, total
```

Đối soát tiền: cho phép lệch làm tròn khoảng 1 đơn vị tiền * số dòng, cộng sàn tương đối nhỏ. Không đòi khớp float tuyệt đối.

Cờ ổn định: `line_items_sum_mismatch`, `subtotal_tax_ne_total`, `implausible_tax_rate`, `due_before_issue`, `missing_currency_or_total`, `duplicate_line_items`.
