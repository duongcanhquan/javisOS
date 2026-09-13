"""Hướng dẫn VPS phải đọc được với người chưa biết SSH / RDP / tên miền.

    python tests/run.py huong_dan_vps     (KHÔNG mạng)

Chỉ đọc file Markdown + HTML. Không deploy, không gọi API.
"""
from _paths import ROOT  # noqa: E402

_fails = []


def check(name, cond, them=""):
    print(("ok   " if cond else "FAIL ") + name + (("  [" + str(them) + "]" if them and not cond else "")))
    if not cond:
        _fails.append(name)


VPS = (ROOT / "HUONG-DAN-CAI-VPS-KHONG-TEN-MIEN.md").read_text(encoding="utf-8")
DON = (ROOT / "CAI-DAT-DON-GIAN.md").read_text(encoding="utf-8")
TONG = (ROOT / "HUONG-DAN-CAI-DAT-VA-SU-DUNG.md").read_text(encoding="utf-8")
HTML = (ROOT / "docs" / "huong-dan" / "HUONG-DAN-CAI-DAT-Javis-OS.html").read_text(encoding="utf-8")
CHUAN = (ROOT / "docs" / "huong-dan" / "CHUAN-BI-TRUOC-KHI-CAI.md").read_text(encoding="utf-8")


# ---- file chính: người mới vào được máy chủ ----
check("VPS nêu PowerShell để SSH trên Windows",
      "PowerShell" in VPS and "ssh root@" in VPS)
check("VPS nêu PuTTY khi Windows chưa có ssh",
      "PuTTY" in VPS and "putty.org" in VPS.lower())
check("VPS nói mật khẩu SSH không hiện chữ",
      "không hiện" in VPS.lower() and "password" in VPS.lower())
check("VPS nêu cách dán lệnh (chuột phải / Cmd+V)",
      "chuột phải" in VPS and "Cmd+V" in VPS)
check("VPS Windows dùng Remote Desktop / mstsc",
      "Remote Desktop" in VPS and "mstsc" in VPS)
check("VPS Windows nêu user Administrator",
      "Administrator" in VPS)

# ---- tên miền miễn phí ----
check("VPS hướng dẫn Hostinger hstgr.cloud",
      "hstgr.cloud" in VPS and "DOMAIN_NAME" in VPS)
check("VPS hướng dẫn DuckDNS từng bước",
      "duckdns.org" in VPS.lower() and "duckdns.org" in VPS)
check("VPS DuckDNS gắn compose HTTPS + Bật SSL",
      "docker-compose.https.yml" in VPS and "Bật SSL" in VPS)
check("VPS nêu Cloudflare Tunnel trycloudflare",
      "trycloudflare" in VPS)

# ---- lần đầu đơn giản ----
check("VPS lần đầu chỉ admin + Models, chưa Gmail/Zalo",
      "Models" in VPS and "Đừng cài Gmail" in VPS)
check("VPS ghi mật khẩu admin vào .env trước up",
      "JAVIS_ADMIN_PASSWORD" in VPS)

# ---- bản ngắn + bản tổng + HTML trỏ đúng chỗ ----
check("CAI-DAT-DON-GIAN trỏ người chưa biết SSH sang file VPS",
      "HUONG-DAN-CAI-VPS-KHONG-TEN-MIEN.md" in DON and "PuTTY" in DON)
check("bản tổng có DuckDNS và mục kết nối SSH",
      "DuckDNS" in TONG and "PuTTY" in TONG and "mstsc" in TONG)
check("HTML có mục kết nối SSH/RDP và DuckDNS",
      "PuTTY" in HTML and "DuckDNS" in HTML and "mstsc" in HTML)
check("CHUAN-BI nói PowerShell/PuTTY và RDP",
      "PuTTY" in CHUAN and "mstsc" in CHUAN)


if _fails:
    print(f"\nFAIL {len(_fails)}: " + "; ".join(_fails))
    raise SystemExit(1)
print("\nOK - test_huong_dan_vps: tất cả pass")
