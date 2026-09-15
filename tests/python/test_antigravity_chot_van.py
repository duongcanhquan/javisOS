"""Chữ TRẠNG THÁI của bước chạy nền không được lọt vào câu trả lời gửi ra ngoài.

Sự cố 13/09/2026 (chủ repo báo kèm log): bản tin giá vàng 07:01 gửi sang Telegram mở đầu bằng
"The task has been started in the background. Waiting for results." Không phải lỗi số liệu -
đó là câu chính model tự nói ở bước chờ tác vụ nền, còn vòng đọc sự kiện của `antigravity_cli`
thì cố ý gom RỘNG ("mọi thứ trông như chữ của trợ lý") để không bao giờ trả bong bóng rỗng.
Hai thứ đó cộng lại: câu trạng thái bị nối thẳng vào ĐẦU bản tin.

Trọng tài là `response` trong sự kiện `result` - `agy` mang toàn văn câu trả lời cuối ở đó.
Test này canh đúng một điều: gọt được phần thừa ĐẦU mà không bao giờ tự xén mất phần đuôi.
"""
from _paths import ROOT, SERVER  # noqa: E402,F401
import os
import sys
import tempfile

os.environ.setdefault("JAVIS_STATE_DIR", tempfile.mkdtemp(prefix="javis-agychot-"))

from antigravity_cli import _chot_van, AntigravityCLI  # noqa: E402

_fails = []


def check(ten, dieu_kien):
    print(("  OK   " if dieu_kien else "  HỎNG ") + ten)
    if not dieu_kien:
        _fails.append(ten)


BAN_TIN = "Giá vàng SJC sáng nay 82,1 triệu/lượng, tăng 300 nghìn so với hôm qua."
TRANG_THAI = "The task has been started in the background. Waiting for results."


# ---- gọt phần thừa đứng TRƯỚC ----
check("cắt câu trạng thái nối trước bản tin (đúng ca 13/09)",
      _chot_van(TRANG_THAI + BAN_TIN, BAN_TIN) == BAN_TIN)
check("cắt cả khi có xuống dòng ngăn giữa",
      _chot_van(TRANG_THAI + "\n\n" + BAN_TIN, BAN_TIN) == BAN_TIN)

# ---- KHÔNG được xén nhầm ----
check("gom trùng khít toàn văn thì giữ nguyên", _chot_van(BAN_TIN, BAN_TIN) == BAN_TIN)
check("không có toàn văn thì vẫn gỡ câu chờ task nền (không phải câu trả lời)",
      _chot_van(TRANG_THAI + BAN_TIN, "") == BAN_TIN)
check("chỗ gom rỗng thì trả rỗng, không dựng câu trả lời từ hư không",
      _chot_van("", BAN_TIN) == "")
check("CANARY: toàn văn bị CẮT NGẮN (chuỗi con giữa chừng) thì KHÔNG tin - giữ bản đầy đủ, "
      "thà thừa một dòng lạ còn hơn thiếu một đoạn không ai biết là đã mất",
      _chot_van(BAN_TIN + " Phần đuôi quan trọng.", BAN_TIN) == BAN_TIN + " Phần đuôi quan trọng.")
check("chữ thừa nằm GIỮA thì giữ nguyên (không đủ căn cứ để đoán chỗ cắt)",
      _chot_van("A" + BAN_TIN + "B", BAN_TIN) == "A" + BAN_TIN + "B")


# ---- nối vào vòng đọc sự kiện thật ----
def _gom(cac_su_kien):
    """Chạy đúng đường `_doi_su_kien` của engine rồi chốt văn như `query()` làm."""
    cli = AntigravityCLI(tag="test")
    manh, chan = [], {}
    for ev in cac_su_kien:
        cli._doi_su_kien(ev, manh, chan)
    return _chot_van("".join(manh).strip(), chan.get("toan_van", ""))


check("luồng thật: step_update trạng thái + step_update bản tin + result -> chỉ còn bản tin",
      _gom([
          {"event": "step_update", "step_update": {"step_type": "agent_response",
                                                   "text_delta": TRANG_THAI}},
          {"event": "step_update", "step_update": {"step_type": "agent_response",
                                                   "text_delta": BAN_TIN}},
          {"event": "result", "result": {"status": "SUCCESS", "response": BAN_TIN}},
      ]) == BAN_TIN)

check("luồng thật: lượt ngắn CHỈ có result (không delta nào) vẫn ra chữ",
      _gom([{"event": "result", "result": {"status": "SUCCESS", "response": BAN_TIN}}]) == BAN_TIN)

check("luồng thật: không có result thì giữ nguyên phần đã gom (không mất câu trả lời)",
      _gom([{"event": "step_update", "step_update": {"step_type": "agent_response",
                                                     "text_delta": BAN_TIN}}]) == BAN_TIN)

check("luồng thật: câu trả lời KHÔNG bị hiện hai lần khi result lặp lại toàn văn",
      _gom([
          {"event": "step_update", "step_update": {"step_type": "agent_response",
                                                   "text_delta": BAN_TIN}},
          {"event": "result", "result": {"status": "SUCCESS", "response": BAN_TIN}},
      ]) == BAN_TIN)

check("CANARY: _doi_su_kien gọi được KHÔNG kèm chan (chữ ký cũ vẫn chạy)",
      AntigravityCLI(tag="test")._doi_su_kien(
          {"event": "result", "result": {"status": "SUCCESS", "response": BAN_TIN}}, []) is not None)


# ---- 15/09: khối SYSTEM_MESSAGE (task nền agy) không được hiện ra chat ----
from antigravity_cli import _loc_thong_bao_he_thong  # noqa: E402

MAU_PIP = (
    "The following is a <SYSTEM_MESSAGE> not actually sent by the user. "
    "It is provided by the system as important information to pay attention to.\n\n"
    "<SYSTEM_MESSAGE>\n"
    "[Message] timestamp=2026-09-15T03:07:47Z "
    "sender=b345750c-284d-4b56-864d-37f07be12ad7/task-42 "
    "priority=MESSAGE_PRIORITY_HIGH content=Task id "
    '"b345750c-284d-4b56-864d-37f07be12ad7/task-42" finished with result:\n\n'
    "The command exited with code 0.\nOutput:\n"
    "Package                   Version\n"
    "fastapi                   0.115.0\n"
    "\nLog: file:///home/javis/.gemini/antigravity-cli/brain/x/.system_generated/tasks/task-42.log\n"
    "</SYSTEM_MESSAGE>"
)

check("gỡ khối SYSTEM_MESSAGE, không còn pip list",
      _loc_thong_bao_he_thong(MAU_PIP) == ""
      and "fastapi" not in _loc_thong_bao_he_thong(MAU_PIP)
      and "SYSTEM_MESSAGE" not in _loc_thong_bao_he_thong(MAU_PIP))
check("giữ câu trả lời THẬT đứng sau khối dump",
      _loc_thong_bao_he_thong(MAU_PIP + "\n\nĐã cài xong các gói.") == "Đã cài xong các gói.")
check("khối bị cắt giữa chừng (không có thẻ đóng) cũng gỡ",
      "task-49" not in _loc_thong_bao_he_thong(
          "Chào.\n<SYSTEM_MESSAGE>\n[Message] task-49 fin"))
check("câu thường không bị đụng",
      _loc_thong_bao_he_thong(BAN_TIN) == BAN_TIN)

check("luồng thật: dump SYSTEM_MESSAGE + bản tin + result -> chỉ còn bản tin",
      _gom([
          {"event": "step_update", "step_update": {"step_type": "agent_response",
                                                   "text_delta": MAU_PIP}},
          {"event": "step_update", "step_update": {"step_type": "agent_response",
                                                   "text_delta": BAN_TIN}},
          {"event": "result", "result": {"status": "SUCCESS", "response": BAN_TIN}},
      ]) == BAN_TIN)
check("sự kiện type=message (task xong) không lọt vào câu trả lời",
      _gom([
          {"event": "message", "message": {"content": MAU_PIP}},
          {"event": "result", "result": {"status": "SUCCESS", "response": BAN_TIN}},
      ]) == BAN_TIN)


print()
if _fails:
    print(f"{len(_fails)} test HỎNG: " + ", ".join(_fails))
    sys.exit(1)
print("Tất cả test antigravity _chot_van đã qua.")
