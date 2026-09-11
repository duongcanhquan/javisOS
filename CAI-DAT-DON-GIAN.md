# Cài Javis - cách đơn giản nhất

Chỉ làm **4 bước**. Không cần Docker, không cần Git, không cần GPU.

---

## Bạn dùng máy nào?

| Máy | Làm theo |
|---|---|
| Laptop / PC **Windows** | [Windows](#windows-4-bước) |
| Laptop / PC **Mac** | [Mac](#mac-4-bước) |
| **VPS Linux** (chạy 24/7) | [VPS](#vps-linux-3-lệnh) |

Chi tiết đầy đủ (Node, ffmpeg, firewall…): [CHUAN-BI-TRUOC-KHI-CAI.md](docs/huong-dan/CHUAN-BI-TRUOC-KHI-CAI.md).

---

## Windows (4 bước)

### 1) Cài Python (một lần)
1. Mở https://www.python.org/downloads/
2. Cài bản **3.11** hoặc **3.12**
3. **Nhớ tick** ô *Add python.exe to PATH*
4. Mở **cmd mới**, gõ:

```text
python --version
```

Thấy `Python 3.11…` hoặc `3.12…` là được.

### 2) Tải Javis
1. Mở link GitHub do admin gửi
2. **Code → Download ZIP**
3. Giải nén ra ví dụ `D:\Javis`

### 3) Chạy cài
1. Mở thư mục vừa giải nén
2. Double-click **`1-Cai-dat.bat`** (lần đầu vài phút)
3. Thấy dòng `http://localhost:7777` là xong

### 4) Mở dùng
1. Chrome / Edge → **http://localhost:7777**
2. Tạo tài khoản admin
3. Vào **Models** → chọn Claude / ChatGPT / API → chat thử

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
GitHub → **Code → Download ZIP** → giải nén (ví dụ `~/Desktop/Javis`).

### 3) Chạy cài
Chuột phải **`1-Cai-dat.command`** → **Open** (lần đầu macOS có thể hỏi - chọn Open).

### 4) Mở dùng
Safari / Chrome → **http://localhost:7777** → admin → **Models** → chat.

**Ngày sau:** double-click `2-Bat-Javis.command`.

> Mac chặn file? **System Settings → Privacy & Security → Open Anyway**.

---

## VPS Linux (3 lệnh)

Chỉ cần SSH vào VPS (Ubuntu khuyến nghị). Không cài Python trên máy chủ.

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker "$USER"
# Đăng xuất SSH, vào lại, rồi:
mkdir -p ~/javis && cd ~/javis
curl -fsSLO https://raw.githubusercontent.com/duongcanhquan/javisOS/main/docker-compose.yml
docker compose up -d
```

Mở trình duyệt: **http://IP-VPS:7777**  
Nhớ mở cổng **7777** trên firewall nhà cung cấp.

---

## Xong rồi làm gì?

1. **Models** → chọn 1 bộ não (Claude / ChatGPT / OpenRouter…)
2. Chat thử một câu
3. (Tuỳ chọn) Kết nối Gmail / Zalo sau

---

## Lỗi hay gặp (ngắn)

| Hiện tượng | Làm gì |
|---|---|
| `python` không nhận | Cài lại Python, tick PATH, **mở cmd mới** |
| Cổng 7777 bị chiếm | Chạy `3-Tat-Javis` rồi `2-Bat-Javis` |
| Mac không mở `.command` | Chuột phải → Open |
| VPS không vào được | Mở firewall TCP 7777; `docker compose ps` |

Hướng dẫn dài hơn: [CAI-DAT-MAY-CA-NHAN.md](CAI-DAT-MAY-CA-NHAN.md) · [HUONG-DAN-CAI-DAT-VA-SU-DUNG.md](HUONG-DAN-CAI-DAT-VA-SU-DUNG.md).
