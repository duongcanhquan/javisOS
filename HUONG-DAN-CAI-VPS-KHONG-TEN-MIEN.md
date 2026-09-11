# Cài Javis trên VPS mới (không có tên miền)

Dành cho người vừa mua VPS Linux hoặc Windows, **chưa mua / chưa trỏ domain**.  
Sau khi làm xong bạn mở Javis bằng **IP** hoặc **link HTTPS tạm** (tunnel / subdomain Hostinger miễn phí).

Tài liệu tổng quát hơn: [HUONG-DAN-CAI-DAT-VA-SU-DUNG.md](HUONG-DAN-CAI-DAT-VA-SU-DUNG.md) · kỹ thuật sâu: [DEPLOY.md](DEPLOY.md).

---

## 0. Không có tên miền thì dùng thế nào?

| Cách | Link dạng | Mic / giọng nói | Khi nào chọn |
|---|---|---|---|
| **A. IP + cổng** | `http://12.34.56.78:7777` | **Không** (trình duyệt chặn mic trên HTTP+IP) | Chat chữ, cấu hình nhanh, nội bộ |
| **B. Cloudflare Tunnel (quick)** | `https://….trycloudflare.com` | **Có** | Muốn mic / mở từ điện thoại, chưa mua domain |
| **C. Subdomain Hostinger miễn phí** | `https://javis.srvXXXX.hstgr.cloud` | **Có** | VPS **Hostinger** (không cần mua domain) |
| **D. SSH tunnel về máy bạn** | `http://localhost:7777` trên laptop | Có (vì localhost) | Chỉ mình bạn dùng, an toàn hơn |

> **Không có chứng chỉ HTTPS cho IP trần.** Muốn mic / voice trên điện thoại hoặc máy khác → chọn **B** hoặc **C** (hoặc sau này mua domain + DNS).

**Khuyến nghị người mới:** cài bằng **A** trước → tạo admin + Models → nếu cần mic thì bật **B**.

---

## 1. Cấu hình VPS tối thiểu

| | Tối thiểu (chạy được) | Khuyến nghị |
|---|---|---|
| **CPU** | 2 vCPU | 2–4 vCPU |
| **RAM** | **4 GB** | **8 GB** |
| **Ổ** | 20 GB SSD | 40 GB+ SSD |
| **OS** | Ubuntu 22.04/24.04 LTS, Debian 12; hoặc Windows Server / Windows 10+ có Docker | Ubuntu 24.04 |
| **Mạng** | IP public, mở cổng **7777** (và 22 SSH) | Firewall chỉ mở 22 + 7777 (hoặc chỉ 22 nếu chỉ dùng tunnel) |

Ghi chú:

- 4 GB RAM: Docker + Javis chạy được; tránh bật thêm nhiều container nặng trên cùng máy.
- Việc nền 24/7 + nhiều brain: ưu tiên **8 GB**.
- Không cần GPU. Model AI chạy qua subscription / API key của bạn (Claude, ChatGPT, OpenRouter…), không bắt buộc cài model local trên VPS.

Bạn cần sẵn **trước khi cài Javis**:

1. IP VPS + user SSH (thường `root` hoặc `ubuntu`) + mật khẩu / key.
2. Máy tính có Terminal (Mac/Linux) hoặc PowerShell / PuTTY (Windows) để SSH.
3. Trình duyệt Chrome / Edge.
4. (Linux Docker) Chưa cần Python/Node trên VPS - sẽ cài Docker ở bước sau.
5. Firewall panel nhà cung cấp: sẵn sàng mở TCP **22** và **7777**.
6. Bảng đủ nền tảng: [docs/huong-dan/CHUAN-BI-TRUOC-KHI-CAI.md](docs/huong-dan/CHUAN-BI-TRUOC-KHI-CAI.md).

---

## 2. VPS Linux (Ubuntu / Debian) - từng bước

### Bước 1 - SSH vào máy

Trên máy cá nhân:

```bash
ssh root@IP_VPS
# hoặc: ssh ubuntu@IP_VPS
```

Lần đầu gõ `yes` rồi nhập mật khẩu / dùng key.

Cập nhật hệ thống (khuyến nghị):

```bash
sudo apt update && sudo apt upgrade -y
```

### Bước 2 - Mở cổng 7777 trên firewall

**ufw (Ubuntu):**

```bash
sudo ufw allow 22/tcp
sudo ufw allow 7777/tcp
sudo ufw enable
sudo ufw status
```

Nếu nhà cung cấp có **Security Group / Cloud Firewall** (Contabo, DigitalOcean, AWS…): vào panel → mở inbound **TCP 7777** (và 22).

### Bước 3 - Cài Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker "$USER"
```

Đăng xuất SSH rồi SSH lại (để group `docker` có hiệu lực). Kiểm tra:

```bash
docker version
docker compose version
```

### Bước 4 - Chạy Javis (không cần domain)

```bash
mkdir -p ~/javis && cd ~/javis
curl -fsSLO https://raw.githubusercontent.com/duongcanhquan/javisOS/main/docker-compose.yml
docker compose up -d
```

Đợi khoảng 1–3 phút lần đầu (kéo image). Xem trạng thái:

```bash
docker compose ps
docker compose logs javis | tail -50
```

### Bước 5 - Mở bằng IP (cách A)

Trên trình duyệt máy nhà:

```text
http://IP_VPS:7777
```

Thay `IP_VPS` bằng IP thật (vd `http://103.20.1.50:7777`).

VPS công khai → Javis **bắt buộc** tạo tài khoản admin (mật khẩu ≥ 8 ký tự).  
Nếu hỏi **MÃ THIẾT LẬP**:

```bash
cd ~/javis
docker compose exec javis cat /data/state/.setup_token
```

Copy chuỗi → dán vào màn hình tạo tài khoản.

### Bước 6 - Đăng nhập bộ não AI

Trong app: **Kết nối → Models** → chọn một đường:

- Claude Code / ChatGPT / Antigravity (subscription), hoặc
- OpenRouter / OpenAI / Gemini API… (dán API key)

Không có domain vẫn chat chữ bình thường qua `http://IP:7777`.

Agent / workflow / skill chuẩn **đã có sẵn** trong image (không cần bấm Studio).

### Bước 7 (tuỳ chọn) - HTTPS + mic không cần domain (cách B)

Vẫn trong `~/javis`:

```bash
docker compose --profile tunnel up -d
docker compose logs tunnel | grep trycloudflare
```

Mở link `https://….trycloudflare.com` in ra → mic/voice dùng được.

Lưu ý:

- URL **đổi mỗi lần** restart tunnel.
- Nên đã có mật khẩu admin trước khi share link này.
- Muốn URL cố định sau này: mua domain, hoặc *named tunnel* Cloudflare (xem [DEPLOY.md](DEPLOY.md)).

### Lệnh dùng hàng ngày (Linux)

```bash
cd ~/javis
docker compose logs -f          # xem log
docker compose restart          # khởi động lại
docker compose pull && docker compose up -d   # cập nhật
docker compose down             # tắt (data trong volume Docker vẫn còn)
```

---

## 3. VPS / máy chủ Windows

### 3.0 Cài sẵn trước

1. RDP vào máy (hoặc SSH nếu có).
2. Bật Virtualization trong BIOS nếu dùng Docker + WSL2.
3. Chọn đường Docker Desktop **hoặc** Python 3.11+ (PATH) + Node 22.
4. Chuẩn bị mở Windows Firewall TCP **7777**.

### 3.1 Cách khuyến nghị: Docker Desktop

1. Cài [Docker Desktop](https://www.docker.com/products/docker-desktop/) (bật **WSL2** nếu được hỏi). Đợi icon Docker xanh.
2. Mở **PowerShell**:

```powershell
mkdir $HOME\javis; cd $HOME\javis
Invoke-WebRequest -Uri https://raw.githubusercontent.com/duongcanhquan/javisOS/main/docker-compose.yml -OutFile docker-compose.yml
docker compose up -d
```

3. **Windows Firewall:** cho phép inbound **TCP 7777** (và 22 nếu Remote Desktop/SSH).
4. Mở trình duyệt: `http://IP_MAY:7777` → tạo admin → Models.

Tunnel HTTPS (mic):

```powershell
cd $HOME\javis
docker compose --profile tunnel up -d
docker compose logs tunnel
# tìm dòng có trycloudflare.com
```

Cập nhật:

```powershell
docker compose pull
docker compose up -d
```

### 3.2 Không Docker (native Windows)

Giống máy cá nhân, nhưng máy chạy 24/7:

1. Cài **Python 3.11+** (tick *Add to PATH*) + **Node.js 22 LTS**.
2. Tải ZIP repo: https://github.com/duongcanhquan/javisOS → Code → Download ZIP → giải nén.
3. Chạy **`1-Cai-dat.bat`** lần đầu; sau đó **`2-Bat-Javis.bat`** (hoặc `javis-autostart.bat install`).
4. Mở firewall TCP **7777**; bind public (Javis tự bắt buộc đăng nhập).
5. Mở `http://IP:7777`.

Chi tiết: [CAI-DAT-MAY-CA-NHAN.md](CAI-DAT-MAY-CA-NHAN.md).

---

## 4. Hostinger mà chưa mua domain (cách C)

Không cần mua tên miền riêng:

1. hPanel → Docker Manager → Compose → URL:

```text
https://raw.githubusercontent.com/duongcanhquan/javisOS/main/docker-compose.hostinger.yml
```

2. Environment:

| Biến | Giá trị |
|---|---|
| `DOMAIN_NAME` | `javis.<hostname-vps>.hstgr.cloud` (hostname xem ở hPanel → VPS) |
| `JAVIS_ADMIN_USER` | `admin` |
| `JAVIS_ADMIN_PASSWORD` | mật khẩu mạnh |

3. Deploy → mở `https://javis.…hstgr.cloud` (HTTPS + mic).

Chưa đặt `DOMAIN_NAME` vẫn vào được tạm bằng `http://IP:7777`.

---

## 5. Chỉ mình dùng từ laptop (cách D - SSH tunnel)

Không mở 7777 ra internet:

```bash
ssh -L 7777:localhost:7777 root@IP_VPS
```

Giữ cửa sổ SSH mở → trên laptop mở `http://localhost:7777`.  
Mic hoạt động (localhost). An toàn hơn cách A nếu bạn quên đặt mật khẩu.

---

## 6. Checklist sau khi vào app

1. Tạo / đăng nhập **admin** (mật khẩu mạnh trên VPS public).
2. **Models** → gắn ít nhất một bộ não.
3. Chat thử một câu (agent/workflow chuẩn đã sync sẵn).
4. Cần mic → bật tunnel (B) hoặc subdomain Hostinger (C).
5. **Kết nối** (Gmail, Zalo…) → tự gắn khi cần; không có sẵn trong image.

---

## 7. Lỗi thường gặp (không domain)

| Hiện tượng | Cách xử lý |
|---|---|
| Trình duyệt không vào được IP:7777 | Firewall VPS / security group chưa mở 7777; `docker compose ps` xem container có Up không |
| Hỏi MÃ THIẾT LẬP | `docker compose exec javis cat /data/state/.setup_token` |
| Pull image fail | Package GHCR `javisos` chưa Public, hoặc hết dung lượng đĩa |
| Mic bị chặn trên IP | Bình thường với HTTP+IP → dùng tunnel hoặc subdomain Hostinger |
| Tunnel không ra URL | `docker compose --profile tunnel up -d` rồi `logs tunnel`; đợi ~30s |
| Windows: Docker chưa sẵn sàng | Mở Docker Desktop, đợi xanh, chạy lại `docker compose up -d` |

---

## 8. Sau này có mua domain

1. Trỏ DNS **A** của `javis.tencuaban.com` → IP VPS.
2. Linux tự quản: thêm `docker-compose.https.yml` (Caddy) + **Cài đặt → Tên miền & SSL** trong app.  
3. Hostinger: đặt `DOMAIN_NAME=javis.tencuaban.com` rồi Redeploy.

Chi tiết: [docs/15-thuong-hieu-ten-mien.md](docs/15-thuong-hieu-ten-mien.md).

---

*Image mặc định: `ghcr.io/duongcanhquan/javisos:latest`. Không gửi kèm thư mục `brains/` cá nhân khi hướng dẫn người khác.*
