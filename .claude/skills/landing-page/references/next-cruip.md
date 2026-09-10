# Next.js / Cruip (chế độ nâng cao)

Chỉ chạy khi user **nói rõ** muốn project Next.js, Cruip, hoặc deploy Vercel từ
template gốc.

## Pháp lý

- Upstream: https://github.com/cruip/tailwind-landing-page-template
- Giấy phép: **GPL** + điều khoản Cruip: dùng personal/commercial OK; **không**
  republish / redistribute / resell template.
- Clone **riêng** vào máy/VPS user (`$JAVIS_STATE_DIR/vendor/cruip-simple-light`),
  **không** copy vào `.claude/skills/` hay image Docker Javis.
- Thành phẩm chỉnh sửa của user thuộc dự án của họ; nhắc họ giữ LICENSE GPL của
  upstream trong repo dự án.

## Quy trình

1. `ensure` vendor (git clone --depth 1 nếu chưa có).
2. Copy project sang `exports/landing/<slug>-next/` trong vault **hoặc** thư mục
   ngoài vault user chỉ định (tránh `node_modules` trong sync não nếu có thể:
   cài deps trong vendor/worktree, chỉ commit source đã đổi vào vault nếu user muốn).
3. Thay copy trong `app/` + `components/` theo `COPY.md` (đọc cấu trúc thực tế sau clone).
4. `pnpm install && pnpm dev` nếu môi trường có Node; báo URL localhost.
5. Hướng dẫn deploy Vercel; không tự publish trừ khi user có MCP/token và yêu cầu rõ.

## Khi nào từ chối / hạ cấp

- Không có git/network/Node → quay về HTML standalone, giải thích thiếu gì.
- User chỉ cần «xem được trang» → HTML đủ, không ép Next.
