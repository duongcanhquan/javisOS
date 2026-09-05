"""GitHub Copilot CLI (`copilot`) - bộ não subscription, không dán API key.

    python tests/run.py copilot      (KHÔNG mạng, KHÔNG cần cài copilot)

Canh đúng những chỗ dễ sai lặng lẽ:
1. Chỉ truyền cờ mà `copilot --help` khai.
2. Hub MCP ghi type=http + url.
3. Token env được coi là đã đăng nhập.
4. Stream trả final từ JSON/text.
"""
from _paths import ROOT, SERVER  # noqa: E402,F401
import asyncio
import json
import os
import stat
import sys
import tempfile
from pathlib import Path

os.environ["JAVIS_STATE_DIR"] = tempfile.mkdtemp(prefix="javis-copilot-test-")

import copilot_cli  # noqa: E402

_fails = []


def check(name, cond, them=""):
    print(("ok   " if cond else "FAIL ") + name
          + (("  [" + str(them) + "]") if them and not cond else ""))
    if not cond:
        _fails.append(name)


def chay(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


def _reset_cache():
    copilot_cli._HELP_CACHE.update(path=None, text="", ts=0.0)
    copilot_cli._AUTH_CACHE.update(ts=0.0, val=None)


def _gia(help_text="", chat_lines=None, chat_err="", chat_code=0,
         models_out="", auth_out="", auth_err="", auth_code=0):
    d = Path(tempfile.mkdtemp(prefix="javis-fakecopilot-"))
    p = d / "copilot"
    p.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        "a = sys.argv[1:]\n"
        f"if '--help' in a:\n    sys.stdout.write({help_text!r}); sys.exit(0)\n"
        "if len(a) >= 2 and a[0] == 'auth' and a[1] == 'status':\n"
        f"    sys.stdout.write({auth_out!r}); sys.stderr.write({auth_err!r}); "
        f"sys.exit({auth_code})\n"
        "if len(a) >= 2 and a[0] == 'models' and a[1] == 'list':\n"
        f"    sys.stdout.write({models_out!r}); sys.exit(0)\n"
        "data = ''\n"
        "try:\n"
        "    data = sys.stdin.read()\n"
        "except Exception:\n"
        "    data = ''\n"
        f"open({str(d / 'argv.txt')!r}, 'w', encoding='utf-8').write('\\x00'.join(a))\n"
        f"open({str(d / 'stdin.txt')!r}, 'w', encoding='utf-8').write(data)\n"
        f"for line in {json.dumps(chat_lines or [])}:\n"
        "    print(line, flush=True)\n"
        f"sys.stderr.write({chat_err!r})\n"
        f"sys.exit({chat_code})\n",
        encoding="utf-8",
    )
    p.chmod(p.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return str(p), d


_HELP = (
    "Usage: copilot [options]\n"
    "  -p, --prompt <text>\n"
    "  -s, --silent\n"
    "  --no-ask-user\n"
    "  --model <id>\n"
    "  --allow-all-tools\n"
    "  --additional-mcp-config <path>\n"
)


# 1. find binary ưu tiên env
_tmp = Path(tempfile.mkdtemp(prefix="javis-copilot-bin-"))
_bin = _tmp / "copilot"
_bin.write_text("", encoding="utf-8")
os.environ["JAVIS_COPILOT_BIN"] = str(_bin)
_that_tim = copilot_cli.tim_binary
copilot_cli.tim_binary = lambda _n: None
check("find_copilot_cli ưu tiên JAVIS_COPILOT_BIN",
      copilot_cli.find_copilot_cli() == str(_bin))
os.environ.pop("JAVIS_COPILOT_BIN", None)
copilot_cli.tim_binary = _that_tim


# 2. hub entry
_hub = copilot_cli.hub_entry("http://127.0.0.1:7777/mcp", {"Authorization": "Bearer x"})
check("hub_entry type=http + url",
      _hub == {"type": "http", "url": "http://127.0.0.1:7777/mcp",
               "headers": {"Authorization": "Bearer x"}}, _hub)


# 3. ghi MCP + trang thái
_vault = Path(tempfile.mkdtemp(prefix="javis-copilot-vault-"))
_path = copilot_cli.ghi_mcp_settings(str(_vault), _hub)
check("ghi_mcp_settings trả đường file", bool(_path), _path)
_doc = json.loads(Path(_path).read_text(encoding="utf-8"))
check("file MCP có servers.javis", _doc.get("servers", {}).get("javis") == _hub, _doc)
_st = copilot_cli.trang_thai_mcp(str(_vault))
check("trang_thai_mcp ok", _st.get("ok") is True and _st["files"][0]["type"] == "http", _st)


# 4. auth qua token env
_cli, _d = _gia(help_text=_HELP)
_reset_cache()
copilot_cli.find_copilot_cli = lambda: _cli
os.environ["COPILOT_GITHUB_TOKEN"] = "ghu_test"
os.environ.pop("GH_TOKEN", None)
os.environ.pop("GITHUB_TOKEN", None)
_auth = copilot_cli.auth_status(bo_qua_cache=True)
check("auth_status nhận COPILOT_GITHUB_TOKEN",
      _auth.get("connected") is True and "COPILOT_GITHUB_TOKEN" in (_auth.get("method") or ""),
      _auth)
os.environ.pop("COPILOT_GITHUB_TOKEN", None)


# 5. list models JSON
_cli2, _ = _gia(
    help_text=_HELP,
    models_out=json.dumps({"models": [{"id": "gpt-5"}, {"name": "claude-sonnet-4.6"}]}),
)
_reset_cache()
copilot_cli.find_copilot_cli = lambda: _cli2
check("list_models bóc JSON",
      copilot_cli.list_models() == ["gpt-5", "claude-sonnet-4.6"])


# 6. query: probe cờ + final
_lines = [json.dumps({"type": "assistant", "content": "Xin chào từ Copilot."})]
_cli3, _d3 = _gia(help_text=_HELP, chat_lines=_lines)
_reset_cache()
copilot_cli.find_copilot_cli = lambda: _cli3
_g = copilot_cli.CopilotCLI(cwd=str(_d3), model="gpt-5")
_g.cli_path = _cli3
_g.mode = "full"
_g.mcp_config = str(_d3 / "javis-mcp.json")


async def _go_query():
    return [ev async for ev in _g.query("Trả lời ngắn thôi")]


_evs = chay(_go_query())
_argv = (_d3 / "argv.txt").read_text(encoding="utf-8").split("\x00")
check("stream trả final",
      any(e.get("type") == "final" and "Copilot" in (e.get("content") or "") for e in _evs),
      _evs)
check("mode full truyền --allow-all-tools", "--allow-all-tools" in _argv, _argv)
check("truyền --additional-mcp-config=@...",
      ("--additional-mcp-config=@" + _g.mcp_config) in _argv, _argv)
check("truyền -s headless", "-s" in _argv, _argv)
check("truyền --no-ask-user", "--no-ask-user" in _argv, _argv)
check("truyền --model", "--model=gpt-5" in _argv or (
    "--model" in _argv and _argv[_argv.index("--model") + 1] == "gpt-5"), _argv)


# 7. CANARY: bản cũ không có --allow-all-tools thì không truyền
_HELP_CU = "Usage: copilot\n  -p, --prompt\n  -s, --silent\n"
_cli4, _d4 = _gia(help_text=_HELP_CU, chat_lines=_lines)
_reset_cache()
copilot_cli.find_copilot_cli = lambda: _cli4
_g4 = copilot_cli.CopilotCLI(cwd=str(_d4))
_g4.cli_path = _cli4
_g4.mode = "full"


async def _go_query4():
    return [ev async for ev in _g4.query("hi")]


_evs4 = chay(_go_query4())
_argv4 = (_d4 / "argv.txt").read_text(encoding="utf-8").split("\x00")
check("CANARY: bản cũ không truyền --allow-all-tools",
      "--allow-all-tools" not in _argv4 and "--allow-all" not in _argv4, _argv4)
check("bản cũ vẫn trả final",
      any(e.get("type") == "final" for e in _evs4), _evs4)


# 8. PROVIDER_DEFS đã khai
sys.path.insert(0, str(SERVER))
# Không import main (nặng). Chỉ đọc chuỗi.
_main = (SERVER / "main.py").read_text(encoding="utf-8")
check("main.py import copilot_cli", "import copilot_cli" in _main)
check("PROVIDER_DEFS có copilot-cli", '"id": "copilot-cli"' in _main)
check("có endpoint /copilot/check", '@app.post("/copilot/check")' in _main)


print()
if _fails:
    print(f"{len(_fails)} test HỎNG: " + ", ".join(_fails))
    sys.exit(1)
print("Tất cả test copilot_cli đã qua.")
