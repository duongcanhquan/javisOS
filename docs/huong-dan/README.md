# Bộ tài liệu hướng dẫn Javis (máy cá nhân)

| File | Dùng để |
|---|---|
| [CAI-DAT-MAY-CA-NHAN.md](../../CAI-DAT-MAY-CA-NHAN.md) | Cài đặt Windows/Mac (double-click) |
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
