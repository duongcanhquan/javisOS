"""Cài máy cá nhân Mac/Windows không được mở app khi pip/venv hỏng.

    python tests/run.py cai_dat_local     (KHÔNG mạng)

Người dùng báo (2026-09-13) trên Mac giải nén ZIP `javisOS-main`:

  [2/3] Cai thu vien...
  ImportError: cannot import name '_musllinux' from 'pip._vendor.packaging'
  ...
  Javis dang chay tai: http://localhost:7777
  ModuleNotFoundError: No module named 'yaml'

Hai lỗi cùng một lần cài: pip trong `.venv` đã vo, script vẫn `exec python main.py`.
`1-Cai-dat.command` cũ gọi `pip` sau `source activate`, không kiểm mã lỗi, không tạo lại
venv hỏng, và dùng `python3` hệ thống (macOS hay 3.9). `setup.bat` cùng kiểu trên Windows.
`install.sh` còn `pip install --upgrade pip` - hay chính là thứ làm vỡ vendor packaging.

KHÔNG chạy pip thật, KHÔNG tạo venv. Chỉ đọc script + bash -n.
"""
from _paths import ROOT  # noqa: E402
import re
import subprocess
import sys

_fails = []


def check(name, cond, them=""):
    print(("ok   " if cond else "FAIL ") + name + (("  [" + str(them) + "]" if them and not cond else "")))
    if not cond:
        _fails.append(name)


MAC = (ROOT / "1-Cai-dat.command").read_text(encoding="utf-8")
WIN = (ROOT / "setup.bat").read_text(encoding="utf-8")
INS = (ROOT / "install.sh").read_text(encoding="utf-8")
HELP = (ROOT / "scripts" / "ensure-venv.sh").read_text(encoding="utf-8")
BAT2 = (ROOT / "start-javis.bat").read_text(encoding="utf-8")
CMD2 = (ROOT / "2-Bat-Javis.command").read_text(encoding="utf-8")
CMD3 = (ROOT / "3-Tat-Javis.command").read_text(encoding="utf-8")
MO = (ROOT / "scripts" / "mo-khoa-mac.sh").read_text(encoding="utf-8")
DOC = (ROOT / "CAI-DAT-DON-GIAN.md").read_text(encoding="utf-8")
UPD = (ROOT / "update.sh").read_text(encoding="utf-8")


# ---- cú pháp ----
check("1-Cai-dat.command còn chạy được (bash -n)",
      subprocess.run(["bash", "-n", str(ROOT / "1-Cai-dat.command")]).returncode == 0)
check("scripts/ensure-venv.sh còn chạy được (bash -n)",
      subprocess.run(["bash", "-n", str(ROOT / "scripts" / "ensure-venv.sh")]).returncode == 0)
check("install.sh còn chạy được (bash -n)",
      subprocess.run(["bash", "-n", str(ROOT / "install.sh")]).returncode == 0)
check("2-Bat-Javis.command còn chạy được (bash -n)",
      subprocess.run(["bash", "-n", str(ROOT / "2-Bat-Javis.command")]).returncode == 0)
check("update.sh còn chạy được (bash -n)",
      subprocess.run(["bash", "-n", str(ROOT / "update.sh")]).returncode == 0)

# ---- Mac: không gọi pip trần, không mở app khi pip chết ----
check("Mac nạp helper ensure-venv (không nhét logic pip vào 1 file click)",
      "scripts/ensure-venv.sh" in MAC)
check("CANARY: Mac cài gói bằng python -m pip, không gọi binary pip",
      "-m pip install -r requirements.txt" in HELP)
check("CANARY: helper KHÔNG gọi binary pip (đúng lỗi _musllinux của pip vo)",
      "bin/pip install" not in HELP
      and not re.search(r"(?m)^\s*pip install -r", HELP))
check("CANARY: 1-Cai-dat.command không còn `pip install -r` trần",
      not re.search(r"(?m)^\s*pip install -r", MAC))
check("CANARY: Mac không in 'Javis dang chay' nếu cai thu vien thất bại",
      "Cai dat CHUA XONG" in MAC and MAC.find("javis_cai_thu_vien") < MAC.find("Javis dang chay"))
check("CANARY: Mac kiểm import yaml trước khi coi là xong",
      "import yaml" in HELP)
check("CANARY: Mac xoá .venv khi pip hỏng rồi tạo lại",
      "rm -rf .venv" in HELP and "javis_pip_ok" in HELP)
check("helper nói rõ _musllinux và yaml cho người đọc lỗi",
      "_musllinux" in HELP and "yaml" in HELP)
check("Mac chọn Python >= 3.10, không tin mỗi `python3` (macOS hay 3.9)",
      "javis_find_python" in MAC and "3.10" in HELP)
check("Mac chạy server bằng python của .venv, không `python` hệ thống",
      ".venv/bin/python main.py" in MAC or "../.venv/bin/python main.py" in MAC)

# ---- Windows ----
check("CANARY: Windows cài gói bằng python -m pip, không `pip install` sau activate",
      '-m pip install -r requirements.txt' in WIN
      and not re.search(r"(?m)^\s*pip install -r", WIN))
check("CANARY: Windows dừng nếu pip install lỗi (không mở app)",
      "THAT BAI" in WIN or "that bai" in WIN.lower())
idx_pip = WIN.lower().find("-m pip install -r requirements.txt")
check("Windows kiểm errorlevel ngay sau pip install",
      idx_pip >= 0 and "if errorlevel 1" in WIN[idx_pip:idx_pip + 500].lower())
check("CANARY: Windows kiểm import yaml trước khi mở app",
      "import yaml" in WIN)
check("Windows xoá .venv khi pip hỏng",
      "rmdir /s /q .venv" in WIN and "-m pip --version" in WIN)
check("Windows nói _musllinux trong hướng dẫn sửa",
      "_musllinux" in WIN)
check("Windows chạy server bằng python của .venv",
      "%VPY%" in WIN and "main.py" in WIN)
check("Windows từ chối Python < 3.10",
      "sys.version_info[:2]>=" in WIN and "(3, 10)" in WIN or "(3,10)" in WIN)
check("Windows chối python Microsoft Store (WindowsApps)",
      "windowsapps" in WIN.lower())
check("Windows thử py -3.12 nếu lệnh python hỏng",
      "py -3.12" in WIN)
check("Windows copy env.example thành .env nếu chưa có",
      "copy /Y env.example .env" in WIN or "copy /y env.example .env" in WIN.lower())
check("Windows Unblock-File file .bat (SmartScreen ZIP)",
      "Unblock-File" in WIN)

# ---- install.sh / update.sh (VPS native + Mac install.sh) ----
check("CANARY: install.sh KHÔNG còn lệnh pip install --upgrade pip",
      not any("pip install --upgrade pip" in ln and not ln.lstrip().startswith("#")
              for ln in INS.splitlines()))
check("install.sh cài gói bằng python -m pip",
      ".venv/bin/python -m pip install -r requirements.txt" in INS)
check("install.sh kiểm yaml sau pip",
      'import yaml, fastapi' in INS)
check("install.sh tạo lại .venv khi pip vo",
      "_musllinux" in INS and "rm -rf .venv" in INS)
check("update.sh không nuốt lỗi pip bằng || true",
      not re.search(r"pip install -r requirements\.txt[^\n]*\|\| true", UPD))
check("update.sh dùng python -m pip",
      ".venv/bin/python -m pip install -r requirements.txt" in UPD)

# ---- bật ngày sau không mở app khi yaml thiếu ----
check("2-Bat-Javis.command từ chối khi thiếu yaml",
      "import yaml" in CMD2 and "1-Cai-dat.command" in CMD2)
check("start-javis.bat từ chối khi thiếu yaml",
      "import yaml" in BAT2 and "1-Cai-dat.bat" in BAT2)

# ---- hướng dẫn người dùng ----
check("CAI-DAT-DON-GIAN có hàng _musllinux / yaml",
      "_musllinux" in DOC and "yaml" in DOC)
check("hướng dẫn bảo copy ra ~/Javis, không Desktop iCloud",
      "~/Javis" in DOC)

# ---- Gatekeeper: ZIP chưa ký, cài qua Terminal ----
check("scripts/mo-khoa-mac.sh gỡ tem bằng xattr -c",
      "xattr -c" in MO)
check("1/2/3 .command đều nạp mo-khoa-mac (lan Terminal go tem cho lan bam sau)",
      "scripts/mo-khoa-mac.sh" in MAC
      and "scripts/mo-khoa-mac.sh" in CMD2
      and "scripts/mo-khoa-mac.sh" in CMD3)
check("CAI-DAT-DON-GIAN day Terminal bash ./1-Cai-dat.command (tranh Gatekeeper)",
      "bash ./1-Cai-dat.command" in DOC and "xattr -c" in DOC)
check("CAI-DAT-DON-GIAN ghi cach keo file .command vao Terminal",
      "kéo file" in DOC.lower() or "Kéo file" in DOC)
check("CAI-DAT-DON-GIAN có mục VPS Windows",
      "VPS Windows" in DOC and "JAVIS_HOST=0.0.0.0" in DOC)
check("CAI-DAT-DON-GIAN VPS Linux ghi mật khẩu admin vào .env trước up",
      "JAVIS_ADMIN_PASSWORD" in DOC)
check("CAI-DAT-DON-GIAN nhắc Hostinger dùng compose riêng",
      "docker-compose.hostinger.yml" in DOC)
check("mo-khoa-mac.sh source được (bash -n)",
      subprocess.run(["bash", "-n", str(ROOT / "scripts" / "mo-khoa-mac.sh")]).returncode == 0)


if _fails:
    print(f"\nFAIL {len(_fails)}: " + "; ".join(_fails))
    sys.exit(1)
print("\nOK - test_cai_dat_local: tất cả pass")
