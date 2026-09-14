---
name: doc-bao-cao-tai-chinh
description: "Đọc BCTC: tính 5 tỷ số, cờ ngôn ngữ rủi ro, briefing 5 điểm; ghi IFRS/GAAP. Không bịa số."
description_en: "Read financial statements: 5 ratios, risk-language flags, 5-point briefing; note IFRS/GAAP. No invented numbers."
group: Tài chính
metadata:
  version: "1.0"
  upstream: "https://github.com/Ruchas-lab/Financial-report-analyzer"
---

# Đọc / phân tích báo cáo tài chính

## Dùng để làm gì

Lượt đọc **lần đầu** một BCTC (PDF, Excel, hoặc số user dán): tính tỷ số, đánh dấu câu rủi ro, viết briefing cho sếp. Rút phương pháp từ [Ruchas-lab/Financial-report-analyzer](https://github.com/Ruchas-lab/Financial-report-analyzer). Javis **không** chạy app Streamlit của họ.

Công thức tỷ số: `references/ty-so.md`.

## Khi nào dùng

- «phân tích BCTC», «tỷ số tài chính», «ROE / đòn bẩy», «going concern», «briefing báo cáo năm»
- Bước phân tích trong workflow `ke-toan-chuan`

**Không dùng** cho unit economics marketing (`phan-tich-tai-chinh-mkt`) hay giá cổ phiếu realtime (`tro-ly-thi-truong-chung-khoan`).

## Chuẩn bị

1. Có số **doanh thu, giá vốn, LNST, VCSH, nợ, TS ngắn hạn, nợ ngắn hạn** - từ file user hoặc bước sổ. Thiếu thì **Giả định:** hoặc dừng hỏi 1 câu.
2. Ghi chuẩn mực nếu thấy (IFRS / VAS / US GAAP). Không chắc thì «chưa rõ».
3. Slug ASCII: `sources/accounting/<slug>/`.

## Quy trình

Lưu `sources/accounting/<slug>/04-analysis.md`:

1. Bảng đầu vào (số + nguồn trang/file).
2. Năm tỷ số + 1 câu nghĩa thường (xem ty-so.md). Không đảo dấu im lặng.
3. **Cờ rủi ro** (chỉ khi có trong văn bản): going concern, material uncertainty, covenant, impairment, nhấn mạnh «không chắc chắn trọng yếu».
4. Briefing 5 gạch: thanh khoản, đòn bẩy, sinh lời, rủi ro đã cờ, việc cần hỏi KTV.
5. So sánh 2 kỳ / 2 công ty chỉ khi user có đủ 2 cột số.

## Bẫy

- Không bịa EBITDA nếu báo cáo không cho (hoặc tách rõ Giả định).
- Không kết luận «phá sản» từ một tỷ số Current < 1.
- Repo gốc v0.2 PDF chưa xong: OCR/PDF do Javis đọc file, không gọi demo Streamlit.

## Kiểm chứng

- [ ] Mọi tỷ số có tử/mẫu
- [ ] Cờ rủi ro trích câu gốc hoặc «không thấy»
- [ ] File `04-analysis.md`
