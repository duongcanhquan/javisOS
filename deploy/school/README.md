# Gói cài Javis cho trường (VPS Linux / Windows / Hostinger)

Hướng dẫn đầy đủ 4 môi trường (Windows/Mac cá nhân + VPS Linux/Windows): [CAI-DAT-TRUONG.md](../../CAI-DAT-TRUONG.md).

## File trong thư mục này

| File | Khi nào dùng |
|---|---|
| `docker-compose.hostinger.yml` | Hostinger Docker Manager (Traefik HTTPS) - Linux |
| `docker-compose.yml` | VPS Linux **hoặc** Windows có Docker Desktop / Docker Engine |
| `env.example` | Mẫu `.env` cạnh compose |

Image mặc định: **`ghcr.io/duongcanhquan/javisos:latest`**. GHCR cần **Public** (hoặc `docker login ghcr.io`).

## VPS Linux (Hostinger)

Compose → URL:

```text
https://raw.githubusercontent.com/duongcanhquan/javisOS/main/deploy/school/docker-compose.hostinger.yml
```

Environment: `DOMAIN_NAME`, `JAVIS_ADMIN_USER`, `JAVIS_ADMIN_PASSWORD` → Deploy → Redeploy khi có bản mới.

## VPS Linux tự quản

```bash
cd ~/javis-school
curl -fsSLO https://raw.githubusercontent.com/duongcanhquan/javisOS/main/deploy/school/docker-compose.yml
curl -fsSLO https://raw.githubusercontent.com/duongcanhquan/javisOS/main/deploy/school/env.example
cp env.example .env && docker compose up -d
```

## VPS / máy chủ Windows (Docker)

Cài Docker Desktop (hoặc Docker Engine trên Windows Server), rồi PowerShell:

```powershell
cd $HOME\javis-school
# tải docker-compose.yml + env.example như trong CAI-DAT-TRUONG.md mục B2
Copy-Item env.example .env
docker compose up -d
```

Không Docker: native Windows bằng `1-Cai-dat.bat` / `2-Bat-Javis.bat` trên máy chủ - xem mục B2 trong `CAI-DAT-TRUONG.md`.

## Sau khi chạy

1. Mở app → admin (đã đặt trong `.env`) hoặc tạo tài khoản lần đầu.
2. **Models** - mỗi bản tự gắn bộ não.
3. **Studio → Bộ Trường** - nạp skill/workflow mẫu (không kèm brain cá nhân).

## Không nằm trong gói này

- Brain / bài giảng / mật khẩu của admin phát hành
- OpenMAIC (tuỳ chọn): `deploy/openmaic/`
