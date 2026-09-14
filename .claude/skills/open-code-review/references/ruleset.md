# Ruleset review mặc định (Javis)

Áp cho file **trong diff**. First-match theo đuôi file. Viết lại cho Javis, không copy catalog Alibaba.

## Mọi ngôn ngữ

- Không nuốt lỗi / `except: pass` / bỏ trống catch.
- Không log secret, token, mật khẩu.
- Input ngoài (query, file, HTTP) phải kiểm trước khi dùng.
- Concurrent: không data race rõ trên biến dùng chung; lock/queue phải có hướng thoát.
- Test: thay đổi hành vi công khai thì phải có test hoặc nêu vì sao chưa có.

## Python / JS / TS

- Null/undefined: không gọi method trên giá trị có thể trống mà không kiểm.
- Path: chặn `..` khi ghép đường dẫn user.
- SQL/lệnh: parameterized; không ghép chuỗi user vào shell/SQL.
- XSS: không nhúng HTML user không escape (đặc biệt dashboard).

## Web / HTML / template

- XSS, CSRF đã có sẵn của app thì đừng tắt.
- Không mở CORS `*` kèm cookie.

## Config / YAML / Docker / compose

- Không bind `0.0.0.0` thêm cổng nhạy cảm nếu user không xin.
- Secret không hardcode.

## Bỏ qua trừ khi user xin

`*.lock`, `dist/`, `node_modules/`, minified, fixture snapshot lớn, file generated.

## Severity

| Mức | Ví dụ |
|---|---|
| critical | RCE, lộ secret, SQL injection chắc |
| high | XSS, auth bypass, mất dữ liệu |
| medium | race, nuốt lỗi, thiếu test cho nhánh mới |
| low | style, rename, nit (mặc định ẩn) |
