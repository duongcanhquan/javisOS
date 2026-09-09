# Cài Javis trên máy local (Windows / Mac)

Dành cho laptop / PC cá nhân. Mở bằng trình duyệt tại **http://localhost:7777**.  
Không cần tên miền. Mic / giọng nói hoạt động bình thường trên localhost.

VPS không domain: [HUONG-DAN-CAI-VPS-KHONG-TEN-MIEN.md](HUONG-DAN-CAI-VPS-KHONG-TEN-MIEN.md).  
Bản rút gọn double-click: [CAI-DAT-MAY-CA-NHAN.md](CAI-DAT-MAY-CA-NHAN.md).

---

## 0. Cấu hình máy tối thiểu

| | Tối thiểu | Khuyến nghị |
|---|---|---|
| **CPU** | 4 nhân hiện đại | Apple Silicon M1+ hoặc Intel/AMD gần đây |
| **RAM** | **8 GB** (chỉ cloud/API) | **16 GB** (thoải mái; Ollama local cần hơn) |
| **Ổ** | 5 GB trống cho Javis | 20 GB+ nếu tải model Ollama |
| **OS** | Windows 10/11, macOS 12+ | Windows 11, macOS 14+ |
| **Trình duyệt** | Chrome hoặc Edge | Chrome |

Ghi chú:

- Chạy Javis local **không cần GPU**.
- Dùng Claude / ChatGPT / OpenRouter / API: máy yếu vẫn ổn (model chạy trên cloud).
- Muốn **Ollama Local**: xem mục 5 - thường cần **16 GB+ RAM** (model 7B–8B); máy 8 GB chỉ nên model rất nhỏ và sẽ chậm.

---

## 1. Windows - từng bước

### 1.1 Cài sẵn (một lần)

1. **Python 3.11+** từ [python.org](https://www.python.org/downloads/)  
   Khi cài: **tick** *Add python.exe to PATH*.
2. **Node.js 22 LTS** từ [nodejs.org](https://nodejs.org/) (khuyến nghị - Claude Code / Codex / một số kết nối).

### 1.2 Lấy Javis

1. Mở https://github.com/duongcanhquan/javisOS  
2. **Code → Download ZIP** → giải nén, ví dụ `D:\Javis`.

### 1.3 Cài lần đầu

1. Mở thư mục vừa giải nén.
2. Double-click **`1-Cai-dat.bat`** (lần đầu vài phút).
3. Thấy `http://localhost:7777` là xong.
4. Chrome / Edge → **http://localhost:7777** → tạo tài khoản admin (máy nhà có thể bỏ trống mật khẩu nếu chỉ mình dùng; vẫn nên đặt).

### 1.4 Mỗi ngày

| Việc | File |
|---|---|
| Bật | `2-Bat-Javis.bat` hoặc `JAVIS OS.bat` |
| Tắt | `3-Tat-Javis.bat` |
| Tự chạy khi đăng nhập Windows | `javis-autostart.bat install` |

---

## 2. Mac - từng bước

### 2.1 Cài sẵn (một lần)

1. Terminal:

```bash
xcode-select --install
```

2. Python 3 từ [python.org/macos](https://www.python.org/downloads/macos/) hoặc `brew install python`.
3. (Khuyến nghị) Node.js 22 LTS.

### 2.2 Lấy Javis

Download ZIP từ GitHub → giải nén, ví dụ `~/Desktop/Javis`.

### 2.3 Cài lần đầu

1. Chuột phải **`1-Cai-dat.command`** → **Open** (macOS có thể hỏi nhà phát triển).
2. Đợi xong → mở **http://localhost:7777**.

Nếu báo không xác định được nhà phát triển: **System Settings → Privacy & Security → Open Anyway**.

### 2.4 Mỗi ngày

| Việc | File |
|---|---|
| Bật | `2-Bat-Javis.command` hoặc `JAVIS OS.app` |
| Tắt | `3-Tat-Javis.command` |
| Tự chạy khi đăng nhập | `./bin/javis-autostart.sh install` |

Trong Terminal nếu `.command` không chạy:

```bash
cd ~/Desktop/Javis   # đúng thư mục của bạn
chmod +x *.command
```

---

## 3. Sau khi vào app (Windows & Mac giống nhau)

1. **Models** → chọn **một** bộ não (bắt buộc):

| Đường | Khi nào hợp |
|---|---|
| **Claude Code** | Có Claude Pro/Max - đăng nhập link + code |
| **ChatGPT (Codex)** | Có ChatGPT Plus/Pro |
| **Antigravity CLI** | Có gói Google / Antigravity |
| **OpenRouter / API** | Chỉ muốn dán key, nhanh |
| **Ollama (Local)** | Muốn chạy model trên máy - xem mục 5 |

2. Chat thử tại **http://localhost:7777**.  
   Agent / workflow / skill chuẩn **đã có sẵn** (không bắt buộc Studio).
3. **Kết nối** (Gmail, Zalo…) → tự gắn khi cần.

**Local vs VPS:** trên máy nhà bạn dùng `localhost` - không cần domain, mic hoạt động. Không mở cổng 7777 ra internet trừ khi bạn cố ý.

---

## 4. Ollama trên máy local - tiện không? Nhanh hơn không?

### Trả lời ngắn

- **Tiện** ở chỗ: miễn phí sau khi tải model, dùng offline, dữ liệu không gửi cloud (nếu không đấu kết nối ngoài).
- **Không tự động nhanh hơn** cloud / Claude / ChatGPT / OpenRouter. Trên laptop CPU hoặc RAM thấp, Ollama thường **chậm hơn rõ** và model nhỏ hơn.
- Local **không bắt buộc** Ollama. Đa số người cài Javis trên Mac/Windows nên dùng subscription hoặc API trước; Ollama là **tuỳ chọn** khi máy đủ mạnh hoặc cần offline.

### Khi nào nên dùng Ollama Local

- Máy **16 GB RAM+** (Apple Silicon M1/M2/M3 hoặc PC có GPU ổn).
- Cần offline / không muốn trả API.
- Việc nền nhẹ, chấp nhận model 7B–14B.

### Khi nào không nên ưu tiên Ollama

- Máy **8 GB RAM** hoặc chỉ CPU yếu.
- Cần chất lượng gần Claude / GPT cho viết proposal, nghiên cứu sâu.
- Muốn “cài xong là nhanh” ngay - hãy chọn Claude / ChatGPT / OpenRouter trước.

### Cách bật (tóm tắt)

1. Cài Ollama từ https://ollama.com (app Mac/Windows).
2. Kéo một model chat (ví dụ `ollama pull qwen2.5:7b` hoặc model Javis gợi ý trên trang Models).
3. Trong Javis: **Models → tab Local / Ollama (Local)** → Kết nối (thường `http://127.0.0.1:11434`) → chọn model chính hoặc model việc nền.
4. Chi tiết đầy đủ: [docs/10-models-va-engine.md](docs/10-models-va-engine.md).

> Ollama Cloud (key tại ollama.com) khác Ollama Local: cloud chạy trên máy chủ Ollama, không cần GPU máy bạn.

---

## 5. So sánh nhanh: local máy nhà vs VPS

| | Máy local | VPS |
|---|---|---|
| Link | `http://localhost:7777` | `http://IP:7777` hoặc HTTPS/tunnel |
| Domain | Không cần | Không bắt buộc (xem hướng dẫn VPS) |
| Mic | Có trên localhost | Cần HTTPS (tunnel / domain) |
| Ollama | Hợp nếu máy mạnh | Thường chậm nếu VPS không GPU - ưu tiên API/cloud |
| Ai dùng | Một người trên máy đó | Mở từ xa / nhiều thiết bị |

---

## 6. Lỗi thường gặp

| Hiện tượng | Cách xử lý |
|---|---|
| Windows: Python không nhận | Cài lại, tick Add to PATH, mở lại CMD, chạy `1-Cai-dat.bat` |
| Cổng 7777 bị chiếm | `3-Tat-Javis` rồi `2-Bat` lại |
| Chat lỗi sau khi mở app | Models chưa đăng nhập / thiếu key |
| Mac không mở `.command` | Chuột phải → Open; `chmod +x *.command` |
| Ollama “chưa kết nối” | App Ollama đang chạy? Địa chỉ `11434`? |
| Ollama rất chậm | Model quá lớn so với RAM; hạ model hoặc dùng OpenRouter/Claude |

---

## 7. Cập nhật bản mới

Tải ZIP mới từ GitHub → giải nén đè thư mục cũ (hoặc folder mới) → chạy lại `1-Cai-dat` một lần nếu script bảo cần.

---

*Image / ZIP: repo `duongcanhquan/javisOS`. Không gửi kèm `brains/` cá nhân khi phát hành cho người khác.*
