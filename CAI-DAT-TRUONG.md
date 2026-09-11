# Cài Javis cho trường (không cần biết lập trình)

Mỗi người / mỗi máy một bản riêng - **không** chia sẻ brain, bài giảng hay mật khẩu của người khác.

## Chọn đúng máy của bạn

| Bạn đang cài trên… | Hệ điều hành | Làm theo |
|---|---|---|
| **Laptop / PC cá nhân** | **Windows** | Đường A1 |
| **Laptop / PC cá nhân** | **Mac** | Đường A2 |
| **VPS / máy chủ trường** | **Linux** (Ubuntu, Hostinger…) | Đường B1 |
| **VPS / máy chủ trường** | **Windows Server** (hoặc Windows để chạy 24/7) | Đường B2 |

Cập nhật bản mới: máy cá nhân tải ZIP mới; VPS Docker thì Redeploy / `docker compose pull`.

Chi tiết kỹ thuật máy cá nhân: [CAI-DAT-MAY-CA-NHAN.md](CAI-DAT-MAY-CA-NHAN.md).  
Compose VPS: [`deploy/school/`](deploy/school/).

---

## Trước khi gửi cho giáo viên (admin)

1. Repo / image GHCR đã **Public** (hoặc đã cấp quyền pull).
2. Một trang PDF/slide: tải → cài → Models → chat thử (agent/workflow chuẩn đã có sẵn trong image).
3. Kèm `docs/huong-dan/HUONG-DAN-SU-DUNG-Javis-OS.pdf`.
4. **Không** gửi thư mục `brains/` của bạn - chỉ phần mềm + hướng dẫn này.

---

## Đường A - Máy cá nhân (Windows / Mac)

### A1 - Windows (laptop giáo viên)

> Cài sẵn trước: Python 3.11+ (PATH), Chrome/Edge; khuyến nghị Node 22 + Git. Chi tiết: [docs/huong-dan/CHUAN-BI-TRUOC-KHI-CAI.md](docs/huong-dan/CHUAN-BI-TRUOC-KHI-CAI.md).

1. Cài **Python 3.11+** từ python.org - **tick** *Add python.exe to PATH*.
2. (Khuyến nghị) Cài **Node.js 22 LTS** từ nodejs.org.
3. GitHub repo nhà trường gửi → **Code → Download ZIP** → giải nén (vd `D:\Javis`).
4. Double-click **`1-Cai-dat.bat`** (lần đầu hơi lâu).
5. Chrome → **http://localhost:7777** → tạo tài khoản admin (máy mình).
6. **Models** → chọn / đăng nhập một bộ não → chat thử (agent/workflow chuẩn đã sync sẵn).
7. Các ngày sau: **`2-Bat-Javis.bat`**. Tắt: **`3-Tat-Javis.bat`**.

### A2 - Mac (laptop giáo viên)

> Cài sẵn trước: `xcode-select --install`, Python 3.11+; khuyến nghị Homebrew + Node 22. Chi tiết: [docs/huong-dan/CHUAN-BI-TRUOC-KHI-CAI.md](docs/huong-dan/CHUAN-BI-TRUOC-KHI-CAI.md).

1. Cài Python 3 nếu chưa có (python.org hoặc `brew install python`). Lần đầu **bắt buộc** `xcode-select --install`.
2. (Khuyến nghị) Node.js 22 LTS.
3. GitHub → **Download ZIP** → giải nén (vd `~/Desktop/Javis`).
4. Chuột phải **`1-Cai-dat.command`** → **Open** (macOS có thể hỏi xác nhận).
5. Chrome → **http://localhost:7777** → Models → chat thử (agent/workflow chuẩn đã sync sẵn).
6. Các ngày sau: **`2-Bat-Javis.command`**. Tắt: **`3-Tat-Javis.command`**.

> Mac báo “không xác định được nhà phát triển”: **System Settings → Privacy & Security → Open Anyway**.

---

## Đường B - VPS / máy chủ (Linux hoặc Windows)

Phòng CNTT cấp **một link** cho giáo viên (hoặc mỗi tổ một stack riêng).

### B1 - VPS Linux (khuyến nghị: Docker)

#### Hostinger Docker Manager

1. Compose → URL:

```text
https://raw.githubusercontent.com/duongcanhquan/javisOS/main/deploy/school/docker-compose.hostinger.yml
```

2. Environment: `DOMAIN_NAME`, `JAVIS_ADMIN_USER`, `JAVIS_ADMIN_PASSWORD`.
3. Deploy → gửi `https://…` cho giáo viên.
4. Cập nhật: **Redeploy**.

#### VPS Linux tự quản (Ubuntu / Debian…)

```bash
mkdir -p ~/javis-school && cd ~/javis-school
curl -fsSLO https://raw.githubusercontent.com/duongcanhquan/javisOS/main/deploy/school/docker-compose.yml
curl -fsSLO https://raw.githubusercontent.com/duongcanhquan/javisOS/main/deploy/school/env.example
cp env.example .env   # sửa mật khẩu admin
docker compose up -d
```

Mở `http://<IP>:7777` (HTTPS: xem [DEPLOY.md](DEPLOY.md)).

Không Docker thì dùng `install.sh` ở gốc repo (native Linux + systemd) - chi tiết [DEPLOY.md](DEPLOY.md).

Image mặc định: `ghcr.io/duongcanhquan/javisos:latest`.

### B2 - VPS / máy chủ Windows

Hai cách, chọn **một**:

#### Cách 1 - Docker trên Windows Server / Windows có Docker Desktop (gần giống Linux)

> Trước đó: RDP được, Virtualization/WSL2 sẵn sàng, firewall TCP 7777. Xem [CHUAN-BI-TRUOC-KHI-CAI.md](docs/huong-dan/CHUAN-BI-TRUOC-KHI-CAI.md).

1. Cài **Docker Desktop** (hoặc Docker Engine trên Windows Server) + bật WSL2 nếu được hỏi.
2. PowerShell:

```powershell
mkdir $HOME\javis-school; cd $HOME\javis-school
Invoke-WebRequest -Uri https://raw.githubusercontent.com/duongcanhquan/javisOS/main/deploy/school/docker-compose.yml -OutFile docker-compose.yml
Invoke-WebRequest -Uri https://raw.githubusercontent.com/duongcanhquan/javisOS/main/deploy/school/env.example -OutFile env.example
Copy-Item env.example .env
# Sửa mật khẩu trong .env bằng Notepad
docker compose up -d
```

3. Mở `http://<IP-máy-chủ>:7777` (mở cổng 7777 trên firewall Windows nếu cần).
4. Cập nhật: `docker compose pull` rồi `docker compose up -d`.

#### Cách 2 - Native Windows trên máy chủ (không Docker)

Giống máy cá nhân nhưng máy chạy 24/7:

1. Cài Python + Node (tick Add to PATH).
2. Tải ZIP repo → giải nén trên ổ máy chủ.
3. Chạy **`1-Cai-dat.bat`** lần đầu; các lần sau **`2-Bat-Javis.bat`** (hoặc `javis-autostart.bat install` để tự bật khi đăng nhập Windows).
4. Để người khác vào từ mạng nội bộ / internet: trong `.env` hoặc cấu hình, lắng nghe `0.0.0.0` và mở firewall cổng 7777 - chi tiết [DEPLOY.md](DEPLOY.md) mục Windows.
5. **Bắt buộc đăng nhập admin** khi mở ra mạng (Javis tự yêu cầu trên bind public).

> Trên VPS Windows, Antigravity / Claude Code đăng nhập qua tab **Code** trong Javis (CLI in link + chỗ dán mã) - không cần trình duyệt trên chính máy chủ.

---

## Sau khi vào app (mọi đường)

1. **Models** - mỗi người tự gắn bộ não / API key. Không dùng chung một Claude Pro cho cả trường chạy nền 24/7.
2. **Agents / Workflows** - brain mới đã có sẵn bộ dùng chung từ image. **Studio → Bộ Trường** chỉ cần nếu muốn làm mới / thêm agent hướng dẫn giáo viên.
3. **Việc → Bài giảng** - nếu trường đã bật OpenMAIC trên VPS.
4. Brain nằm trên máy hoặc volume Docker của **bản đó**.

---

## Phân phối đúng / sai

| Đúng | Sai |
|---|---|
| Gửi link repo + hướng dẫn này | Gửi nguyên `brains/` có bài giảng / mật khẩu |
| Giáo viên mở app là đã có agent/workflow chuẩn | Đóng gói vault admin gửi USB |
| Cập nhật ZIP mới hoặc Redeploy image | Bắt mọi người tự `git pull` nếu không biết Git |
| Mỗi người Models / admin riêng | Một tài khoản Claude dùng chung cả trường |

---

## Lỗi thường gặp

| Hiện tượng | Cách xử lý |
|---|---|
| Windows: Python / PATH | Cài lại Python, tick Add to PATH, mở lại cửa sổ, chạy `1-Cai-dat` |
| Mac không mở `.command` | Chuột phải → Open; hoặc `chmod +x *.command` |
| Chat lỗi sau khi mở app | Models chưa đăng nhập / thiếu API key |
| Hostinger không HTTPS | Chưa đặt `DOMAIN_NAME` đúng |
| Pull image fail | Package GHCR chưa Public |
| VPS Windows firewall chặn | Mở inbound TCP 7777 (và 443 nếu reverse proxy) |
| Docker Desktop trên Windows chưa chạy | Mở Docker Desktop, đợi engine xanh, rồi `docker compose up -d` lại |
| Muốn OpenMAIC / giọng lớp học | Admin xem `deploy/openmaic/README.md` + Gemini API key trên server OpenMAIC |
