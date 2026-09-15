"""Tin trạng thái Telegram: gửi im lặng, không đè tool, chốt gọn. Chạy:

    python tests/python/test_tin_trang_thai_telegram.py

0.55.238: bỏ dòng vết liệt kê shell/tool (trước đây thành tin kiểu
`⚙ /bin/sh -lc "rg …" · 1m16s`). Progress tool không còn sửa tin trạng thái.
"""
from _paths import ROOT, SERVER  # noqa: E402,F401
import asyncio
import sys

from bot_gateway import RE_TEN_TOOL, dong_vet_gon
from telegram_bot import TelegramBot

loi = []


def check(ten, dieu_kien, them=""):
    print(("ok   " if dieu_kien else "FAIL ") + ten + (("  [" + repr(them) + "]") if them and not dieu_kien else ""))
    if not dieu_kien:
        loi.append(ten)


# ---- 1. Bóc tên công cụ (helper vẫn đúng; bot chủ không còn hiện lên chat) ----

MAU_CO_TOOL = [
    ("⚙ Đang gọi: pos_statistics", "pos_statistics"),
    ("⚙ Đang gọi công cụ: Read", "Read"),
    ("⚙ Đang dùng công cụ: mcp__pancake-pos__pos_order",
     "mcp__pancake-pos__pos_order"),
    ("⚙ Đang gọi: `Write`", "Write"),
]
for chuoi, mong in MAU_CO_TOOL:
    m = RE_TEN_TOOL.match(chuoi)
    got = m.group(1).strip().strip("`").strip() if m else None
    check(f"bóc tên tool: {chuoi[:28]}", got == mong, got)

for chuoi in ("✓ Nhận kết quả - đang phân tích…", "✍ Đang soạn câu trả lời…", "⏳ Đang xử lý…"):
    check(f"KHÔNG bóc nhầm: {chuoi[:26]}", RE_TEN_TOOL.match(chuoi) is None)


# ---- 2. Dòng vết gọn + helper cũ vẫn có ----

bot_tron = TelegramBot.__new__(TelegramBot)
check("dong_vet_gon chỉ thời gian",
      dong_vet_gon(3.2) == "✓ Đã xong · 3s", dong_vet_gon(3.2))
check("dong_vet_gon trên 1 phút",
      dong_vet_gon(76) == "✓ Đã xong · 1m16s", dong_vet_gon(76))
check("_dong_vet_gon qua bot",
      bot_tron._dong_vet_gon(8.7) == "✓ Đã xong · 9s", bot_tron._dong_vet_gon(8.7))
check("helper cũ không tool vẫn nói trả lời trực tiếp",
      bot_tron._dong_vet([], 3.2) == "✓ Trả lời trực tiếp · 3s", bot_tron._dong_vet([], 3.2))


# ---- 3. Chạy trọn một lượt với client HTTP giả ----

class FakeResp:
    def __init__(self, data):
        self._d, self.status_code, self.content = data, 200, b"{}"
        self.text = str(data)

    def json(self):
        return self._d


class FakeClient:
    def __init__(self):
        self.calls = []
        self._mid = 100

    async def post(self, url, json=None, data=None, files=None):
        method = url.rsplit("/", 1)[-1]
        self.calls.append((method, json or data or {}))
        if method == "sendMessage":
            self._mid += 1
            return FakeResp({"ok": True, "result": {"message_id": self._mid}})
        return FakeResp({"ok": True, "result": {}})

    def goi(self, method):
        return [p for m, p in self.calls if m == method]


def chay_luot(answer_fn, giau_trang_thai=False):
    bot = TelegramBot.__new__(TelegramBot)
    bot.token, bot.chat_ids, bot.giau_trang_thai = "t", ["7"], giau_trang_thai
    bot.answer_fn = answer_fn
    c = FakeClient()
    asyncio.run(bot._handle_turn(c, "7", "doanh thu tuần này?"))
    return c


async def _answer_hai_tool(text, meta, progress):
    await progress("⚙ Đang gọi: pos_statistics")
    await progress("⚙ Đang gọi: Read")
    await progress("⚙ Đang gọi: /bin/sh -lc \"rg --files /brains\"")
    await progress("✍ Đang soạn câu trả lời…")
    return {"text": "Doanh thu 12,4 triệu, tăng 8%."}


c = chay_luot(_answer_hai_tool)

check("KHÔNG còn gọi deleteMessage", not c.goi("deleteMessage"),
      [m for m, _ in c.calls])

gui = c.goi("sendMessage")
check("tin trạng thái gửi IM LẶNG", bool(gui) and gui[0].get("disable_notification") is True,
      gui[0] if gui else None)
check("tin trạng thái mở đầu bằng 'đang thực hiện yêu cầu'",
      bool(gui) and "đang thực hiện yêu cầu" in (gui[0].get("text") or "").lower(),
      gui[0] if gui else None)

check("câu trả lời là tin MỚI, không phải sửa tin cũ", len(gui) == 2, len(gui))
check("tin cuối cùng chính là câu trả lời",
      len(gui) == 2 and "12,4 triệu" in (gui[-1].get("text") or ""), gui[-1] if len(gui) > 1 else None)
check("câu trả lời KHÔNG bị tắt chuông",
      len(gui) == 2 and not gui[-1].get("disable_notification"), gui[-1] if len(gui) > 1 else None)

sua = c.goi("editMessageText")
check("có sửa tin trạng thái (chốt xong)", len(sua) >= 1, len(sua))
vet = (sua[-1].get("text") or "") if sua else ""
check("lần sửa CUỐI là dòng gọn ✓ Đã xong", vet.startswith("✓ Đã xong"), vet)
check("KHÔNG lộ tên tool/shell trong dòng chốt",
      "pos_statistics" not in vet and "Read" not in vet and "/bin/sh" not in vet
      and "Đang gọi" not in vet and "Đang đọc" not in vet, vet)
# Progress tool không được sửa tin thành "⏳ ⚙ …"
check("không sửa tin trạng thái bằng dòng tool giữa lượt",
      all("Đang gọi" not in (p.get("text") or "") and "Đang đọc" not in (p.get("text") or "")
          for p in sua[:-1] or []),
      sua)


# ---- 4. /stop ----

async def _answer_bi_cat(text, meta, progress):
    await progress("⚙ Đang gọi: pos_order")
    raise asyncio.CancelledError()


c2 = chay_luot(_answer_bi_cat)
check("/stop cũng KHÔNG xoá tin", not c2.goi("deleteMessage"), [m for m, _ in c2.calls])
sua2 = c2.goi("editMessageText")
check("/stop → tin trạng thái đổi thành 'Đã dừng'",
      bool(sua2) and "Đã dừng" in (sua2[-1].get("text") or ""), sua2[-1] if sua2 else None)
check("/stop → KHÔNG gửi thêm câu trả lời nào", len(c2.goi("sendMessage")) == 1,
      len(c2.goi("sendMessage")))


# ---- 5. Bot chuyên trách ----

async def _answer_khach(text, meta, progress):
    await progress("⚙ Đang gọi: pos_product")
    return {"text": "Dạ bên em còn hàng ạ."}


c3 = chay_luot(_answer_khach, giau_trang_thai=True)
check("chế độ người thật: không tin trạng thái, chỉ 1 tin trả lời",
      len(c3.goi("sendMessage")) == 1, len(c3.goi("sendMessage")))
check("chế độ người thật: không sửa tin nào", not c3.goi("editMessageText"),
      c3.goi("editMessageText"))
check("chế độ người thật: có giữ chấm 'đang nhập'", len(c3.goi("sendChatAction")) >= 1,
      len(c3.goi("sendChatAction")))


# ---- 6. Prompt kênh yêu cầu trả lời ngắn, không tường thuật tool ----
cc = (ROOT / "server" / "channel_context.py").read_text(encoding="utf-8")
check("prompt Telegram cấm tường thuật từng bước tool",
      "CHỈ gửi câu trả lời CUỐI" in cc and "TUYỆT ĐỐI không tường thuật" in cc)
check("prompt Zalo cũng cấm tường thuật tool",
      cc.count("CHỈ gửi câu trả lời CUỐI") >= 2)
check("prompt Telegram vẫn cho Bash curl send-file (không cấm tool)",
      "Vẫn ĐƯỢC" in cc and "Bash curl" in cc and "chat_id" in cc)
check("prompt Telegram cấm paste lệnh vào tin nhắn",
      "không paste lệnh shell/curl" in cc)


print()
if loi:
    print(f"{len(loi)} test ĐỎ: " + ", ".join(loi))
    sys.exit(1)
print("Tất cả test xanh.")
