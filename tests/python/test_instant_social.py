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


check("xin chào", "LYON" in (S.try_reply("xin chào", "LYON") or ""))
check("Xin chào!", "LYON" in (S.try_reply("Xin chào!", "LYON") or ""))
check("hello", S.try_reply("hello", "LYON") is not None)
check("hi", S.try_reply("hi", "LYON") is not None)
check("cảm ơn", "giúp" in (S.try_reply("cảm ơn", "LYON") or ""))
check("thanks", S.try_reply("thanks", "LYON") is not None)

check("không nuốt câu có việc", S.try_reply("xin chào, hôm nay doanh thu bao nhiêu?", "LYON") is None)
check("không nuốt câu hỏi", S.try_reply("chào bạn, bạn làm được gì?", "LYON") is None)
check("rỗng", S.try_reply("", "LYON") is None)
check("dài", S.try_reply("xin chào " + ("a" * 80), "LYON") is None)

print("\nOK - test_instant_social")
