"""Regression: provider DeepSeek đấu ĐỦ mọi tầng, không sót chỗ nào.

Cùng checklist 7 chỗ với Groq (PROVIDER_DEFS, config, khoá bí mật, _api_stream,
_api_stream_mcp, aux_engine, KEYFIELD). DeepSeek V4 dùng endpoint OpenAI-compat
nhưng thinking/reasoning_effort khác Groq: tắt phải gửi thinking.disabled, bật
chỉ nhận low|high|max (gửi medium là 400).

Chạy:
    .venv/bin/python tests/python/test_deepseek_provider.py
"""
import asyncio
import json
import os
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

os.environ.setdefault("JAVIS_STATE_DIR", tempfile.mkdtemp(prefix="javis-deepseek-test-"))

from _paths import ROOT, SERVER  # noqa: E402,F401  - nạp server/ vào sys.path

import aux_engine  # noqa: E402
import config as cfgmod  # noqa: E402
import engine  # noqa: E402
import main  # noqa: E402

CONSOLE_JS = (ROOT / "dashboard" / "console.js").read_text(encoding="utf-8")

fails = []


def check(name: str, condition: bool) -> None:
    print(("PASS: " if condition else "FAIL: ") + name)
    if not condition:
        fails.append(name)


# ─────────── 1. Đấu dây: có mặt ở mọi bảng ───────────
_defs = {p["id"]: p for p in main.PROVIDER_DEFS}
check("có trong PROVIDER_DEFS", "deepseek" in _defs)
_d = _defs.get("deepseek") or {}
check("kind=api (đi đường gọi API thẳng)", _d.get("kind") == "api")
check("khai đúng key_field", _d.get("key_field") == "deepseek_api_key")
check("có model mặc định để picker không rỗng khi chưa gọi được mạng",
      len(_d.get("default_models") or []) > 0)

check("config có ô deepseek_api_key", "deepseek_api_key" in cfgmod._DEFAULT["model"])
check("config có catalog deepseek", "deepseek" in cfgmod._DEFAULT["model"]["catalog"])
check("khoá DeepSeek nằm trong danh sách MÃ HOÁ",
      "model.deepseek_api_key" in cfgmod._SECRET_PATHS)

check("aux_engine coi deepseek là provider API", "deepseek" in aux_engine.API_PROVIDERS)
check("aux_engine map được key field",
      aux_engine._KEY_FIELD.get("deepseek") == "deepseek_api_key")

check("giao diện biết ô nhập key nào là của deepseek",
      '"deepseek": "deepseek_api_key"' in CONSOLE_JS)

check("_api_label có tên người đọc được", main._api_label("deepseek") == "DeepSeek")
_cfg = {"model": {}}
main._set_main_model(_cfg, "deepseek", "deepseek-v4-flash")
check("_set_main_model ghi đúng engine + main", _cfg["model"]["engine"] == "deepseek"
      and _cfg["model"]["main"] == {"provider": "deepseek", "model": "deepseek-v4-flash"})


# ─────────── 2. Chạy thật với máy chủ DeepSeek giả lập ───────────
SEEN = []


class _Fake(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        SEEN.append({"auth": self.headers.get("Authorization"), "body": body})
        has_tools = bool(body.get("tools"))
        first = has_tools and not any(m.get("role") == "tool" for m in body["messages"])
        if body.get("stream"):
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            for ch in ("Xin ", "chào ", "từ DeepSeek"):
                self.wfile.write(
                    b"data: " + json.dumps({"choices": [{"delta": {"content": ch}}]}).encode()
                    + b"\n\n")
            self.wfile.write(b"data: [DONE]\n\n")
            return
        msg = ({"role": "assistant", "content": None,
                "tool_calls": [{"id": "c1", "type": "function",
                                "function": {"name": "javis_connections", "arguments": "{}"}}]}
               if first else {"role": "assistant", "content": "Đã gọi tool xong"})
        out = {"choices": [{"message": msg, "finish_reason": "tool_calls" if first else "stop"}],
               "usage": {"prompt_tokens": 10, "completion_tokens": 5}}
        raw = json.dumps(out).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


_srv = HTTPServer(("127.0.0.1", 0), _Fake)
threading.Thread(target=_srv.serve_forever, daemon=True).start()
engine.DEEPSEEK_URL = f"http://127.0.0.1:{_srv.server_address[1]}/chat/completions"

TOOLS = [{"fn": "javis_connections", "server": "javis", "name": "javis_connections",
          "description": "liệt kê nguồn", "schema": {"type": "object", "properties": {}, "required": []}}]


async def _call(_args):
    return "Kết nối: POS, Lịch"


ROUTE = {"javis_connections": {"call": _call}}


async def _run():
    text = ""
    async for ev in engine.deepseek_stream("sk-ds-test", "deepseek-v4-flash",
                                          [{"role": "user", "content": "chào"}], "off"):
        if ev["type"] == "text":
            text += ev["content"]
    check(f"chat thuần stream ra chữ (nhận: {text!r})", text == "Xin chào từ DeepSeek")
    check("tắt suy nghĩ thì gửi thinking.disabled",
          SEEN[0]["body"].get("thinking") == {"type": "disabled"}
          and "reasoning_effort" not in SEEN[0]["body"])

    kinds, called = [], []
    async for ev in engine.deepseek_chat_with_mcp(
            "sk-ds-test", "deepseek-v4-flash",
            [{"role": "user", "content": "có nguồn nào"}],
            "off", TOOLS, ROUTE):
        kinds.append(ev["type"])
        if ev["type"] == "tool_call":
            called.append(ev.get("name"))
    check("vòng tool MCP gọi được tool", called == ["javis_connections"])
    check("và trả về chữ sau khi có kết quả tool", "text" in kinds)

    # medium (thang Javis/OpenAI) phải thành high, ultra thành max - DeepSeek không nhận medium.
    for mdl, level, want_effort in (
            ("deepseek-v4-flash", "high", "high"),
            ("deepseek-v4-pro", "medium", "high"),
            ("deepseek-v4-pro", "ultra", "max"),
    ):
        SEEN.clear()
        async for _ in engine.deepseek_chat_with_mcp(
                "sk-ds-test", mdl, [{"role": "user", "content": "x"}],
                level, TOOLS, ROUTE):
            pass
        got = SEEN[0]["body"].get("reasoning_effort")
        think = SEEN[0]["body"].get("thinking")
        check(f"thinking bật với {mdl}/{level}", think == {"type": "enabled"})
        check(f"reasoning_effort {mdl}/{level} = {want_effort!r} (nhận {got!r})",
              got == want_effort)
    check("gửi key bằng header Bearer", SEEN[0]["auth"] == "Bearer sk-ds-test")


asyncio.run(_run())

_gen = main._api_stream_goc("deepseek", "k", "m", [{"role": "user", "content": "x"}], "off")
check("_api_stream chọn đúng generator của DeepSeek",
      _gen.__qualname__.startswith("deepseek_stream"))
_gen.aclose() if hasattr(_gen, "aclose") else None

_boc = main._api_stream("deepseek", "k", "m", [{"role": "user", "content": "x"}], "off")
check("_api_stream bọc lớp thử lại khi gãy tạm thời",
      _boc.__qualname__.startswith("thu_lai_khi_tam_thoi"))
_boc.aclose() if hasattr(_boc, "aclose") else None


if fails:
    raise SystemExit(f"\nFAIL - test_deepseek_provider: {len(fails)} lỗi")
print("\nOK - test_deepseek_provider: tất cả pass")
