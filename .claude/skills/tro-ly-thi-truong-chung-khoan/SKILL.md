---
name: tro-ly-thi-truong-chung-khoan
description: "Giá/tin/cổ phiếu tăng giảm realtime qua MCP Finnhub-AlphaVantage. Không phải sổ kế toán."
description_en: "Live quotes, news, and market movers via Finnhub/Alpha Vantage MCP. Not bookkeeping."
group: Tài chính
license: MIT
metadata:
  version: "1.0"
  upstream: "https://github.com/Pyligent/Finance-Assistant-with-MCP-and-Langchain"
---

# Trợ lý thị trường chứng khoán (MCP)

## Dùng để làm gì

Hỏi **giá cổ phiếu, tin, mã tăng/giảm mạnh** bằng tiếng thường. Rút kiến trúc MCP từ
[Pyligent/Finance-Assistant-with-MCP-and-Langchain](https://github.com/Pyligent/Finance-Assistant-with-MCP-and-Langchain) (MIT).

**Đây không phải kế toán.** Không ghi sổ, không P&L công ty bạn.

## Khi nào dùng

- «giá AAPL», «tin TSLA», «top gainers», «thị trường hôm nay»
- Công ty niêm yết trong brief kế toán *và* user muốn bối cảnh giá - bước phụ, không thay BCTC

**Không dùng** cho hóa đơn, sổ kép, BCTC nội bộ.

## Chuẩn bị

Tool đã thấy trong repo: `get_price`, `get_news`, `get_market_movers` (MCP backend Finnhub / Alpha Vantage). Key nằm **server MCP**, không nhét vào chat.

1. Liệt kê MCP/Kết nối Javis đã đấu. Có tool tương đương thì gọi.
2. **Không tự cài** Streamlit/`fin_server_v2.py`. Thiếu MCP: nói rõ + fallback WebSearch (ghi «không phải giá khớp lệnh»).

## Quy trình

1. Tách ticker (không bịa mã).
2. Gọi đúng 1-2 tool: giá *hoặc* tin *hoặc* movers.
3. Trả 5-8 dòng + thời điểm lấy. Gợi ý câu tiếp (tin / so sánh) nếu hữu ích.
4. Nếu nằm trong gói kế toán: chỉ 1 mục «Bối cảnh thị trường» trong `04-analysis.md`, không trộn vào sổ.

## Bẫy

- Không tư vấn mua bán như khuyến nghị đầu tư có giấy phép.
- Không dùng số giá để bịa doanh thu công ty trong sổ.
- Không bịa API Finnhub khác các tool trên.

## Kiểm chứng

- [ ] Nguồn: MCP tên tool / hoặc «fallback web»
- [ ] Có ticker + thời điểm
