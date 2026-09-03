# Cài Javis trên máy cá nhân (Windows / Mac)

Dành cho người **không cần biết lập trình**, không cần Cursor.
Mỗi người một bản trên máy mình. Mở bằng trình duyệt Chrome/Edge.

---

## Trước khi bắt đầu (1 lần)

### Windows
1. Cài **Python 3.11+**: https://www.python.org/downloads/  
   Khi cài nhớ **tick ô “Add python.exe to PATH”**.
2. (Khuyến nghị) Cài **Node.js 22 LTS**: https://nodejs.org/  
   Để dùng Claude Code / ChatGPT trong trang Models.

### Mac
1. Mở **Terminal**, dán lệnh này rồi Enter (cài Homebrew nếu chưa có):

```bash
xcode-select --install
```

2. Nếu máy chưa có Python 3, cài từ https://www.python.org/downloads/macos/  
   hoặc: `brew install python` (khi đã có Homebrew).

---

## Bước 1 - Lấy Javis về máy

1. Vào repo GitHub (link do nhà trường / admin gửi).
2. Bấm nút xanh **Code** → **Download ZIP**.
3. Giải nén ra thư mục dễ nhớ, ví dụ:
   - Windows: `D:\Javis`
   - Mac: `~/Desktop/Javis`

---

## Bước 2 - Cài lần đầu

### Windows
1. Mở thư mục vừa giải nén.
2. Double-click **`1-Cai-dat.bat`** (lần đầu hơi lâu: tải thư viện).
3. Thấy dòng `http://localhost:7777` là xong.
4. Mở Chrome → vào **http://localhost:7777**

Các lần sau: double-click **`2-Bat-Javis.bat`** (chạy nền, không cần cửa sổ đen).  
Tắt: double-click **`3-Tat-Javis.bat`**.

### Mac
1. Mở thư mục vừa giải nén.
2. Lần đầu: chuột phải **`1-Cai-dat.command`** → **Open** (macOS có thể hỏi xác nhận).
3. Đợi chạy xong → Chrome mở **http://localhost:7777** (hoặc tự mở).

Các lần sau: double-click **`2-Bat-Javis.command`**.  
Tắt: **`3-Tat-Javis.command`**.

> Nếu Mac báo “không mở được vì không xác định được nhà phát triển”:  
> **System Settings → Privacy & Security → Open Anyway**, rồi chạy lại.

---

## Bước 3 - Chọn “bộ não” AI (bắt buộc 1 lần)

Trong app: trang **Models**

Chọn **một** trong các cách dễ:

| Cách | Ai hợp | Việc cần làm |
|---|---|---|
| **Antigravity CLI** | Có gói Google / Antigravity | Cài `agy` theo hướng dẫn trên thẻ, đăng nhập 1 lần |
| **Claude Code** | Có Claude Pro/Max | Đăng nhập trên thẻ Claude |
| **OpenRouter** | Muốn nhanh, chỉ dán key | Tạo key tại openrouter.ai → dán vào |

Xong là chat được ngay trên web.

---

## Mỗi ngày dùng thế nào?

1. Bật Javis (`2-Bat-Javis...`)
2. Mở **http://localhost:7777**
3. Chat / làm việc
4. Tắt khi xong (`3-Tat-Javis...`) - không bắt buộc nếu muốn để chạy nền

---

## Lỗi thường gặp

| Hiện tượng | Cách xử lý |
|---|---|
| Windows: “Python chưa cài” | Cài Python, tick Add to PATH, **mở lại** cửa sổ rồi chạy `1-Cai-dat.bat` |
| Cổng 7777 bị chiếm | Chạy `3-Tat-Javis` rồi `2-Bat-Javis` lại |
| Mở được app nhưng chat lỗi | Vào **Models**, kiểm tra đã đăng nhập / dán key chưa |
| Mac không chạy được `.command` | Chuột phải → Open; hoặc trong Terminal: `chmod +x *.command` rồi double-click lại |
| Muốn cập nhật bản mới | Tải ZIP mới từ GitHub, giải nén đè thư mục cũ (hoặc folder mới), chạy lại `1-Cai-dat` |

---

## Ghi chú cho người phát hành (admin trường)

- Gửi link repo + file hướng dẫn này là đủ.
- Kèm bản PDF dùng: `docs/huong-dan/HUONG-DAN-SU-DUNG-Javis-OS.pdf`.
- Không cần dạy Git / Cursor.
- Mỗi máy = 1 brain riêng trên ổ cứng người đó (không chung dữ liệu trừ khi họ tự bật sao lưu GitHub).
- Khuyến nghị chuẩn bị sẵn **1 slide / PDF 1 trang**: tải ZIP → double-click cài → mở trình duyệt → Models.
