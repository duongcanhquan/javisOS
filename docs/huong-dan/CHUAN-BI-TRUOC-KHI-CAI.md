# Cài sẵn trên máy trước khi cài Javis

Làm xong mục này **trước** khi chạy `1-Cai-dat` / Docker. Thiếu bước này hay gây lỗi `Python not found`, Docker đỏ, không mở được cổng.

Bản HTML có hình: [HUONG-DAN-CAI-DAT-Javis-OS.html](HUONG-DAN-CAI-DAT-Javis-OS.html) mục 3.

---

## Bảng nhanh

| Nền tảng | Bắt buộc trước | Khuyến nghị | Tuỳ chọn sau |
|---|---|---|---|
| **Windows PC** | Python 3.11+ (tick PATH), Chrome/Edge | Node.js 22 LTS, Git for Windows | ffmpeg, Ollama, Docker Desktop |
| **macOS** | Xcode CLT (`xcode-select --install`), Python 3.11+ | Homebrew, Node.js 22 LTS | ffmpeg, Ollama |
| **VPS Linux** | SSH được, Docker Engine + Compose, mở cổng 22 + 7777 | `apt update && upgrade`, ufw / security group | Domain / tunnel HTTPS (cho mic) |
| **VPS Windows** | RDP/SSH được; Docker Desktop *hoặc* Python+Node; Firewall TCP 7777 | WSL2 (Docker), bật Virtualization trong BIOS | Tunnel HTTPS, domain |

**Không cần GPU** để cài và chat qua Claude / ChatGPT / OpenRouter.

---

## Windows (máy cá nhân)

1. **Python 3.11 hoặc 3.12** - [python.org/downloads/windows](https://www.python.org/downloads/windows/)  
   - Tick **Add python.exe to PATH**.  
   - Nên bật *Disable path length limit*.  
   - Kiểm tra (cmd mới): `python --version`
2. Chrome hoặc Edge mới.
3. **Node.js 22 LTS** - [nodejs.org](https://nodejs.org/) (Claude Code / Codex / một số kết nối).
4. **Git for Windows** nếu clone repo (ZIP thì không bắt buộc).
5. **ffmpeg** (media): `winget install Gyan.FFmpeg`
6. Nếu Windows chặn `.bat`: *More info → Run anyway*.

---

## macOS

1. `xcode-select --install` (bắt buộc lần đầu).
2. Python 3.11+: [python.org/macos](https://www.python.org/downloads/macos/) hoặc `brew install python`.
3. Homebrew (khuyến nghị): [brew.sh](https://brew.sh).
4. Node.js 22 LTS: nodejs.org hoặc `brew install node@22`.
5. Tuỳ chọn: `brew install ffmpeg`.
6. File `.command`: chuột phải → **Open** (Gatekeeper).

---

## VPS Linux (Docker)

1. SSH: `ssh root@IP` (hoặc `ubuntu@IP`).
2. Ubuntu 22.04/24.04 hoặc Debian 12; RAM ≥ 4 GB (khuyến nghị 8 GB).
3. `sudo apt update && sudo apt upgrade -y`
4. Cài Docker (không cần Python/Node trên host):

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker "$USER"
# Đăng xuất SSH rồi vào lại
docker version && docker compose version
```

5. Firewall / Security Group: mở **22** và **7777** (thêm 80/443 nếu HTTPS).
6. Mic từ điện thoại cần HTTPS (domain hoặc tunnel) - `http://IP:7777` chỉ chat chữ ổn định.

---

## VPS / máy chủ Windows

1. RDP (hoặc SSH) vào máy.
2. Bật ảo hóa trong BIOS nếu dùng Docker Desktop + WSL2.
3. Chọn **một** đường:
   - **Docker Desktop** (khuyến nghị): docker.com, đợi engine xanh.
   - **Native**: Python 3.11+ (PATH) + Node.js 22 như máy cá nhân.
4. Windows Firewall: inbound TCP **7777** (và 3389 nếu RDP).

---

## Giải thích từng thành phần

| Thứ | Để làm gì |
|---|---|
| Python | Chạy server Javis khi không dùng Docker |
| Node.js | Claude Code / Codex / một số MCP |
| Git | `git clone` (ZIP thì khỏi) |
| Docker | Chạy Javis trong container trên VPS |
| ffmpeg | Audio/video (cuộc họp, render) |
| Ollama | Model offline - không bắt buộc |

Chi tiết từng bước cài Javis: [HUONG-DAN-CAI-DAT-VA-SU-DUNG.md](../../HUONG-DAN-CAI-DAT-VA-SU-DUNG.md).
