"""Lệnh hệ thống mới và Zalo nhóm mặc định tắt.

    python tests/run.py lenh_va_zalo_nhom
"""
from _paths import ROOT, SERVER  # noqa: E402,F401
import os
import sys
import tempfile

os.environ["JAVIS_STATE_DIR"] = tempfile.mkdtemp(prefix="javis-lenh-zalo-")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import chatbot_runtime  # noqa: E402
import chatbot_store  # noqa: E402
import chatbot_tu_dong as td  # noqa: E402
import lenh_he_thong  # noqa: E402

_fails = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        _fails.append(name)


check("skill trùng tên thì skill thắng", lenh_he_thong.skill_thang("usage", ["Usage", "notes"]))
check("không có skill thì lệnh hệ thống chạy", not lenh_he_thong.skill_thang("usage", ["notes"]))
check("lệnh cũ không bị cửa này nuốt", not lenh_he_thong.skill_thang("status", ["status"]))
check("/plan có khối chỉ lập kế hoạch", "CHỈ LẬP KẾ HOẠCH" in lenh_he_thong.khoi_chi_dan("plan"))
check("/goal có trần vòng", "vòng 2/8" in lenh_he_thong.khoi_chi_dan("goal", "xong bài", 2, 8))

src = (SERVER / "main.py").read_text(encoding="utf-8")
i = src.find("if cmd in lenh_he_thong.LENH_MOI")
j = src.find("Hãy dùng skill", i)
check("Telegram hỏi skill trùng tên trước khi chạy lệnh mới",
      i > 0 and j > i and "_tg_co_skill" in src[i:j])

check("tầng 1 nhận câu hỏi", td.nhin_nhu_cau_hoi("Javis báo lỗi cổng 7777 thì làm sao ạ?")[0])
check("tầng 1 bỏ câu trò chuyện", not td.nhin_nhu_cau_hoi("haha đúng rồi cả nhà ơi")[0])
check("auto + không tag thì được đánh giá",
      td.can_danh_gia({"reply_when": "auto"}, {"chat_type": "group", "chat_id": "1"}))
check("mention thì không vào bộ đánh giá",
      not td.can_danh_gia({"reply_when": "mention"}, {"chat_type": "group"}))
check("được tag thì không vào bộ đánh giá",
      not td.can_danh_gia({"reply_when": "auto"},
                          {"chat_type": "group", "mentioned": True}))
td.TRAN_NHOM_GIO = 1
td.KHOANG_CACH_GIAY = 0
td.reset_cho_test()
check("lượt đầu còn hạn mức", td.duoc_tra_loi("b", "g", "u") == "")
td.ghi_da_tra_loi("b", "g", "u")
check("hết hạn mức nhóm", td.duoc_tra_loi("b", "g", "u2") == "het_han_muc")

cfg = {"id": "b", "groups": ["555"], "reply_when": "auto"}
nhom = {"chat_type": "group", "chat_id": "555"}
check("auto + nhóm đã cho phép: cho đi tiếp", chatbot_runtime._ly_do_im(cfg, nhom) == "")
check("auto + nhóm chưa cho phép: vẫn chặn",
      chatbot_runtime._ly_do_im(dict(cfg, groups=[]), nhom) == "nhom_chua_bat")
check("mention + không tag: im",
      chatbot_runtime._ly_do_im(dict(cfg, reply_when="mention"), nhom) == "khong_goi_ten")
check("giá trị reply_when lạ thì im",
      chatbot_runtime._ly_do_im(dict(cfg, reply_when="tu-dong-di"), nhom) == "khong_goi_ten")

bid, loi = chatbot_store.create_bot({
    "name": "Lan", "agent_slug": "lan", "brain": "brain", "muc_quyen": "suggest",
})
check("tạo bot được", bool(bid) and not loi, )
bot = chatbot_store.get_bot(bid)
check("trả lời nhóm Zalo mặc định tắt", bot.get("tra_loi_nhom") is False)
check("reply_when mặc định vẫn là gọi tên", bot.get("reply_when") == "mention")
chatbot_store.update_bot(bid, {"reply_when": "auto", "tra_loi_nhom": "1"})
bot = chatbot_store.get_bot(bid)
check("bật được tự đánh giá và trả lời nhóm",
      bot.get("reply_when") == "auto" and bot.get("tra_loi_nhom") is True)
chatbot_store.update_bot(bid, {"tra_loi_nhom": "0"})
check("tắt trả lời nhóm được", chatbot_store.get_bot(bid).get("tra_loi_nhom") is False)

ev = {"text": "@Javis Vũ cho hỏi", "account_name": "Javis Vũ", "account_id": "z1",
      "metadata": {}}
check("tag đúng tên nick Zalo thì nhận ra",
      chatbot_runtime._nhan_zalo({"name": "Lan", "accounts": []}, ev)[0])
check("tag đúng tên bot trong form vẫn nhận ra",
      chatbot_runtime._nhan_zalo({"name": "Lan"}, {"text": "chào Lan ơi", "account_name": "Javis Vũ"})[0])
check("tag tên khác thì không phải gọi bot",
      not chatbot_runtime._nhan_zalo(
          {"name": "Lan"}, {"text": "@Nam ơi mai họp", "account_name": "Javis Vũ"})[0])
check("reply đúng tên nick thì nhận ra",
      chatbot_runtime._nhan_zalo(
          {"name": "Lan"},
          {"text": "cho hỏi thêm", "account_name": "Javis Vũ",
           "metadata": {"replyTo": {"senderName": "Javis Vũ"}}})[1])
check("reply tên người khác thì không nhận",
      not chatbot_runtime._nhan_zalo(
          {"name": "Lan"},
          {"text": "ok", "account_name": "Javis Vũ",
           "metadata": {"replyTo": {"senderName": "Nam"}}})[1])

print()
if _fails:
    print(f"{len(_fails)} FAIL")
    sys.exit(1)
print("ALL PASS")
