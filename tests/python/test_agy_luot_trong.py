#!/usr/bin/env python3
"""Antigravity: lượt trống (thoát 0, không chữ) khi đang nối mạch thì thử lại mạch mới.

    python tests/run.py agy_luot_trong

Ca thật: chat thường xuyên, agy `--conversation` thoát 0 nhưng stdout rỗng, Javis báo
nhầm "CLI quá cũ mất stdout". Không mạng, không cần binary thật.
"""
from __future__ import annotations

import asyncio
import json
import os
import tempfile
from pathlib import Path

from _paths import ROOT, SERVER  # noqa: F401

os.environ.setdefault("JAVIS_STATE_DIR", tempfile.mkdtemp(prefix="javis-agy-rong-"))

import antigravity_cli as A  # noqa: E402

_fails = []


def check(name, cond, them=""):
    print(("ok   " if cond else "FAIL ") + name
          + (("  [" + str(them) + "]") if them and not cond else ""))
    if not cond:
        _fails.append(name)


def chay(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


_HELP = ("Usage: agy [OPTIONS]\n  -p, --print <PROMPT>\n  --model <M>\n"
         "  --output-format <F>\n  --conversation <ID>\n  --mcp-config <F>\n"
         "  --add-dir <D>\n  --print-timeout <T>\n")


def _gia_agy_rong_roi_ok():
    """Có --conversation → im lặng thoát 0. Không conversation → trả lời."""
    d = Path(tempfile.mkdtemp(prefix="javis-fakeagy-rong-"))
    log = d / "log.txt"
    p = d / "agy"
    p.write_text(
        "#!/usr/bin/env python3\n"
        "import json, sys, pathlib\n"
        f"log = pathlib.Path({str(log)!r})\n"
        "argv = sys.argv[1:]\n"
        "log.write_text((log.read_text() if log.exists() else '') + json.dumps(argv) + '\\n')\n"
        "if '--help' in argv:\n"
        f"    print({_HELP!r}); sys.exit(0)\n"
        "if 'models' in argv:\n"
        "    print('gemini-3.8-flash-medium'); sys.exit(0)\n"
        "if '--conversation' in argv:\n"
        "    sys.exit(0)\n"
        "print(json.dumps({'event':'init','conversation_id':'mach-moi','init':{'model':'x'}}))\n"
        "print(json.dumps({'event':'step_update','step_update':"
        "{'step_type':'agent_response','text_delta':'Đây là câu trả lời'}}))\n"
        "print(json.dumps({'event':'result','result':"
        "{'status':'SUCCESS','response':'Đây là câu trả lời'}}))\n"
        "sys.exit(0)\n",
        encoding="utf-8",
    )
    p.chmod(p.stat().st_mode | 0o755)
    return str(p), log


cli, log = _gia_agy_rong_roi_ok()
os.environ["JAVIS_AGY_BIN"] = cli
os.environ["JAVIS_AGY_PROMPT_DAI"] = "argv"
A._HELP_CACHE.update({"path": None, "text": "", "ts": 0.0})


async def _thu_query(co_mach: bool):
    g = A.AntigravityCLI(cwd=tempfile.mkdtemp(prefix="agy-cwd-"),
                         model="gemini-3.8-flash-medium")
    g.cli_path = cli
    g.prompt_khoi_phuc = "[KHÔI PHỤC NGỮ CẢNH] marker-lich-su-XYZ"
    if co_mach:
        g.session_id = "mach-cu-bi-dut"
    evs = []
    async for ev in g.query("Xin chào"):
        evs.append(ev)
    return g, evs


g, evs = chay(_thu_query(True))
finals = [e for e in evs if e.get("type") == "final"]
errors = [e for e in evs if e.get("type") == "error"]
check("CANARY: mạch cũ + stdout rỗng → vẫn có câu trả lời (không báo CLI quá cũ)",
      bool(finals) and "Đây là câu trả lời" in (finals[-1].get("content") or ""),
      str(evs)[:500])
check("không hiện bong bóng lỗi sau khi phục hồi",
      not errors, errors)
check("đánh dấu mach_khoi_phuc để dashboard bỏ id mạch hỏng",
      g.mach_khoi_phuc is True)
_chat = []
for ln in (log.read_text() if log.exists() else "").splitlines():
    if not ln.strip():
        continue
    argv = json.loads(ln)
    if "--help" in argv or (argv and argv[0] == "models"):
        continue
    _chat.append(argv)
check("lần đầu còn --conversation (nối mạch cũ)",
      any("--conversation" in r for r in _chat), _chat)
check("có lần sau bỏ --conversation (mạch mới)",
      any("--conversation" not in r for r in _chat), _chat)


def _p_arg(argv):
    if "-p" in argv:
        i = argv.index("-p")
        return argv[i + 1] if i + 1 < len(argv) else ""
    return " ".join(argv)


_lan_moi = [r for r in _chat if "--conversation" not in r]
_lan_cu = [r for r in _chat if "--conversation" in r]
check("lần mạch mới mang transcript mồi, không chỉ câu hiện tại",
      any("marker-lich-su-XYZ" in _p_arg(r) for r in _lan_moi), _lan_moi[:2])
check("lần nối mạch không nhồi transcript (tránh Agent terminated)",
      all("marker-lich-su-XYZ" not in _p_arg(r) for r in _lan_cu), _lan_cu[:1])


def _gia_agy_luon_rong():
    d = Path(tempfile.mkdtemp(prefix="javis-fakeagy-im-"))
    p = d / "agy"
    p.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        "if '--help' in sys.argv[1:]:\n"
        f"    print({_HELP!r}); sys.exit(0)\n"
        "sys.exit(0)\n",
        encoding="utf-8",
    )
    p.chmod(p.stat().st_mode | 0o755)
    return str(p)


cli_im = _gia_agy_luon_rong()
A._HELP_CACHE.update({"path": None, "text": "", "ts": 0.0})
os.environ["JAVIS_AGY_BIN"] = cli_im


async def _thu_im():
    g = A.AntigravityCLI(cwd=tempfile.mkdtemp(prefix="agy-cwd-"))
    g.cli_path = cli_im
    return [ev async for ev in g.query("Xin chào")]


evs2 = chay(_thu_im())
check("không mạch + stdout rỗng → vẫn báo lỗi, không im",
      any(e.get("type") == "error" for e in evs2)
      and not any(e.get("type") == "final" for e in evs2), evs2)
check("câu lỗi còn chữ nâng cấp (test_antigravity_cli khoá)",
      any("nâng cấp" in (e.get("content") or "") for e in evs2 if e.get("type") == "error"))
check("câu lỗi không đổ hết cho 'CLI quá cũ'",
      not any("quá cũ" in (e.get("content") or "") for e in evs2))

main_py = (ROOT / "server" / "main.py").read_text(encoding="utf-8")
check("dashboard xoá mạch agy khi xoay mạch / lượt hỏng",
      "clear_agy_conversation_id" in main_py)
check("dashboard gắn prompt_khoi_phuc từ transcript SQLite",
      "prompt_khoi_phuc" in main_py and "bootstrap_prompt" in main_py)
check("dashboard Antigravity lượt sau chỉ gửi câu hiện tại khi đã có mạch",
      "_a_prompt = _a_cur if _a_mach else _a_boot" in main_py)
check("CANARY: dashboard nối --conversation theo đúng phiên (agy_conversation_id)",
      '_a_mach = (_row0.get("agy_conversation_id")' in main_py
      and "set_agy_conversation_id(conv_sid, acli.session_id)" in main_py)
check("dashboard Antigravity mồi lịch sử bằng _tg_lich_su_kho (không cắt cứng [:-1])",
      "_a_raw, _a_tom = _tg_lich_su_kho" in main_py)
check("Telegram Antigravity mồi transcript khi chưa có mạch",
      "_hoi = text if getattr(acli, \"session_id\", None) else _a_boot" in main_py)
check("Telegram Antigravity nối mạch đã lưu của đúng phiên",
      'acli.session_id = (_row_tg.get("agy_conversation_id")' in main_py)
check("đường tắt nhồi lịch sử trước khi gọi model",
      "_fast_path_kem_lich_su" in main_py)

g_sel = A.AntigravityCLI(cwd=tempfile.mkdtemp(prefix="agy-sel-"))
g_sel.prompt_khoi_phuc = "BOOT"
g_sel.session_id = "s1"
check("có mạch + argv → chỉ câu hiện tại", g_sel.phan_user_gui("hi", "argv") == "hi")
check("có mạch + file → transcript mồi (file tắt --conversation)",
      g_sel.phan_user_gui("hi", "file") == "BOOT")
g_sel.session_id = None
check("mất mạch + argv → transcript mồi", g_sel.phan_user_gui("hi", "argv") == "BOOT")


print()
if _fails:
    print(f"THẤT BẠI {len(_fails)}: {_fails}")
    raise SystemExit(1)
print("OK - test_agy_luot_trong")
