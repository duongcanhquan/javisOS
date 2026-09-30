"""Lệnh hệ thống dùng chung khung chat web và Telegram.

Bốn lệnh Telegram mới (/usage /tasks /memory /plan) nhường cho skill nếu não đang mở
có skill trùng tên. Lệnh phiên cũ không đi qua đây.
"""
from __future__ import annotations

LENH_MOI = ("usage", "tasks", "memory", "plan")


def skill_thang(cmd: str, slugs) -> bool:
    """True khi phải gọi skill, không chạy lệnh hệ thống cùng tên."""
    c = str(cmd or "").lower()
    if c not in LENH_MOI:
        return False
    co = {str(s or "").lower() for s in (slugs or []) if str(s or "").strip()}
    return c in co


def khoi_chi_dan(kind: str, dk: str = "", vong: int = 1, toi_da: int = 8) -> str:
    """Khối chỉ dẫn đặt trước câu người dùng. /plan không làm ra ngoài. /goal tự vòng."""
    if kind == "plan":
        return (
            "[CHỈ LẬP KẾ HOẠCH. Chưa làm gì ra ngoài: không gửi tin, không chi tiền, "
            "không sửa file, không tạo việc. Nêu các bước và rủi ro.]\n\n"
        )
    if kind == "goal":
        return (
            f"[MỤC TIÊU: {dk}\n"
            f"Đây là vòng {int(vong)}/{int(toi_da)}. Làm tiếp phần còn thiếu trong mục tiêu. "
            "Không lan sang việc khác.\n"
            "Kết thúc câu trả lời bằng đúng một dòng:\n"
            '<!-- JAVIS_GOAL: {"done": false, "left": "phần còn lại, để trống nếu đã xong"} -->\n'
            "done là true khi mục tiêu đã đạt, false khi còn việc.]\n\n"
        )
    return ""
