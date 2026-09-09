# Bộ tài liệu hướng dẫn Javis (máy cá nhân)

| File | Dùng để |
|---|---|
| [HUONG-DAN-CAI-DAT-VA-SU-DUNG.md](../../HUONG-DAN-CAI-DAT-VA-SU-DUNG.md) | **Sau đóng gói:** Windows/Mac + VPS Linux/Windows + domain + Studio + Kết nối |
| [HUONG-DAN-CAI-MAY-LOCAL.md](../../HUONG-DAN-CAI-MAY-LOCAL.md) | **Máy local Windows/Mac:** cài từng bước, cấu hình tối thiểu, Ollama tùy chọn |
| [HUONG-DAN-CAI-VPS-KHONG-TEN-MIEN.md](../../HUONG-DAN-CAI-VPS-KHONG-TEN-MIEN.md) | **VPS mới chưa có domain:** IP:7777, tunnel HTTPS, Hostinger miễn phí, cấu hình tối thiểu |
| [CAI-DAT-MAY-CA-NHAN.md](../../CAI-DAT-MAY-CA-NHAN.md) | Cài đặt Windows/Mac (double-click) |
| [CAI-DAT-TRUONG.md](../../CAI-DAT-TRUONG.md) | Gói phát cho trường |
| [HUONG-DAN-SU-DUNG.html](HUONG-DAN-SU-DUNG.html) | Hướng dẫn dùng (mở bằng trình duyệt) |
| [HUONG-DAN-SU-DUNG-Javis-OS.pdf](HUONG-DAN-SU-DUNG-Javis-OS.pdf) | Bản PDF gửi người mới |

In lại PDF từ HTML (nếu sửa nội dung):

```bash
cd docs/huong-dan
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --disable-gpu --no-pdf-header-footer \
  --print-to-pdf=HUONG-DAN-SU-DUNG-Javis-OS.pdf \
  "file://$PWD/HUONG-DAN-SU-DUNG.html"
```
