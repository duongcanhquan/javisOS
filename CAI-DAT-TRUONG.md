# Cài Javis cho trường (giáo viên không cần biết lập trình)

Hai đường cài. Chọn **một**. Mỗi người một bản riêng - **không** chia sẻ brain / bài giảng / mật khẩu của người khác.

| Đường | Ai hợp | Mở app bằng |
|---|---|---|
| **A - Máy cá nhân** (Windows / Mac) | Giáo viên tự cài trên laptop | `http://localhost:7777` |
| **B - VPS / Hostinger** | Phòng CNTT cấp 1 link HTTPS | `https://…` do admin gửi |

Cập nhật bản mới: đường A tải ZIP mới; đường B Redeploy (kéo image mới từ GitHub).

---

## Trước khi gửi cho giáo viên (admin)

1. Repo / image đã public (hoặc đã cấp quyền pull GHCR).
2. Chuẩn bị **1 trang PDF/slide**: tải → cài → Models → Studio → Bộ Trường.
3. Kèm link này + `docs/huong-dan/HUONG-DAN-SU-DUNG-Javis-OS.pdf`.
4. **Không** gửi bản backup brain của bạn. Chỉ gửi phần mềm + hướng dẫn. Gói năng lực mẫu (Bài giảng…) giáo viên tự bấm trong Studio.

---

## Đường A - Máy cá nhân (2 nút)

Chi tiết kỹ thuật: [CAI-DAT-MAY-CA-NHAN.md](CAI-DAT-MAY-CA-NHAN.md).

### Tóm tắt cho giáo viên

1. Cài **Python 3.11+** (Windows: tick *Add to PATH*) và nên có **Node.js 22 LTS**.
2. Vào GitHub repo nhà trường gửi → **Code → Download ZIP** → giải nén.
3. **Lần đầu:** double-click `1-Cai-dat.bat` (Windows) hoặc `1-Cai-dat.command` (Mac).
4. Mở Chrome → **http://localhost:7777** → tạo tài khoản admin (máy mình).
5. Trang **Models**: chọn **một** bộ não (Antigravity / Claude Code / OpenRouter / Gemini API…).
6. **Studio → Workflows → Bộ Trường** (một lần) để có sẵn bộ Bài giảng.
7. Các ngày sau: `2-Bat-Javis…` rồi mở lại trình duyệt. Tắt: `3-Tat-Javis…`.

Muốn bản mới: tải ZIP mới, giải nén đè (hoặc folder mới), chạy lại `1-Cai-dat`.

---

## Đường B - VPS / Hostinger (phòng CNTT)

Thư mục sẵn: **[deploy/school/](deploy/school/)** (compose + README).

### Hostinger Docker Manager

1. Compose → URL, dán (đổi `main` nếu bạn phát hành nhánh khác):

```text
https://raw.githubusercontent.com/duongcanhquan/javisOS/main/deploy/school/docker-compose.hostinger.yml
```

2. Environment (tối thiểu):
   - `DOMAIN_NAME` - tên miền hoặc `javis.<hostname>.hstgr.cloud`
   - `JAVIS_ADMIN_USER` / `JAVIS_ADMIN_PASSWORD` - tài khoản quản trị **của bản đó**
3. Deploy → đợi HTTPS → gửi link cho giáo viên / tổ bộ môn.
4. Cập nhật: **Redeploy** (image `:latest` + `pull_policy: always`).

Mỗi tổ / mỗi người một stack riêng nếu cần tách dữ liệu: đổi `JAVIS_NAME` + `JAVIS_HOST_PORT` + `DOMAIN_NAME` (xem chú thích trong file compose).

### VPS tự quản (Docker)

```bash
mkdir -p ~/javis-school && cd ~/javis-school
curl -fsSLO https://raw.githubusercontent.com/duongcanhquan/javisOS/main/deploy/school/docker-compose.yml
curl -fsSLO https://raw.githubusercontent.com/duongcanhquan/javisOS/main/deploy/school/env.example
cp env.example .env   # sửa mật khẩu admin, cổng nếu cần
docker compose up -d
```

Mở `http://<IP>:7777` (hoặc gắn Caddy/HTTPS theo [DEPLOY.md](DEPLOY.md)).

Image mặc định của gói trường: `ghcr.io/duongcanhquan/javisos:latest`.

---

## Sau khi vào app (mọi đường)

1. **Models** - tự gắn key / đăng nhập gói cá nhân. Không dùng chung một tài khoản Claude cho cả trường chạy nền 24/7.
2. **Studio → Bộ Trường** - nạp workflow/skill bài giảng mẫu (không copy dữ liệu cá nhân ai).
3. **Việc → Bài giảng** - soạn / tạo lớp OpenMAIC nếu trường đã bật OpenMAIC trên VPS.
4. Brain nằm trên máy hoặc volume Docker của **bản đó** - backup / GitHub brain là việc riêng của từng người.

---

## Phân phối đúng / sai

| Đúng | Sai |
|---|---|
| Gửi link repo + hướng dẫn này | Gửi nguyên thư mục `brains/` có bài giảng / mật khẩu |
| Giáo viên tự bấm **Bộ Trường** / **Bộ Bài giảng** | Đóng gói sẵn vault của admin rồi gửi USB |
| Cập nhật qua ZIP mới hoặc Redeploy image | Bảo mọi người tự `git pull` nếu họ không biết Git |
| Mỗi người Models / admin riêng | Một tài khoản Claude dùng chung VPS cho cả trường |

---

## Lỗi thường gặp

| Hiện tượng | Cách xử lý |
|---|---|
| Python / PATH (Windows) | Cài lại Python, tick Add to PATH, mở lại cửa sổ, chạy `1-Cai-dat` |
| Chat lỗi sau khi mở app | Models chưa đăng nhập / thiếu API key |
| Hostinger không HTTPS | Chưa đặt `DOMAIN_NAME` đúng hostname |
| Pull image fail | Package GHCR chưa Public (Settings package → Public) |
| Muốn OpenMAIC / giọng lớp học | Admin VPS xem `deploy/openmaic/README.md` + Gemini API key trên server OpenMAIC |
