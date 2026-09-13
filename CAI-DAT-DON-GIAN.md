# Cài Javis - cách đơn giản nhất

Chỉ làm **4 bước**. Không cần Docker, không cần Git, không cần GPU.

> **Sau khi cài bạn có gì?** Dashboard web tại cổng **7777**, chat UI, Second Brain, skills/agents hệ thống.  
> **Chưa có sẵn:** bộ não AI. Bắt buộc vào **Models** chọn Claude / ChatGPT / Antigravity / API key rồi mới chat được.  
> **Antigravity (`agy`) không tự cài** khi chạy `1-Cai-dat` - cài tay theo thẻ Models nếu muốn dùng gói Google.

---

## Bạn dùng máy nào?

| Máy | Làm theo |
|---|---|
| Laptop / PC **Windows** | [Windows](#windows-4-bước) |
| Laptop / PC **Mac** | [Mac](#mac-4-bước) |
| **VPS Linux** (chạy 24/7) | [VPS Linux](#vps-linux-docker) |
| **VPS / máy chủ Windows** | [VPS Windows](#vps-windows) |

Chi tiết đầy đủ (Node, ffmpeg, firewall…): [CHUAN-BI-TRUOC-KHI-CAI.md](docs/huong-dan/CHUAN-BI-TRUOC-KHI-CAI.md).

### Tên file cần nhớ (máy cá nhân)

| Việc | Windows | Mac |
|---|---|---|
| Cài lần đầu | **`1-Cai-dat.bat`** (gọi nội bộ `setup.bat`) | **`1-Cai-dat.command`** |
| Bật ngày sau | **`2-Bat-Javis.bat`** | **`2-Bat-Javis.command`** |
| Tắt | **`3-Tat-Javis.bat`** | **`3-Tat-Javis.command`** |

> Đừng lẫn với `setup.bat` / `start-javis.bat`: đó là file kỹ thuật bên trong. Người dùng cuối chỉ cần bộ **1 / 2 / 3** ở trên.

---

## Windows (4 bước)

### 1) Cài Python (một lần)
1. Mở https://www.python.org/downloads/
2. Cài bản **3.11** hoặc **3.12**
3. **Nhớ tick** ô *Add python.exe to PATH*
4. **Không** cài bản Microsoft Store (gõ `python` mà hiện cửa hàng là sai)
5. Mở **cmd mới**, gõ:

```text
python --version
```

Thấy `Python 3.11…` hoặc `3.12…` là được. Nếu không: thử `py -3.12 --version`.

### 2) Tải Javis
1. Mở link GitHub do admin gửi
2. **Code → Download ZIP**
3. Giải nén ra ví dụ `D:\Javis` (**không** để trong Desktop OneDrive)

### 3) Chạy cài
1. Mở thư mục vừa giải nén
2. Double-click **`1-Cai-dat.bat`** (lần đầu vài phút)
3. Windows báo *đã bảo vệ máy tính*? **More info → Run anyway**
4. Thấy dòng `http://localhost:7777` là xong

### 4) Mở dùng
1. Chrome / Edge → **http://localhost:7777**
2. Tạo tài khoản admin
3. Vào **Models** → chọn Claude / ChatGPT / Antigravity / API → chat thử

**Ngày sau:** double-click `2-Bat-Javis.bat` rồi mở lại `http://localhost:7777`.

---

## Mac (4 bước)

### 1) Công cụ Apple + Python (một lần)
Mở **Terminal**, chạy:

```bash
xcode-select --install
```

Rồi cài Python 3 từ https://www.python.org/downloads/macos/  
(hoặc `brew install python` nếu đã có Homebrew).

Kiểm tra:

```bash
python3 --version
```

### 2) Tải Javis
GitHub → **Code → Download ZIP** → giải nén ra **`~/Javis`** (không để trên Desktop iCloud: pip hay hỏng `_musllinux`).

### 3) Chạy cài

Finder hay chặn file `.command` tải từ ZIP ("Apple không thể xác minh"). **Cách dễ: kéo file vào Terminal.**

1. Mở **Terminal**
2. Gõ `bash ` (có **dấu cách** sau bash)
3. Kéo file **`1-Cai-dat.command`** từ Finder **thả vào** cửa sổ Terminal
4. Enter

Hoặc dán 4 dòng (đổi `~/Javis` đúng folder của bạn):

```bash
cd ~/Javis
xattr -c *.command
chmod +x *.command
bash ./1-Cai-dat.command
```

Cách khác: chuột phải file → **Open**, hoặc **System Settings → Privacy & Security → Open Anyway**.

### 4) Mở dùng
Safari / Chrome → **http://localhost:7777** → admin → **Models** → chat.

**Ngày sau:** double-click `2-Bat-Javis.command` (sau lần Terminal ở trên thì không còn bị chặn).

---

## VPS Linux (Docker)

**Khuyến nghị: Docker** (mở được từ IP). Không cài Python trên máy chủ.

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker "$USER"
# Dang xuat SSH, vao lai, roi:
mkdir -p ~/javis && cd ~/javis
curl -fsSLO https://raw.githubusercontent.com/duongcanhquan/javisOS/main/docker-compose.yml
printf 'JAVIS_ADMIN_USER=admin\nJAVIS_ADMIN_PASSWORD=DoiMatKhauManh\n' > .env
docker compose up -d
```

Đổi `DoiMatKhauManh` trước khi chạy. Thiếu `.env` thì phải đọc **MÃ THIẾT LẬP** trong `docker compose logs javis`.

Mở trình duyệt: **http://IP-VPS:7777**  
Firewall nhà cung cấp: mở TCP **7777** (và **22**).

**Hostinger Docker Manager:** không dùng 3 lệnh trên. Dán URL  
`https://raw.githubusercontent.com/duongcanhquan/javisOS/main/docker-compose.hostinger.yml`  
rồi điền `DOMAIN_NAME` + mật khẩu admin. Chi tiết: [CAI-DAT-TRUONG.md](CAI-DAT-TRUONG.md).

> **Không dùng Docker?** `./install.sh` mặc định chỉ lắng nghe **`127.0.0.1`**. Muốn vào từ máy khác: Docker / SSH tunnel / Cloudflare Tunnel. Chi tiết: [DEPLOY.md](DEPLOY.md).

---

## VPS Windows

Chọn **một** đường.

### Docker Desktop (khuyến nghị)

RDP vào máy chủ. Cài Docker Desktop (bật WSL2 nếu hỏi), đợi icon xanh. PowerShell:

```powershell
mkdir $HOME\javis; cd $HOME\javis
Invoke-WebRequest -Uri https://raw.githubusercontent.com/duongcanhquan/javisOS/main/docker-compose.yml -OutFile docker-compose.yml
@"
JAVIS_ADMIN_USER=admin
JAVIS_ADMIN_PASSWORD=DoiMatKhauManh
"@ | Set-Content -Encoding ascii .env
docker compose up -d
```

Windows Firewall: inbound TCP **7777**. Mở **http://IP-MAY:7777**.

### Native (không Docker)

Giống máy Windows nhà, nhưng máy chạy 24/7. Sau `1-Cai-dat.bat`, sửa `.env`:

```text
JAVIS_HOST=0.0.0.0
JAVIS_ADMIN_USER=admin
JAVIS_ADMIN_PASSWORD=DoiMatKhauManh
```

Rồi `2-Bat-Javis.bat` (hoặc `javis-autostart.bat install`). Mở firewall 7777. Javis tự bắt buộc đăng nhập khi bind public.

---

## Xong rồi làm gì?

1. **Models** → chọn 1 bộ não:
   - Claude Code / ChatGPT-Codex (nếu đã có Node khi chạy `1-Cai-dat`)
   - **Antigravity (`agy`)** - cài tay theo thẻ Models (gói Google cá nhân)
   - OpenRouter / API key khác
2. Chat thử một câu
3. (Tuỳ chọn) Kết nối Gmail / Zalo sau

---

## Lỗi hay gặp (ngắn)

| Hiện tượng | Làm gì |
|---|---|
| `python` không nhận / mở Microsoft Store | Cài python.org, tick PATH, **không** bản Store; mở cmd mới; hoặc `py -3.12` |
| Windows: SmartScreen chặn `.bat` | **More info → Run anyway** |
| `_musllinux` / `No module named yaml` | Cài **chưa xong**. Xoá thư mục `.venv`, copy cả folder ra `~/Javis` (Mac) hoặc `D:\Javis` (Win) - **không** để trên Desktop iCloud/OneDrive - rồi chạy lại `1-Cai-dat` |
| Cổng 7777 bị chiếm | Chạy `3-Tat-Javis` rồi `2-Bat-Javis` |
| Mac: Apple không thể xác minh `.command` | Mở Terminal, gõ `bash ` (có dấu cách), **kéo file `1-Cai-dat.command` thả vào**, Enter |
| VPS không vào được | Firewall TCP 7777; `docker compose ps`; native Windows cần `JAVIS_HOST=0.0.0.0` trong `.env` |
| VPS hỏi MÃ THIẾT LẬP | Thiếu mật khẩu trong `.env` - xem `docker compose logs javis` hoặc điền `JAVIS_ADMIN_PASSWORD` rồi `up` lại |
| Chat lỗi dù mở được app | Chưa chọn bộ não ở **Models** |
| Muốn Google / Antigravity | `agy` **không** nằm trong `1-Cai-dat` - cài theo thẻ Models |

Hướng dẫn dài hơn: [CAI-DAT-MAY-CA-NHAN.md](CAI-DAT-MAY-CA-NHAN.md) · [HUONG-DAN-CAI-DAT-VA-SU-DUNG.md](HUONG-DAN-CAI-DAT-VA-SU-DUNG.md).
