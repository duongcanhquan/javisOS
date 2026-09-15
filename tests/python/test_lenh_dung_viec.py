"""Bảo dừng việc ngầm thì dừng thật, không giao việc mới để đi dừng.

    python tests/run.py lenh_dung_viec
"""
from _paths import ROOT  # noqa: E402,F401
import os
import re

from lenh_dung_viec import cau_tra_loi, la_lenh_dung_viec  # noqa: E402

_fails = []


def check(name, cond, extra=None):
    print(("ok   " if cond else "FAIL ") + name + ("" if cond or extra is None else f"  [{extra}]"))
    if not cond:
        _fails.append(name)


LENH = [
    "tạm dừng cái việc tìm kiếm ngầm đi nhé",
    "tắt việc tìm kiếm đang chạy",
    "dừng việc nền", "huỷ tác vụ đang chạy", "thôi bỏ việc ngầm đi",
    "ngừng chạy nền", "stop the background task", "cancel background work",
]
KHONG_PHAI = [
    "dừng việc nhập liệu lại",
    "việc nền chạy tới đâu rồi",
    "cho anh xem việc nền",
    "dừng lại", "thôi",
    "tìm giúp anh tin tức hôm nay",
    "tạo việc nền mới",
]
for c in LENH:
    check("nhận là lệnh dừng: " + c, la_lenh_dung_viec(c) is True)
for c in KHONG_PHAI:
    check("KHÔNG nhận nhầm: " + c, la_lenh_dung_viec(c) is False)
check("câu rỗng không phải lệnh",
      la_lenh_dung_viec("") is False and la_lenh_dung_viec(None) is False)

check("không có việc thì nói thật", cau_tra_loi(0) == "Không có việc nền nào đang chạy.")
check("một việc", cau_tra_loi(1) == "Đã dừng việc đang chạy.")
check("nhiều việc", "2" in cau_tra_loi(2))

main_src = open(os.path.join(ROOT, "server", "main.py"), encoding="utf-8").read()
check("lưới 1 dashboard: nhận lệnh thì huỷ ngay, không hỏi model",
      re.search(r"if lenh_dung_viec\.la_lenh_dung_viec\(user_message\):[\s\S]{0,400}"
                r"lenh_dung_viec\.thu_huy\(brain\)", main_src) is not None)
check("lưới 1 telegram: cùng chốt",
      re.search(r"if lenh_dung_viec\.la_lenh_dung_viec\(text\):[\s\S]{0,200}"
                r"lenh_dung_viec\.thu_huy\(brain\)", main_src) is not None)

pl = open(os.path.join(ROOT, "system", "plugins", "javis-task", "plugin.py"),
          encoding="utf-8").read()
check("lưới 2: model vẫn cố giao việc để dừng thì cũng chặn",
      re.search(r"if la_lenh_dung_viec\(tieu_de\) or la_lenh_dung_viec\(intent\):[\s\S]{0,400}"
                r"huy_viec_dang_chay", pl) is not None)

cl = open(os.path.join(ROOT, "CLAUDE.md"), encoding="utf-8").read()
check("lưới 3: system prompt cấm giao việc để đi dừng",
      "Stopping a background job is a COMMAND" in cl)

tk = open(os.path.join(ROOT, "server", "tasks.py"), encoding="utf-8").read()
check("tasks có hàm huỷ việc đang chạy", "def huy_viec_dang_chay(" in tk)

print(("\n%d FAIL" % len(_fails)) if _fails else "\nTat ca OK")
raise SystemExit(1 if _fails else 0)
