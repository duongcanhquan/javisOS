"""Nhãn chip «Đang gọi…» cho người đọc, không phải tên tool nội bộ của CLI.

Ca 15/09: sau khi Antigravity phát `step_type: tool` thành tool_call (để output tool
không lọt vào câu trả lời), khung chat hiện «Đang gọi: view-file» / «Đang gọi: run-command».
Đó là Javis đang đọc file / chạy lệnh, nhưng tên kebab-case trông như lỗi.

Tool MCP (pos_*, javis_*) vẫn hiện tên vì đó là nguồn dữ liệu người dùng nhận ra.
"""
from __future__ import annotations

# khoá đã chuẩn hoá: chữ thường, gạch dưới thành gạch ngang
_NHAN = {
    "view-file": "Đang đọc file",
    "viewfile": "Đang đọc file",
    "read-file": "Đang đọc file",
    "read-file-content": "Đang đọc file",
    "read": "Đang đọc file",
    "read-many-files": "Đang đọc file",
    "cat": "Đang đọc file",
    "run-command": "Đang chạy lệnh",
    "execute-command": "Đang chạy lệnh",
    "bash": "Đang chạy lệnh",
    "shell": "Đang chạy lệnh",
    "terminal": "Đang chạy lệnh",
    "local-shell": "Đang chạy lệnh",
    "grep": "Đang tìm trong file",
    "grep-search": "Đang tìm trong file",
    "search-file-content": "Đang tìm trong file",
    "glob": "Đang xem thư mục",
    "glob-search": "Đang xem thư mục",
    "list-dir": "Đang xem thư mục",
    "list-directory": "Đang xem thư mục",
    "ls": "Đang xem thư mục",
    "write-file": "Đang ghi file",
    "replace": "Đang sửa file",
    "edit": "Đang sửa file",
    "edit-file": "Đang sửa file",
    "web-search": "Đang tìm trên web",
    "web-fetch": "Đang mở trang web",
    "fetch": "Đang mở trang web",
}


def _khoa(ten: str) -> str:
    s = (ten or "").strip().lower().replace("_", "-").replace(" ", "-")
    return s


def nhan(ten: str) -> str:
    """Câu tiếng Việt nếu là tool native; rỗng nếu nên hiện tên gốc."""
    k = _khoa(ten)
    if not k:
        return ""
    if k in _NHAN:
        return _NHAN[k]
    # mcp__server__tool → không map
    return ""


def dong_dang_goi(ten: str) -> str:
    """Dòng chip / Telegram. Native → câu tiếng Việt, không kèm tên kebab."""
    goc = (ten or "").strip()
    cau = nhan(goc)
    if cau:
        return "⚙ " + cau
    if not goc:
        return "⚙ Đang làm…"
    return f"⚙ Đang gọi: {goc}"
