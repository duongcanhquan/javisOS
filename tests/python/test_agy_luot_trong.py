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
check("dashboard xoá mạch khi mach_khoi_phuc",
      "mach_khoi_phuc" in main_py and "clear_agy_conversation_id" in main_py)


print()
if _fails:
    print(f"THẤT BẠI {len(_fails)}: {_fails}")
    raise SystemExit(1)
print("OK - test_agy_luot_trong")
