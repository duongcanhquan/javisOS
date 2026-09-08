#!/usr/bin/env python3
"""Antigravity: tự phục hồi khi 'Agent execution terminated' / thoát mã 1 rỗng.

    python tests/run.py agy_agent_terminated

Không cần mạng, không cần cài agy thật. Mô phỏng binary thoát mã 1 lần đầu rồi OK.
"""
from __future__ import annotations

import asyncio
import json
import os
import stat
import tempfile
from pathlib import Path

from _paths import ROOT, SERVER  # noqa: F401

os.environ.setdefault("JAVIS_STATE_DIR", tempfile.mkdtemp(prefix="javis-agy-cut-"))

import antigravity_cli as A  # noqa: E402
import sessions as _sess  # noqa: E402

_fails = []


def check(name, cond, them=""):
    print(("ok   " if cond else "FAIL ") + name
          + (("  [" + str(them) + "]") if them and not cond else ""))
    if not cond:
        _fails.append(name)


def chay(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


# ---------- nhận diện + câu user ----------
check("nhận Agent execution terminated",
      A._la_loi_agent_cut("⚠ Agent execution terminated due to error."))
check("nhận truncation",
      A._la_loi_agent_cut("could not convert a single message before hitting truncation"))
check("không nhận empty prompt như agent-cut",
      not A._la_loi_agent_cut("Error: empty prompt. Usage: agy --print"))
check("câu user không để nguyên tiếng Anh generic",
      "Antigravity bị cắt" in A._loi_user_agy("Agent execution terminated due to error.")
      or "cắt giữa lượt" in A._loi_user_agy("Agent execution terminated due to error."))
check("thoát mã 1 không stderr → có hướng dẫn",
      "mã 1" in A._loi_user_agy("", ma_exit=1))


# ---------- sessions: cột mạch agy ----------
check("MACH_NATIVE có antigravity-cli",
      _sess.SessionStore._MACH_NATIVE.get("antigravity-cli") == "agy_conversation_id")
_db = Path(tempfile.mkdtemp(prefix="javis-agy-sess-")) / "s.db"
s = _sess.SessionStore(_db)
sid = s.create_session(brain="brain")
s.set_agy_conversation_id(sid, "agy-conv-1")
row = s.get_session(sid) or {}
check("lưu agy_conversation_id", row.get("agy_conversation_id") == "agy-conv-1")
s.clear_agy_conversation_id(sid)
row2 = s.get_session(sid) or {}
check("xoá agy_conversation_id", not (row2.get("agy_conversation_id") or ""))
s.set_agy_conversation_id(sid, "agy-keep")
s.set_grok_session_id(sid, "grok-x")
don = s.clear_native_threads(sid, keep="antigravity-cli")
check("clear_native giữ agy khi keep=antigravity-cli",
      (s.get_session(sid) or {}).get("agy_conversation_id") == "agy-keep")
check("clear_native dọn grok khi keep agy", "grok-cli" in don)


# ---------- fake agy: lần 1 terminated, lần 2 OK khi không còn --conversation ----------
_HELP = ("Usage: agy [OPTIONS]\n  -p, --print <PROMPT>\n  --model <M>\n"
         "  --output-format <F>\n  --conversation <ID>\n  --mcp-config <F>\n"
         "  --add-dir <D>\n  --print-timeout <T>\n")


def _gia_agy_cut_roi_ok():
    """Lần đầu có --conversation → thoát 1 + terminated. Lần sau không conversation → OK."""
    d = Path(tempfile.mkdtemp(prefix="javis-fakeagy-cut-"))
    log = d / "log.txt"
    p = d / "agy"
    p.write_text(
        "#!/usr/bin/env python3\n"
        "import json, sys, pathlib\n"
        f"log = pathlib.Path({str(log)!r})\n"
        "argv = sys.argv[1:]\n"
        "log.write_text(log.read_text() + json.dumps(argv) + '\\n' if log.exists() else json.dumps(argv) + '\\n')\n"
        "if '--help' in argv:\n"
        f"    print({_HELP!r}); sys.exit(0)\n"
        "if 'models' in argv:\n"
        "    print('gemini-3.8-flash-medium'); sys.exit(0)\n"
        "has_conv = '--conversation' in argv\n"
        "n = len(log.read_text().strip().splitlines()) if log.exists() else 0\n"
        "# Đếm mọi lần chạy (kể cả --help). Chỉ fail khi có --conversation.\n"
        "if has_conv:\n"
        "    print(json.dumps({'event':'error','message':'Agent execution terminated due to error.'}))\n"
        "    print('Agent execution terminated due to error.', file=sys.stderr)\n"
        "    sys.exit(1)\n"
        "print(json.dumps({'event':'init','conversation_id':'new-ok','init':{'model':'x'}}))\n"
        "print(json.dumps({'event':'step_update','step_update':{'step_type':'agent_response','text_delta':'Xin chào lại'}}))\n"
        "print(json.dumps({'event':'result','result':{'status':'SUCCESS','response':'Xin chào lại'}}))\n"
        "sys.exit(0)\n",
        encoding="utf-8",
    )
    p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return str(p), log


cli, log = _gia_agy_cut_roi_ok()
os.environ["JAVIS_AGY_BIN"] = cli
os.environ["JAVIS_AGY_PROMPT_DAI"] = "argv"
A._HELP_CACHE.update({"path": None, "text": "", "ts": 0.0})


async def _thu_query():
    g = A.AntigravityCLI(cwd=tempfile.mkdtemp(prefix="agy-cwd-"), model="gemini-3.8-flash-medium")
    g.session_id = "mach-hong-cu"   # ép lần đầu đi --conversation
    g.cli_path = cli
    evs = []
    async for ev in g.query("Xin chào"):
        evs.append(ev)
    return g, evs


g, evs = chay(_thu_query())
finals = [e for e in evs if e.get("type") == "final"]
errors = [e for e in evs if e.get("type") == "error"]
check("sau terminated vẫn có final (không để trống)", bool(finals), str(evs)[:400])
if finals:
    check("final có chữ trả lời sau retry",
          "Xin chào lại" in (finals[-1].get("content") or ""),
          finals[-1].get("content"))
check("không nhân đôi error đỏ khi đã phục hồi",
      len(errors) == 0 or "Xin chào lại" in (finals[-1].get("content") or ""),
      f"errors={len(errors)} finals={len(finals)}")
check("mạch mới sau phục hồi",
      (g.session_id or "") in ("new-ok", None) or g.session_id != "mach-hong-cu",
      g.session_id)


# ---------- dashboard nối mạch ----------
main_py = (ROOT / "server" / "main.py").read_text(encoding="utf-8")
check("dashboard lưu agy_conversation_id",
      "set_agy_conversation_id" in main_py)
check("dashboard nối mạch khi có agy id",
      "agy_conversation_id" in main_py and "_a_mach" in main_py)
check("dashboard không gửi response rỗng",
      'không trả lời được lượt này' in main_py or "Antigravity không trả lời" in main_py)


print()
if _fails:
    print(f"THẤT BẠI {len(_fails)}: {_fails}")
    raise SystemExit(1)
print("OK - test_agy_agent_terminated")
