# Gói cài Javis cho trường (VPS / Hostinger)

Dùng kèm hướng dẫn gốc: [CAI-DAT-TRUONG.md](../../CAI-DAT-TRUONG.md).

## File trong thư mục này

| File | Khi nào dùng |
|---|---|
| `docker-compose.hostinger.yml` | Hostinger Docker Manager (Traefik HTTPS) |
| `docker-compose.yml` | VPS bất kỳ (DigitalOcean, Vultr, VPS tự quản…) |
| `env.example` | Mẫu `.env` cho bản VPS tự quản |

Image mặc định: **`ghcr.io/duongcanhquan/javisos:latest`** (fork trường). Đổi bằng biến `JAVIS_IMAGE` nếu phát hành image khác.

Package trên GHCR cần **Public** (hoặc máy đã `docker login ghcr.io`) thì pull mới được.

## Hostinger (nhanh)

1. Docker Manager → Compose → URL:

```text
https://raw.githubusercontent.com/duongcanhquan/javisOS/main/deploy/school/docker-compose.hostinger.yml
```

2. Environment:
   - `DOMAIN_NAME` (bắt buộc nếu muốn HTTPS)
   - `JAVIS_ADMIN_USER` / `JAVIS_ADMIN_PASSWORD`
3. Deploy → gửi link cho giáo viên.
4. Cập nhật bản mới từ nhà phát hành: **Redeploy**.

## VPS tự quản

```bash
cd ~/javis-school   # thư mục trống
curl -fsSLO https://raw.githubusercontent.com/duongcanhquan/javisOS/main/deploy/school/docker-compose.yml
curl -fsSLO https://raw.githubusercontent.com/duongcanhquan/javisOS/main/deploy/school/env.example
cp env.example .env
# sửa mật khẩu trong .env
docker compose up -d
```

HTTPS (Caddy): xem [DEPLOY.md](../../DEPLOY.md) + `docker-compose.https.yml` ở gốc repo.

## Sau khi chạy

1. Mở app → đăng nhập admin (đã đặt trong env) hoặc tạo tài khoản lần đầu.
2. **Models** - mỗi người / mỗi bản tự gắn bộ não.
3. **Studio → Bộ Trường** - nạp skill/workflow bài giảng mẫu (không phải dữ liệu cá nhân).

## Không nằm trong gói này

- Brain / bài giảng / mật khẩu của admin phát hành
- OpenMAIC (tuỳ chọn, xem `deploy/openmaic/`) - chỉ cần nếu dùng «Tạo lớp OpenMAIC»
