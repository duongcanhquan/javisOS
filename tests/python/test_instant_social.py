"""Trả lời xã giao tức thì - không gọi model."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))

import instant_social as S  # noqa: E402


def check(name, cond, detail=""):
    if cond:
        print(f"ok   {name}")
    else:
        print(f"FAIL {name}  [{detail}]")
        raise SystemExit(1)


check("xin chào", "Javis" in (S.try_reply("xin chào", "Javis") or ""))
check("Xin chào!", "Javis" in (S.try_reply("Xin chào!", "Javis") or ""))
check("hello", S.try_reply("hello", "Javis") is not None)
check("hi", S.try_reply("hi", "Javis") is not None)
check("cảm ơn", "giúp" in (S.try_reply("cảm ơn", "Javis") or ""))
check("thanks", S.try_reply("thanks", "Javis") is not None)

check("không nuốt câu có việc", S.try_reply("xin chào, hôm nay doanh thu bao nhiêu?", "Javis") is None)
check("không nuốt câu hỏi", S.try_reply("chào bạn, bạn làm được gì?", "Javis") is None)
check("rỗng", S.try_reply("", "Javis") is None)
check("dài", S.try_reply("xin chào " + ("a" * 80), "Javis") is None)
_tg = (ROOT / "server" / "main.py").read_text(encoding="utf-8")
_khoi = _tg.split("không spawn Antigravity/CLI.", 1)[1].split("async def _p", 1)[0]
check("Telegram nhận câu chào ở khóa text",
      '{"text": _social, "files": []}' in _khoi and '{"reply": _social' not in _khoi)

print("\nOK - test_instant_social")
