"""Chip «Đang gọi» không lộ tên kebab của CLI (view-file, run-command).

    python tests/run.py nhan_tool
"""
from _paths import ROOT  # noqa: E402,F401
import os

from nhan_tool import dong_dang_goi, nhan  # noqa: E402

_fails = []


def check(name, cond, extra=None):
    print(("ok   " if cond else "FAIL ") + name + ("" if cond or extra is None else f"  [{extra}]"))
    if not cond:
        _fails.append(name)


check("view-file → Đang đọc file, không còn tên kebab",
      dong_dang_goi("view-file") == "⚙ Đang đọc file"
      and "view-file" not in dong_dang_goi("view-file"))
check("view_file / Read cũng ra đọc file",
      nhan("view_file") == "Đang đọc file" and nhan("Read") == "Đang đọc file")
check("run-command → Đang chạy lệnh",
      dong_dang_goi("run-command") == "⚙ Đang chạy lệnh"
      and "run-command" not in dong_dang_goi("run-command"))
check("Bash / shell → chạy lệnh",
      dong_dang_goi("Bash") == "⚙ Đang chạy lệnh")
check("MCP POS vẫn hiện tên",
      dong_dang_goi("pos_statistics") == "⚙ Đang gọi: pos_statistics")
check("javis_task vẫn hiện tên",
      "javis_task" in dong_dang_goi("javis_task"))
check("rỗng không nổ", dong_dang_goi("") == "⚙ Đang làm…")

src = open(os.path.join(ROOT, "server", "main.py"), encoding="utf-8").read()
check("CANARY: main.py không còn ghép tên tool thô vào chip",
      "Đang gọi: {ev.get('name'" not in src
      and "Đang gọi: {event['name']}" not in src
      and "Đang gọi: {nm}" not in src)
check("mọi đường Đang gọi đi qua nhan_tool.dong_dang_goi",
      src.count("nhan_tool.dong_dang_goi") >= 8)

js = open(os.path.join(ROOT, "dashboard", "app.js"), encoding="utf-8").read()
check("dải HUD: view-file thành Đọc file", "view[-_]?file" in js)
check("dải HUD: run-command thành Terminal", "run[-_]?command" in js)
agy = open(os.path.join(ROOT, "server", "antigravity_cli.py"), encoding="utf-8").read()
check("agy vẫn phát tool_call từ bước tool (không nuốt vào câu trả lời)",
      'if _step == "tool":' in agy and '"type": "tool_call"' in agy)

print(("\n%d FAIL" % len(_fails)) if _fails else "\nTat ca OK")
raise SystemExit(1 if _fails else 0)
