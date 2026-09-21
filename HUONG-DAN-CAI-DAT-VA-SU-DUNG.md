# Hướng dẫn cài đặt & sử dụng VMOS / Javis OS (sau đóng gói)

***Tiếng Việt** · Bản này dành cho người nhận **bản đóng gói** (ZIP máy cá nhân hoặc image Docker trên VPS).*

Tài liệu dẫn từ lúc **cài lần đầu** tới lúc **dùng được chat, Cộng sự, Kết nối, Hội thoại khách**.  
**Trong app:** menu trái nhóm **Hướng dẫn** (dưới Kết nối) - 4 trang: VMOS làm được gì · Kết nối · Skill/Agent/Workflow · Công việc & chức năng.  
**PDF:** [Cài đặt](docs/huong-dan/HUONG-DAN-CAI-DAT-Javis-OS.pdf) · [Sử dụng](docs/huong-dan/HUONG-DAN-SU-DUNG-Javis-OS.pdf) - mục lục [docs/huong-dan/README.md](docs/huong-dan/README.md).  
Chi tiết từng chức năng: [docs/README.md](docs/README.md).  
Cài nhanh trường: [CAI-DAT-TRUONG.md](CAI-DAT-TRUONG.md).  
**VPS:** [HUONG-DAN-CAI-VPS-KHONG-TEN-MIEN.md](HUONG-DAN-CAI-VPS-KHONG-TEN-MIEN.md).  
**Máy local:** [HUONG-DAN-CAI-MAY-LOCAL.md](HUONG-DAN-CAI-MAY-LOCAL.md) · [CAI-DAT-DON-GIAN.md](CAI-DAT-DON-GIAN.md).  
**Chuẩn bị trước khi cài:** [docs/huong-dan/CHUAN-BI-TRUOC-KHI-CAI.md](docs/huong-dan/CHUAN-BI-TRUOC-KHI-CAI.md).  
Kỹ thuật VPS: [DEPLOY.md](DEPLOY.md).  
**Nhiều người / subdomain:** [docs/30-nhieu-ban-va-dau-nao.md](docs/30-nhieu-ban-va-dau-nao.md).

> **Đổi tên quan trọng (từ 0.56):** trang **Agents** và **Workflows** cũ đã gộp thành **Năng lực → Cộng sự** (hai tab **Trợ Lý (Agent)** và **Quy Trình (Workflows)**). Chatbot khách nằm trong **Hội thoại khách**. Link công khai quản ở **Hệ thống → Chia sẻ**.

---

## 1. Bản đóng gói gồm gì / không gồm gì

### Có sẵn (dùng chung trên cùng một Javis)

| Loại | Nội dung |
|---|---|
| **Phần mềm** | Dashboard + server + cập nhật theo phiên bản |
| **Skills hệ thống** | Toàn bộ skill trong `.claude/skills/` (đồng bộ vào mỗi brain mới) |
| **Agents / Workflows chuẩn** | Tự đồng bộ từ `system/agents/` + `system/workflows/` vào mỗi brain. Xem / sửa tại **Năng lực → Cộng sự** |
| **Plugins hệ thống** | Tool native đi kèm app (lịch VN, schedule, task, ảnh ChatGPT, Zalo image…) |

Skills / agent / workflow **dùng chung** trên cùng một bản Javis: mọi brain đều nhận được bộ năng lực chuẩn.  
**Project (dự án chat)** thuộc **đúng một brain** - không lẫn giữa các não.

### Không đi kèm (người dùng tự làm)

| Loại | Lý do |
|---|---|
| **Bộ nhớ / wiki / sources cá nhân** | Kiến thức riêng của người phát hành - không đóng gói |
| **Kết nối MCP** (Gmail, Ads, Zalo, POS…) | Mỗi người tự đăng nhập / dán key / quét QR |
| **API key / đăng nhập Claude / ChatGPT / Antigravity** | Thuộc tài khoản cá nhân |
| **Tên miền / SSL** | Phụ thuộc VPS và DNS của bạn |

> **Nguyên tắc phân phối:** gửi phần mềm + hướng dẫn này. **Không** gửi thư mục `brains/` có memory, Drive cá nhân, mật khẩu hay hội thoại thật.

---

## 2. Chọn đúng đường cài

| Bạn đang cài trên… | Hệ điều hành | Mục đọc |
|---|---|---|
| Laptop / PC cá nhân | **Windows** | [§3](#3-máy-cá-nhân---windows) |
| Laptop / PC cá nhân | **macOS** | [§4](#4-máy-cá-nhân---macos) |
| VPS / máy chủ | **Linux** (Ubuntu, Debian, Hostinger…) | [§5](#5-vps-linux---docker-khuyến-nghị) |
| VPS / máy chủ | **Windows Server** (hoặc PC Windows chạy 24/7) | [§6](#6-vps--máy-chủ-windows) |
| Muốn link đẹp + HTTPS | Có VPS + domain (hoặc subdomain Hostinger) | [§7](#7-map-tên-miền--https) |

Cổng mặc định: **7777**. Trên máy mình: `http://localhost:7777`.

---

## 2b. Cài sẵn trước khi cài Javis (đọc trước)

Chi tiết một trang: [docs/huong-dan/CHUAN-BI-TRUOC-KHI-CAI.md](docs/huong-dan/CHUAN-BI-TRUOC-KHI-CAI.md) · HTML [mục 3](docs/huong-dan/HUONG-DAN-CAI-DAT-Javis-OS.html#chuan-bi).

| Nền tảng | Bắt buộc trên máy trước | Khuyến nghị | Tuỳ chọn |
|---|---|---|---|
| Windows PC | Python 3.11+ (tick PATH), Chrome/Edge | Node.js 22 LTS, Git | ffmpeg, Ollama, Docker Desktop |
| macOS | Xcode CLT, Python 3.11+ | Homebrew, Node 22 | ffmpeg, Ollama |
| VPS Linux | SSH được, Docker + Compose, mở cổng 22 + 7777 | apt update/upgrade, firewall | Domain / tunnel HTTPS |
| VPS Windows | RDP được; Docker Desktop *hoặc* Python+Node; Firewall 7777 | WSL2, Virtualization BIOS | HTTPS tunnel |

Không cần GPU để chat qua cloud. Mic từ máy khác cần HTTPS (không dùng `http://IP`).

---

## 3. Máy cá nhân - Windows

### 3.1 Chuẩn bị (một lần - làm trước khi chạy 1-Cai-dat)

1. Cài **Python 3.11 hoặc 3.12** từ [python.org](https://www.python.org/downloads/).  
   Khi cài: **tick** *Add python.exe to PATH*; nên bật *Disable path length limit*.  
   Kiểm tra (mở **cmd mới**): `python --version` ≥ 3.11.
2. Trình duyệt **Chrome** hoặc **Edge** (bản mới).
3. (Khuyến nghị) **Node.js 22 LTS** từ [nodejs.org](https://nodejs.org/) - Claude Code / Codex / một số kết nối (Zalo…). Kiểm tra: `node -v`.
4. (Khuyến nghị) **Git for Windows** nếu clone repo thay vì ZIP.
5. (Tuỳ chọn) **ffmpeg**: `winget install Gyan.FFmpeg` - hỗ trợ media / cuộc họp.
6. Tải **ZIP bản đóng gói** (hoặc Download ZIP từ GitHub do admin gửi).
7. Giải nén ra thư mục dễ nhớ, ví dụ `D:\Javis` (không Desktop OneDrive).
8. Double-click **`1-Cai-dat.bat`**. SmartScreen: **More info → Run anyway**. Python phải là python.org, không Microsoft Store.

### 3.2 Cài lần đầu

1. Mở thư mục vừa giải nén.
2. Double-click **`1-Cai-dat.bat`** (lần đầu có thể vài phút: tạo venv, cài thư viện).
3. Thấy dòng có `http://localhost:7777` là xong.
4. Mở Chrome / Edge → **http://localhost:7777**.
5. Tạo tài khoản admin (máy cá nhân có thể bỏ trống mật khẩu nếu chỉ mình dùng; vẫn nên đặt mật khẩu).

### 3.3 Các ngày sau

| Việc | File |
|---|---|
| Bật Javis | `2-Bat-Javis.bat` (chạy nền) hoặc `JAVIS OS.bat` (mở như app) |
| Tắt | `3-Tat-Javis.bat` hoặc `stop-javis.bat` |
| Tự chạy khi đăng nhập Windows | `javis-autostart.bat install` |

Chi tiết ngắn: [CAI-DAT-MAY-CA-NHAN.md](CAI-DAT-MAY-CA-NHAN.md).

---

## 4. Máy cá nhân - macOS

### 4.1 Chuẩn bị (một lần - làm trước Javis)

1. Mở Terminal, chạy (bắt buộc lần đầu):

```bash
xcode-select --install
```

2. Cài Python 3.11+ từ [python.org/macos](https://www.python.org/downloads/macos/) hoặc `brew install python`. Kiểm tra: `python3 --version`.
3. (Khuyến nghị) Cài [Homebrew](https://brew.sh) rồi Node.js 22 LTS (`brew install node@22` hoặc tải từ nodejs.org).
4. (Tuỳ chọn) `brew install ffmpeg` cho media.
5. Tải ZIP → giải nén ra **`~/Javis`** (không để trên Desktop iCloud - pip hay hỏng `_musllinux`).

### 4.2 Cài lần đầu

1. Chuột phải **`1-Cai-dat.command`** hay bị Apple chặn. **Kéo file vào Terminal:** gõ `bash ` (có dấu cách), thả file vào cửa sổ, Enter.

   Hoặc:

```bash
cd ~/Javis
xattr -c *.command
chmod +x *.command
bash ./1-Cai-dat.command
```

2. Đợi script xong → mở **http://localhost:7777**.
3. Tạo tài khoản admin.

Nếu vẫn muốn Finder: chuột phải → Open, hoặc **System Settings → Privacy & Security → Open Anyway**.

### 4.3 Các ngày sau

| Việc | File |
|---|---|
| Bật | `2-Bat-Javis.command` hoặc double-click `JAVIS OS.app` |
| Tắt | `3-Tat-Javis.command` |
| Tự chạy khi đăng nhập | `./bin/javis-autostart.sh install` |

---

## 5. VPS Linux - Docker (khuyến nghị)

Người chưa từng SSH / mở firewall / đặt tên miền: làm đủ trong **[HUONG-DAN-CAI-VPS-KHONG-TEN-MIEN.md](HUONG-DAN-CAI-VPS-KHONG-TEN-MIEN.md)** (từ điển, PowerShell/PuTTY, Hostinger không gõ lệnh, DuckDNS). Mục dưới là bản rút.

Cần quyền SSH vào VPS. Image mặc định fork:

`ghcr.io/duongcanhquan/javisos:latest`

> Package GHCR phải **Public** (hoặc bạn đã `docker login ghcr.io`) thì Hostinger / máy mới pull được.

### 5.0 Kết nối SSH rồi cài sẵn trên VPS

**Kết nối từ laptop (làm trước mọi lệnh):**

| Laptop bạn | Mở gì | Gõ / dán |
|---|---|---|
| Windows 10/11 | **PowerShell** (phím Windows, gõ `powershell`) | `ssh root@IP` hoặc `ssh ubuntu@IP` |
| Windows, chưa có lệnh `ssh` | Cài **OpenSSH Client** (Tính năng tùy chọn) hoặc tải **PuTTY** (putty.org): Host = IP, Port 22 | Mật khẩu VPS (gõ không hiện chữ) |
| Mac | **Terminal** | `ssh root@IP` |

Lần đầu gõ `yes`. Thấy `root@máy:~#` = đã vào VPS, mới dán lệnh Docker.

1. OS: Ubuntu 22.04/24.04 hoặc Debian 12; RAM ≥ 4 GB (khuyến nghị 8 GB).
2. `sudo apt update && sudo apt upgrade -y`.
3. **Không cần** cài Python/Node trên host nếu đi đường Docker.
4. Firewall / Security Group nhà cung cấp: mở TCP **22** và **7777** (thêm 80/443 nếu sau này HTTPS / DuckDNS).
5. Có máy tính + trình duyệt để mở `http://IP:7777` sau khi lên.

### 5.1 Cài Docker (nếu chưa có)

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker "$USER"
# Đăng xuất SSH rồi vào lại để group docker có hiệu lực
```

### 5.2 Cách nhanh - VPS bất kỳ (IP:7777)

```bash
mkdir -p ~/javis && cd ~/javis
curl -fsSLO https://raw.githubusercontent.com/duongcanhquan/javisOS/main/docker-compose.yml
printf 'JAVIS_ADMIN_USER=admin\nJAVIS_ADMIN_PASSWORD=DoiMatKhauManh\n' > .env
docker compose up -d
```

Mở `http://<IP-VPS>:7777`.  
Xem log / MÃ THIẾT LẬP:

```bash
docker compose logs javis | tail -80
# hoặc trong container:
docker compose exec javis cat /data/state/.setup_token
```

Lệnh hằng ngày:

```bash
docker compose logs -f      # theo dõi
docker compose restart      # khởi động lại
docker compose pull && docker compose up -d   # cập nhật image
docker compose down         # tắt (data trong volume vẫn còn)
```

### 5.3 Hostinger Docker Manager (HTTPS dễ nhất)

1. hPanel → **VPS** → **Docker Manager** → **Compose** → **URL**.
2. Dán:

```text
https://raw.githubusercontent.com/duongcanhquan/javisOS/main/docker-compose.hostinger.yml
```

(Hoặc bản trường: `.../deploy/school/docker-compose.hostinger.yml`)

3. Ô **Environment** điền tối thiểu:

| Biến | Ví dụ | Ý nghĩa |
|---|---|---|
| `DOMAIN_NAME` | `javis.srvXXXX.hstgr.cloud` hoặc `javis.tencuaban.com` | Link HTTPS |
| `JAVIS_ADMIN_USER` | `admin` | Tài khoản |
| `JAVIS_ADMIN_PASSWORD` | mật khẩu mạnh (≥8) | Đăng nhập ngay, không cần MÃ THIẾT LẬP |

4. **Deploy** → đợi 1-3 phút Traefik cấp SSL → mở `https://<DOMAIN_NAME>`.

**Subdomain miễn phí Hostinger (không mua domain):**

1. Xem hostname VPS ở hPanel (vd `srv1782015.hstgr.cloud`).
2. Đặt `DOMAIN_NAME=javis.srv1782015.hstgr.cloud`.
3. Không cần tạo bản ghi DNS tay - wildcard `*.hstgr.cloud` đã có.

### 5.4 Linux native (không Docker)

```bash
git clone https://github.com/duongcanhquan/javisOS.git javis && cd javis
chmod +x install.sh && ./install.sh
```

Script cài Python/Node/CLI, tạo venv, đăng ký **systemd** tự chạy khi boot. Chi tiết: [DEPLOY.md](DEPLOY.md).

---

## 6. VPS / máy chủ Windows

Từng nút (Remote Desktop, Docker, DuckDNS): [HUONG-DAN-CAI-VPS-KHONG-TEN-MIEN.md](HUONG-DAN-CAI-VPS-KHONG-TEN-MIEN.md) mục D–G.

### 6.0 Kết nối RDP rồi cài sẵn trước

1. **Laptop Windows:** phím Windows → gõ `Remote Desktop` / `mstsc` → ô Máy tính = **IP VPS** → user `Administrator` + mật khẩu.
2. **Laptop Mac:** App Store → **Windows App** (Microsoft Remote Desktop) → Add PC = IP.
3. Không vào được: panel VPS mở cổng **3389**; thử Reset password.
4. Bật **Virtualization** trong BIOS nếu dùng Docker Desktop + WSL2.
5. Chọn một đường: **Docker Desktop** (khuyến nghị) *hoặc* Python 3.11+ (tick PATH) + Node.js 22.
6. Windows Firewall: inbound TCP **7777** (và 3389 nếu RDP; 80/443 nếu tên miền HTTPS).

### 6.1 Docker Desktop (gần giống Linux)

1. Cài [Docker Desktop](https://www.docker.com/products/docker-desktop/) (bật WSL2 nếu được hỏi). Đợi engine xanh.
2. PowerShell:

```powershell
mkdir $HOME\javis; cd $HOME\javis
Invoke-WebRequest -Uri https://raw.githubusercontent.com/duongcanhquan/javisOS/main/docker-compose.yml -OutFile docker-compose.yml
@"
JAVIS_ADMIN_USER=admin
JAVIS_ADMIN_PASSWORD=DoiMatKhauManh
"@ | Set-Content -Encoding ascii .env
docker compose up -d
```

3. Mở `http://<IP>:7777`. Mở **Windows Firewall** inbound TCP **7777** (và **80/443** nếu dùng reverse proxy).
4. Cập nhật: `docker compose pull` rồi `docker compose up -d`.

### 6.2 Native Windows (không Docker, chạy 24/7)

Giống máy cá nhân (§3) nhưng:

1. Giải nén trên ổ máy chủ, chạy `1-Cai-dat.bat`.
2. `javis-autostart.bat install` để tự bật khi đăng nhập.
3. Trong `.env` (copy từ `env.example` nếu chưa có):

```text
JAVIS_HOST=0.0.0.0
JAVIS_ADMIN_USER=admin
JAVIS_ADMIN_PASSWORD=DoiMatKhauManh
```

4. Javis **bắt buộc đăng nhập** khi chạy public.
5. Đăng nhập Claude / Antigravity trên VPS không màn hình: tab **Code / Terminal** trong dashboard.

---

## 7. Map tên miền & HTTPS

### 7.1 Vì sao cần HTTPS

- Link đẹp, không nhớ IP:cổng.
- **Micro / giọng nói** trên trình duyệt **chỉ** chạy trên `https://` hoặc `localhost`.  
  Mở `http://IP:7777` từ máy khác → mic bị chặn.

### 7.2 Hostinger (Traefik) - cách ngắn

Đã mô tả ở §5.3: chỉ cần `DOMAIN_NAME` đúng.

**Tên miền riêng trên Hostinger:**

1. Mua / trỏ domain về VPS.
2. DNS nhà cung cấp domain:

| Loại | Name | Value |
|---|---|---|
| **A** | `javis` (hoặc `@` nếu dùng root) | IP VPS Hostinger |

3. Đặt `DOMAIN_NAME=javis.tencuaban.com` trong Docker Manager → Redeploy.
4. Đợi DNS lan (vài phút đến vài giờ) → mở `https://javis.tencuaban.com`.

Trên Hostinger, nút **Bật SSL** trong Cài đặt app thường **ẩn** - Traefik lo SSL.

### 7.3 VPS tự quản + Caddy (docker-compose.https.yml)

1. Deploy Javis bằng `docker-compose.yml` trước (chạy được bằng IP).
2. Trỏ DNS **A** của `javis.tencuaban.com` → IP VPS. Mở firewall **80** và **443**.
3. Chạy kèm lớp HTTPS:

```bash
cd ~/javis
# file https nằm cùng repo; tải thêm nếu chỉ có compose gốc:
curl -fsSLO https://raw.githubusercontent.com/duongcanhquan/javisOS/main/docker-compose.https.yml
docker compose -f docker-compose.yml -f docker-compose.https.yml up -d
```

4. Trong app: **Cài đặt → Giọng nói, thương hiệu & truy cập → TÊN MIỀN & SSL**:
   - Nhập `javis.tencuaban.com` → **Lưu & kiểm tra**.
   - Khi badge DNS = đã trỏ đúng → **Bật SSL**.
   - Mở `https://javis.tencuaban.com`.

Hướng dẫn UI đầy đủ: [docs/15-thuong-hieu-ten-mien.md](docs/15-thuong-hieu-ten-mien.md).

### 7.4 Tên miền miễn phí (không mua domain)

Chọn **một**:

| Cách | Việc làm | Link |
|---|---|---|
| **Hostinger** | `DOMAIN_NAME=javis.<hostname>.hstgr.cloud` | `https://javis.srv….hstgr.cloud` |
| **DuckDNS** | duckdns.org đăng nhập Google → tạo `tenban.duckdns.org` trỏ IP VPS → bật `docker-compose.https.yml` → trong app **Tên miền & SSL** → **Bật SSL** | `https://tenban.duckdns.org` |
| **Cloudflare Tunnel** | lệnh dưới | `https://….trycloudflare.com` (đổi mỗi restart) |

Từng nút DuckDNS / Hostinger / tunnel: [HUONG-DAN-CAI-VPS-KHONG-TEN-MIEN.md](HUONG-DAN-CAI-VPS-KHONG-TEN-MIEN.md) mục G.

```bash
docker compose --profile tunnel up -d
docker compose logs tunnel | grep trycloudflare
```

Mở URL `https://….trycloudflare.com`. Muốn URL cố định: DuckDNS (trên) hoặc *named tunnel* + `TUNNEL_TOKEN` (xem [DEPLOY.md](DEPLOY.md)).

### 7.5 Checklist DNS nhanh

1. `ping javis.tencuaban.com` (hoặc tra A record) phải ra **đúng IP VPS**.
2. Cổng 80/443 mở với thế giới (hoặc Traefik Hostinger đã mở).
3. Không trỏ CNAME vòng về chỗ khác khi đang dùng bản ghi A.
4. Sau khi đổi DNS, đợi TTL rồi **Kiểm tra lại** trong Cài đặt.

---

## 8. Thiết lập lần đầu trong app (mọi đường)

Làm **ít nhất** 3 việc rồi dừng: **admin** + **Models** + chat một câu. Gmail / Zalo / Ads / Hội thoại khách để lần sau.

### Bước A - Tài khoản admin

- Máy cá nhân: wizard chào mừng → Workspace + (tuỳ chọn) mật khẩu.
- VPS công khai: **bắt buộc** mật khẩu ≥8 ký tự. Nếu chưa set sẵn trong compose → nhập **MÃ THIẾT LẬP** (log / file `.setup_token`).

Chi tiết: [docs/01-bat-dau-thiet-lap.md](docs/01-bat-dau-thiet-lap.md).

### Bước B - Chọn bộ não (Models)

Nhóm **Kết nối → Models**. Chọn **một** đường phổ biến:

| Đường | Cần gì | Ghi chú |
|---|---|---|
| **Claude Code** | Đăng nhập subscription (link + code) | Đủ tool + shell; cẩn thận khi chạy nền 24/7 trên gói Pro/Max |
| **ChatGPT (Codex)** | Đăng nhập ChatGPT Plus/Pro | Vẫn dùng MCP hub của Javis |
| **Grok Build** | Đăng nhập SuperGrok / X Premium+ | CLI `grok`, gắn plan không cần API key |
| **Antigravity CLI** | Cài `agy`, đăng nhập một lần | Lineup model Google plan; VPS: in link trong terminal |
| **OpenRouter / OpenAI / Gemini / Anthropic / Groq / DeepSeek / Ollama** | API key | Không cần CLI; không chạy lệnh máy |

**Nhiều bản trên một VPS:** mỗi subdomain tự đấu não một lần. Chi tiết: [docs/30-nhieu-ban-va-dau-nao.md](docs/30-nhieu-ban-va-dau-nao.md).

Sau khi kết nối: chọn **Main Model** + (tuỳ chọn) **Model việc nền** rẻ hơn. Chi tiết: [docs/10-models-va-engine.md](docs/10-models-va-engine.md).

### Bước C - Năng lực chuẩn (tự có sẵn)

Image / bản đóng gói **tự đồng bộ** skill + agent + workflow hệ thống vào mỗi brain mới. Không bắt buộc seed tay.

Sau khi Models + chat thử được: mở **Năng lực → Cộng sự** để thấy danh sách Trợ Lý / Quy Trình chuẩn. Muốn làm mới bộ theo ngành (Trường, Bài giảng, Marketing, Video, Pháp chế…): dùng các nút seed trên trang Cộng sự / form Studio (modal), không còn mục «Studio» riêng trên rail.

Agents / workflows chuẩn nằm trong `system/agents/` và `system/workflows/`. Agent nội bộ tổ chức **không** đi kèm image công khai.

### Bước D - Brain & Project

1. Tạo / chọn **brain** theo ngữ cảnh (công việc vs học tập). Mỗi brain có memory / wiki / sources riêng.
2. **Project** chỉ thuộc brain đang chọn.
3. Skill / agent / workflow **chuẩn** dùng chung trên instance; nội dung vault vẫn riêng từng não.

---

## 9. Bản đồ menu trái (nhiệm vụ từng nhóm)

Menu trái (rail) gom trang thành nhóm. Hiểu **nhiệm vụ từng nhóm** rồi mới đi sâu chức năng.

| Nhóm rail | Nhiệm vụ chính | Trang trên menu |
|---|---|---|
| **Trợ lý** | Trang chủ + nói chuyện với AI trên web | Home · Chat |
| **Bộ não** | File / Drive / học từ tri thức gắn brain | Files · Kho Drive · Tự học |
| **Code** | Dòng lệnh thật trên máy/container đang chạy Javis | Terminal |
| **Năng lực** | Đội AI + hộp thư khách + skill + plugin | **Cộng sự** · **Hội thoại khách** · Skills · Plugins |
| **Việc** | Họp, bài giảng, video, marketing, Kanban, tự cải thiện | Họp · Bài giảng · Video · Marketing · Kanban · … |
| **Kết nối** | Não AI + MCP + kênh điện thoại + gói + API công cụ | Models · Kết nối · Kênh · Gói · API công cụ |
| **Hướng dẫn** | Đọc hướng dẫn ngay trong app (4 trang) | VMOS làm được gì · Kết nối · Skill/Agent · Công việc |
| **Hệ thống** (đáy) | Mức dùng, cài đặt, **chia sẻ link**, log, tài khoản | Mức dùng · Cài đặt · **Chia sẻ** · Log · Tài khoản |
| **Tổ chức** (đáy, nếu có) | Quản trị multi-tenant / org | Tổ chức |

**Luồng nên nhớ:** Models (não) → Chat thử → **Cộng sự** / Skills → Kết nối MCP / Kênh → (tuỳ) **Hội thoại khách** & **Chia sẻ**.

---

## 10. Chức năng mới & cách dùng chi tiết

### 10.1 Cộng sự (Agent + Workflow trong một trang)

**Mở ở đâu:** rail **Năng lực → Cộng sự**.

**Nhiệm vụ trang:** một chỗ quản lý «đội AI» của bạn. Hai tab phía trên:

| Tab | Tên hiển thị | Là gì | Khi nào dùng |
|---|---|---|---|
| Agent | **Trợ Lý (Agent)** | Một trợ lý có vai trò, prompt, skill, model | Muốn «nhân viên» chuyên một mảng |
| Workflow | **Quy Trình (Workflows)** | Chuỗi nhiều bước / nhiều agent | Việc nhiều giai đoạn, bàn giao giữa các vai |

(Tên cũ «Agents» / «Workflows» trên rail đã bỏ - URL cũ `/agents`, `/workflows` vẫn chuyển vào Cộng sự.)

#### Tab Trợ Lý (Agent)

1. Bấm **+ Agent** (hoặc mở thẻ agent sẵn có).
2. Điền **vai trò** 2–3 dòng tiếng Việt: làm gì, khi nào, cần dữ liệu gì.
3. Tick **skills** được phép dùng; chọn **model** (hoặc mặc định).
4. Viết **system prompt** chi tiết (cách làm, định dạng đầu ra, điều cấm).
5. **Tài liệu trợ lý:** mỗi agent có tủ tài liệu riêng (file hướng dẫn / mẫu). Khác **Tủ tài liệu phiên** trong chat (chỉ gắn phiên hiện tại).

**Chạy agent ở đâu?** Trong Quy trình, Hội thoại khách, hoặc khi bạn nhờ VMOS dùng agent đó trong chat.

Chi tiết sâu: [docs/07-agents-va-workflows.md](docs/07-agents-va-workflows.md).

#### Tab Quy Trình (Workflows)

1. Chuyển tab **Quy Trình (Workflows)**. Brain mới có thể bấm tạo mẫu để có ví dụ chạy được.
2. Mỗi bước chọn agent + mô tả nhiệm vụ. Dùng `{{input}}` cho đầu vào user, `{{prev}}` cho kết quả bước trước.
3. Bật quy trình → **▶ Chạy** (hoặc gọi từ Telegram / Kanban tùy cấu hình).

**Sơ đồ nhanh:**

```
Skill (công thức)  →  Agent / Trợ lý (nhân viên)  →  Workflow / Quy trình (dây chuyền)
```

| Lớp | File / chỗ | Ví dụ |
|---|---|---|
| **Skill** | Năng lực → Skills | Viết SEO, đọc hóa đơn |
| **Agent** | Cộng sự → Trợ Lý | «Nghiên cứu thị trường» |
| **Workflow** | Cộng sự → Quy Trình | Nghiên cứu → viết → kiểm chứng |

### 10.2 Skills (vẫn trong Năng lực)

**Skills:** rail **Năng lực → Skills** - bật/tắt thẻ skill; tạo mới với mô tả tiếng Việt rõ; trong Chat gõ `/` để gọi tay.

Seed bộ năng lực theo ngành (Trường, Marketing, Video…) nằm trên **Cộng sự** / modal Studio khi tạo mẫu - xem [docs/07-agents-va-workflows.md](docs/07-agents-va-workflows.md).

### 10.3 Hội thoại khách (bot chuyên trách + hộp thư)

**Mở ở đâu:** rail **Năng lực → Hội thoại khách**.

**Nhiệm vụ:** một trang gom **hộp thư khách**, **kênh** (Telegram / Zalo…) và **chatbot chuyên trách**. Đem Agent ra nói chuyện với khách bên ngoài, đọc lại tin, tiếp quản khi bot bí.

Trong trang thường có các tab (Hộp thư · Kênh · Chatbot) - xem chi tiết [docs/28-hoi-thoai-khach.md](docs/28-hoi-thoai-khach.md).

**Không nhầm với:**

| | Hội thoại khách | Kênh (Kết nối → Kênh) | Chat (Trợ lý) |
|---|---|---|---|
| Ai nói chuyện | Khách ↔ bot / bạn tiếp quản | Bạn cấu hình bot token để **Javis của mình** nhận tin | Bạn ↔ Javis trên web |
| Brain | Brain gắn chatbot | Theo cấu hình kênh chính | Brain bạn đang chọn |
| Mục đích | CSKH / tư vấn có kiểm soát | Điều khiển Javis từ điện thoại | Làm việc hàng ngày trên dashboard |

**Các bước điển hình:**

1. Trong **Cộng sự → Trợ Lý** tạo / chọn Agent đủ giỏi cho chủ đề.
2. Mở **Hội thoại khách** → tab Chatbot → tạo bot → chọn Agent + gắn tài khoản kênh.
3. Gắn brain riêng cho bot (tránh lẫn memory cá nhân).
4. Kiểm tra: nhắn từ số khách thử → xem **Hộp thư** trên cùng trang.

Chi tiết: [docs/28-hoi-thoai-khach.md](docs/28-hoi-thoai-khach.md) · [docs/25-chatbot.md](docs/25-chatbot.md).

### 10.4 Chia sẻ (link công khai)

**Mở ở đâu:** rail **Hệ thống → Chia sẻ**.

**Nhiệm vụ:** quản lý **link / tài nguyên công khai** bạn đã tạo (agent/workflow được share, trang public…). Đây là chỗ **theo dõi và thu hồi**, không phải chỗ tạo Agent.

| Việc | Làm ở đâu |
|---|---|
| Tạo Agent / Workflow | **Năng lực → Cộng sự** |
| Bật chia sẻ / lấy link | Trong thẻ Cộng sự (nút chia sẻ trên item) hoặc luồng share của trang đó |
| Xem danh sách link đang mở, tắt chia sẻ | **Hệ thống → Chia sẻ** |

### 10.5 Kết nối dịch vụ ngoài (người dùng tự làm)

Bản đóng gói **không** sẵn Gmail/Ads/Zalo của người phát hành. Mỗi người tự gắn.

#### Luồng chung MCP

1. Rail **Kết nối → Kết nối**.
2. Nhiều dịch vụ nằm trong tab **VMOS Store**: tìm → **Cài đặt** → quay lại **Kết nối sẵn có**.
3. Bấm **Kết nối** trên thẻ → dán key / OAuth / quét QR.
4. Chọn **mức quyền** trên chip tài khoản: Chỉ đọc / Ghi nháp / Toàn quyền.
5. Kiểm tra bằng chat: «kiểm tra kết nối …» hoặc hỏi số liệu thật.

Chi tiết từng dịch vụ: [docs/09-mcp-va-so-lieu.md](docs/09-mcp-va-so-lieu.md).

#### Bảng lối tắt

| Muốn… | Làm gì | Tài liệu |
|---|---|---|
| Đổi / thêm bộ não AI | Models | [docs/10-models-va-engine.md](docs/10-models-va-engine.md) |
| Hỏi Javis trên điện thoại | Kết nối → Kênh → Telegram | [docs/11-telegram.md](docs/11-telegram.md) |
| Zalo Bot chính thức | Kênh Zalo Bot | [docs/26-kenh-zalo-bot.md](docs/26-kenh-zalo-bot.md) |
| Đọc/gửi Zalo cá nhân (MCP) | Zalo Agent - quét QR | [docs/12-zalo.md](docs/12-zalo.md) |
| Bot CSKH mang đúng một Agent | **Năng lực → Hội thoại khách** | [docs/28-hoi-thoai-khach.md](docs/28-hoi-thoai-khach.md) |
| Gmail / Lịch / Drive / Sheets | Thẻ Google trên Kết nối | [docs/09-mcp-va-so-lieu.md](docs/09-mcp-va-so-lieu.md) |
| Meta Ads / Facebook Page | Store rồi OAuth / token | [docs/09](docs/09-mcp-va-so-lieu.md) |
| Kho Drive → Second Brain | Bộ não → Kho Drive | [docs/29-kho-drive.md](docs/29-kho-drive.md) |
| Sao lưu brain lên GitHub | Hệ thống / Sao lưu | [docs/18-sao-luu-github.md](docs/18-sao-luu-github.md) |
| Logo + domain | Cài đặt → Thương hiệu & tên miền | [docs/15-thuong-hieu-ten-mien.md](docs/15-thuong-hieu-ten-mien.md) |
| Xem / tắt link public | **Hệ thống → Chia sẻ** | (trang trong app) |

#### An toàn khi kết nối

- Không dán API key vào chat công khai; chỉ vào ô Kết nối.
- Zalo Agent MCP **không chính thức** - nên dùng số phụ.
- Mức **Toàn quyền** cho phép gửi tin / đăng bài / thao tác tiền - chỉ bật khi cần.
- Không chia sẻ một subscription Claude Pro cho nhiều người chạy nền 24/7 trên VPS.

### 10.6 Tủ tài liệu: Agent vs phiên chat

| Loại | Ở đâu | Phạm vi | Dùng khi |
|---|---|---|---|
| **Tài liệu trợ lý** | Cộng sự → mở Agent → khu tài liệu | Gắn **đúng agent đó**, mọi lần chạy agent | SOP, mẫu trả lời, tài liệu chuẩn của vai trò |
| **Tủ tài liệu phiên** | Trong Chat (phiên đang mở) | Chỉ **phiên hội thoại hiện tại** | File / ghi chú phục vụ cuộc nói chuyện này |

Không nhầm hai tủ: xóa phiên chat **không** xóa tài liệu trợ lý; sửa agent **không** tự gắn file vào mọi phiên cũ.

### 10.7 Chat, Việc, Bộ não (nhắc nhanh)

- **Chat (Trợ lý):** hỏi việc hàng ngày; lệnh `/`; đính kèm file phiên; giọng nói cần HTTPS (§7).
- **Kanban / Việc định kỳ (Việc):** giao goal bằng lời; AI chạy task nền.
- **Wiki / Memory / Files / Tự học (Bộ não):** tri thức lâu dài theo brain; Tự học có thể hoàn tác.
- **Terminal (Code):** lệnh thật trên host/container - cẩn thận trên VPS production.

---

## 11. Danh mục năng lực đóng gói (tham chiếu)

### Skills hệ thống (ví dụ nhóm chính)

Đi kèm image / ZIP (đồng bộ qua `system_sync`):

- **Lõi:** `javis-builder`, `ingest-source`, `query-wiki`, `lint-wiki`, `notes`, `html-to-webcake`
- **Nghiên cứu & KD/MKT:** `nghien-cuu-thi-truong`, `ke-hoach-kinh-doanh`, `ke-hoach-marketing`, `phan-tich-tai-chinh-mkt`, `proposal-chien-luoc`, `writing-plans`, `brainstorming`
- **Marketing / SEO:** `marketing-hub`, `kiem-tra-seo`, `seo-gpt`, `viet-bai-seo`, `bao-cao-facebook-ads`
- **Bài giảng / nội dung:** `tao-bai-giang`, `bai-giang-lop-hoc`, `bai-giang-slide`, `openmaic`
- **Video / Pháp chế / Vận hành / Kế toán / UI:** xem thư mục `.claude/skills/` trong bản đóng gói

### Agents / Workflows không đưa vào bản công khai

Vai trò **riêng tổ chức** (không seed cho người lạ): xem [`system/EXCLUDE-AGENTS.md`](system/EXCLUDE-AGENTS.md).  
Người nhận tự xây agent trong **Cộng sự** của brain họ. Caps dùng chung: [`system/README-CAPS.md`](system/README-CAPS.md).

---

## 12. Checklist người phát hành (trước khi gửi bản đóng gói)

Dùng khi bạn **đóng gói để người khác cài**:

1. [ ] Image GHCR / ZIP build từ `main` đã xanh CI.
2. [ ] README / compose trỏ đúng registry fork (`ghcr.io/duongcanhquan/javisos`).
3. [ ] Skills hệ thống nằm trong `.claude/skills/` (đủ bộ bạn muốn ship).
4. [ ] Agents / workflows chuẩn có đường nạp: sync hệ thống và/hoặc Studio seed / `deploy/caps-bundles/*.zip`.
5. [ ] **Không** đóng gói `brains/*/memory`, sources cá nhân, `.env` có secret, volume state cũ.
6. [ ] Kèm file này + [docs/huong-dan/HUONG-DAN-SU-DUNG-Javis-OS.pdf](docs/huong-dan/) (nếu có).
7. [ ] Thử sạch: cài → Models → chat → mở **Cộng sự** thấy agent/workflow chuẩn → Kết nối một dịch vụ thử.
8. [ ] Viết rõ cho người nhận: họ **tự** Models + Kết nối; không kỳ vọng sẵn Gmail/Ads của bạn.

---

## 13. Lỗi thường gặp

| Hiện tượng | Cách xử lý |
|---|---|
| Windows: `python` không nhận / Store | python.org, tick PATH, không bản Store; `py -3.12`; SmartScreen: More info → Run anyway |
| Mac: Apple không xác minh `.command` | Terminal: gõ `bash `, kéo file thả vào, Enter |
| `_musllinux` / `No module named yaml` | Xoá `.venv`, copy folder ra `~/Javis` hoặc `D:\Javis`, chạy lại `1-Cai-dat` |
| Pull image fail | GHCR chưa Public / sai tên image / hết disk |
| Mở app hỏi MÃ THIẾT LẬP | `docker compose logs` hoặc `cat /data/state/.setup_token`; hoặc điền sẵn admin trong `.env` |
| Chat báo chưa có bộ não | Models chưa đăng nhập / thiếu API key |
| Không thấy menu Agents / Workflows | Đã gộp thành **Năng lực → Cộng sự** (tab Trợ Lý / Quy Trình) |
| Cộng sự / Studio trống năng lực | Đợi sync hệ thống; hoặc Studio seed **Bộ …** tương ứng |
| Không tìm Chatbots | Đã gộp vào **Năng lực → Hội thoại khách** (tab Chatbot) |
| Mic không bật trên VPS | Chưa HTTPS - làm §7 |
| Hostinger không HTTPS | Sai / thiếu `DOMAIN_NAME` |
| Thấy Project não khác | Sai brain đang chọn - chọn đúng não / sửa project lệch |
| Banner «bản cũ» dù Ctrl+Shift+R | CDN cache path cũ; bấm **Xóa cache** trên banner hoặc đợi deploy asset mới |
| Firewall Windows chặn | Mở inbound TCP 7777 (và 80/443 nếu proxy) |
| Docker Desktop chưa sẵn sàng | Mở Docker Desktop, đợi xanh, `docker compose up -d` lại |

Thêm FAQ: [docs/17-khac-phuc-su-co.md](docs/17-khac-phuc-su-co.md).

---

## 14. Bản đồ tài liệu liên quan

| File | Khi nào mở |
|---|---|
| [CAI-DAT-MAY-CA-NHAN.md](CAI-DAT-MAY-CA-NHAN.md) | Chỉ Windows/Mac double-click |
| [CAI-DAT-TRUONG.md](CAI-DAT-TRUONG.md) | Phát cho giáo viên / trường |
| [DEPLOY.md](DEPLOY.md) | VPS, HTTPS, nhiều bản trên một máy |
| [QUICKSTART.md](QUICKSTART.md) | Chạy dev từ source |
| [docs/01-bat-dau-thiet-lap.md](docs/01-bat-dau-thiet-lap.md) | Wizard lần đầu |
| [docs/07-agents-va-workflows.md](docs/07-agents-va-workflows.md) | Cộng sự: Agent + Workflow |
| [docs/28-hoi-thoai-khach.md](docs/28-hoi-thoai-khach.md) | Hội thoại khách |
| [docs/09-mcp-va-so-lieu.md](docs/09-mcp-va-so-lieu.md) | Kết nối từng dịch vụ |
| [docs/15-thuong-hieu-ten-mien.md](docs/15-thuong-hieu-ten-mien.md) | Domain trong UI |
| [docs/README.md](docs/README.md) | Mục lục toàn bộ chức năng |

---

*Cập nhật theo phiên bản app trong file `VERSION`. Quy ước: không dùng em dash; Project theo brain; skill/agent/workflow chuẩn dùng chung instance; kết nối do người dùng tự gắn; Agents/Workflows = Cộng sự; Chatbots = Hội thoại khách.*
