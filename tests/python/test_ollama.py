"""Nhà cung cấp Ollama Cloud.

    python tests/run.py ollama

Bản 0.16.0 đấu CẢ hai đường của Ollama: chạy trên máy nhà và chạy trên Cloud. Chủ repo dùng
Javis trên VPS nên chỉ cần Cloud, và yêu cầu gỡ hẳn phần máy nhà.

Gỡ đi là được nhiều hơn mất về mặt mã: đường máy nhà đòi một ô ĐỊA CHỈ riêng, tức là
`host_field` - ca đặc biệt duy nhất xuyên suốt lớp nhà cung cấp, kéo theo một nhánh riêng ở
`_providers_view`, một nhánh riêng ở thẻ giao diện, và một hàm chọn-đường-theo-key. Bỏ hết,
Ollama thành đúng hình dạng của Groq hay Gemini: dán key là chạy.

File này canh hai thứ. Một, Ollama Cloud chạy thật: lượt chat đi đúng nhánh của nó chứ không
rơi về nhánh Anthropic mặc định cuối `_api_stream` - nhánh nuốt mọi provider quên đấu, và nuốt
trong im lặng. Hai, phần máy nhà đã đi sạch, không để lại mẩu nào còn sống nửa vời.
"""
from _paths import ROOT, SERVER  # noqa: E402,F401
import asyncio
import json
import httpx
import os
import sys
import tempfile
import types

os.environ["JAVIS_STATE_DIR"] = tempfile.mkdtemp(prefix="javis-ollama-")

import config as cfg  # noqa: E402
import engine  # noqa: E402
import main  # noqa: E402

_fails = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        _fails.append(name)


# ---- 1. Là một provider API bình thường, không còn ca đặc biệt ----
_p = main._provider_def("ollama")
check("có nhà cung cấp ollama", bool(_p))
check("thuộc nhóm API (đi qua hub, không chạy lệnh máy)", _p.get("kind") == "api")
check("nhận diện bằng API key như mọi provider API", _p.get("key_field") == "ollama_key")
check("CANARY: không còn ô địa chỉ riêng", "host_field" not in _p)
check("nhãn nói rõ đây là bản Cloud", "Cloud" in (_p.get("label") or ""))
# Danh sách model của Ollama đổi luôn; /provider/models nạp bản LIVE nên đoán hộ là bày ra
# những cái tài khoản người dùng không có.
check("không đoán hộ danh sách model", _p.get("default_models") == [])
check("key có chỗ trong cấu hình mặc định", "ollama_key" in (cfg._DEFAULT["model"] or {}))
check("CANARY: key được mã hoá như mọi key khác", "model.ollama_key" in cfg._SECRET_PATHS)
check("CANARY: cấu hình không còn ô địa chỉ", "ollama_host" not in (cfg._DEFAULT["model"] or {}))


# ---- 2. Endpoint cố định, không dựng từ cấu hình nữa ----
check("gọi thẳng máy chủ Ollama Cloud", engine.OLLAMA_BASE == "https://ollama.com")
check("dùng đường chat chuẩn OpenAI", engine.OLLAMA_URL == "https://ollama.com/v1/chat/completions")
_esrc = (ROOT / "server" / "engine.py").read_text(encoding="utf-8")
check("CANARY: không còn hàm dựng URL theo địa chỉ", "def ollama_url(" not in _esrc)
check("CANARY: không còn địa chỉ máy nhà trong mã", "11434" not in _esrc)


# ---- 3. Chọn làm model chính thì mọi đường đều trỏ về Ollama ----
_c = {"model": dict(cfg._DEFAULT["model"])}
main._set_main_model(_c, "ollama", "gpt-oss:120b-cloud")
check("đặt được làm model chính",
      _c["model"]["main"] == {"provider": "ollama", "model": "gpt-oss:120b-cloud"})
check("engine legacy khớp theo", _c["model"]["engine"] == "ollama")
_c["model"]["ollama_key"] = "sk-cloud-test"
_prov, _kind, _key, _model = main._chat_provider(_c["model"])
check("lượt chat định tuyến về ollama", _prov == "ollama" and _kind == "api")
check("CANARY: mang đúng key vào lượt chat", _key == "sk-cloud-test")
check("giữ đúng model đã chọn", _model == "gpt-oss:120b-cloud")


# ---- 4. Lượt chat THẬT SỰ đi vào nhánh Ollama ----
# `_api_stream` kết thúc bằng `return engine.anthropic_stream(...)` - nhánh mặc định nuốt mọi
# provider quên đấu, và nuốt trong im lặng: không lỗi, chỉ là câu hỏi bay sang Anthropic với
# key của Ollama rồi báo lỗi xác thực chẳng liên quan gì.
_goi = {}
_goc = (engine.ollama_stream, engine.ollama_chat_with_mcp, engine.anthropic_stream)


async def _gia_stream(api_key, model, messages, reasoning="off"):
    _goi["stream"] = {"key": api_key, "model": model}
    yield {"type": "text", "content": "ok"}


async def _gia_anthropic(*a, **k):
    _goi["anthropic"] = True
    yield {"type": "text", "content": "sai nhánh"}


async def _gia_mcp(api_key, model, messages, reasoning, tools, route):
    _goi["mcp"] = {"key": api_key, "model": model, "tools": len(tools or [])}
    yield {"type": "text", "content": "ok"}


engine.ollama_stream, engine.ollama_chat_with_mcp = _gia_stream, _gia_mcp
engine.anthropic_stream = _gia_anthropic
try:
    async def _chay():
        gen = main._api_stream("ollama", "sk-cloud-test", "gpt-oss:120b-cloud",
                               [{"role": "user", "content": "chào"}])
        async for _ in gen:
            pass

    asyncio.run(_chay())
    check("CANARY: lượt chat vào đúng nhánh Ollama", "stream" in _goi)
    check("CANARY: KHÔNG lặng lẽ rơi về Anthropic", "anthropic" not in _goi)
    check("key thật sự được mang theo", (_goi.get("stream") or {}).get("key") == "sk-cloud-test")
finally:
    engine.ollama_stream, engine.ollama_chat_with_mcp, engine.anthropic_stream = _goc


# ---- 5. Có tool MCP thì Ollama cũng là agent, không chỉ chat suông ----
_src = (ROOT / "server" / "main.py").read_text(encoding="utf-8")
check("ollama nằm trong danh sách provider được phát tool",
      '"gemini", "groq", "ollama")' in _src)
check("có nhánh gọi vòng tool cho ollama",
      "engine.ollama_chat_with_mcp(key, model, messages, reasoning, tools, route)" in _src)
check("CANARY: mã đã sạch hàm chọn địa chỉ",
      "_ollama_cfg" not in _src and "_ollama_host" not in _src)


# ---- 6. Lấy danh sách model: hai đường, vì tài liệu không nói rõ đường nào là chính ----
class _FakeResp:
    def __init__(self, ma, body):
        self.status_code, self._body = ma, body

    def raise_for_status(self):
        if self.status_code != 200:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._body


def _fake_httpx(ket_qua):
    """ket_qua: dict đuôi-URL -> (status, body). Ghi lại URL và header đã gọi."""
    duong, auth = [], []

    class _C:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, url, headers=None, **k):
            duong.append(url)
            auth.append((headers or {}).get("Authorization", ""))
            for duoi, (ma, body) in ket_qua.items():
                if url.endswith(duoi):
                    return _FakeResp(ma, body)
            return _FakeResp(404, {})

    mod = types.ModuleType("httpx")
    mod.AsyncClient = _C
    return mod, duong, auth


def _lay_model(ket_qua, m=None):
    mod, duong, auth = _fake_httpx(ket_qua)
    sys.modules["httpx"] = mod
    try:
        ids = asyncio.run(main._fetch_provider_models(
            "ollama", m if m is not None else {"ollama_key": "sk-cloud"}))
    except Exception:  # noqa: BLE001 - cả hai đường hụt là ca hợp lệ, coi như không có model
        ids = None
    finally:
        sys.modules.pop("httpx", None)
    return ids, duong, auth


_ids, _duong, _auth = _lay_model({"/v1/models": (200, {"data": [
    {"id": "gpt-oss:120b-cloud"}, {"id": "qwen3-coder:480b-cloud"}]})})
check("lấy được model qua đường chuẩn OpenAI",
      _ids == ["gpt-oss:120b-cloud", "qwen3-coder:480b-cloud"])
check("hỏi đúng máy chủ Cloud", bool(_duong) and _duong[0].startswith(engine.OLLAMA_BASE))
check("CANARY: mang key theo khi hỏi model, không chỉ khi chat",
      bool(_auth) and all(a == "Bearer sk-cloud" for a in _auth))

# Đường chuẩn hụt thì phải hỏi tiếp đường gốc của Ollama; thiếu bước này là key đúng mà trang
# vẫn báo "chưa thấy model".
_ids, _duong, _auth = _lay_model({
    "/v1/models": (404, {}),
    "/api/tags": (200, {"models": [{"name": "gpt-oss:120b-cloud"}]}),
})
check("CANARY: hụt đường chuẩn thì hỏi tiếp đường gốc Ollama", _ids == ["gpt-oss:120b-cloud"])
check("thử đúng thứ tự: chuẩn trước, gốc sau",
      len(_duong) == 2 and _duong[0].endswith("/v1/models") and _duong[1].endswith("/api/tags"))
# Giữ tên kèm tag: "gpt-oss" và "gpt-oss:120b-cloud" là hai model khác nhau.
check("giữ nguyên tên kèm tag", _ids == ["gpt-oss:120b-cloud"])

# Chưa dán key thì đừng gọi mạng làm gì - vừa vô ích vừa bắt người dùng chờ.
_ids, _duong, _auth = _lay_model({}, m={})
check("CANARY: chưa có key thì không gọi mạng", _ids is None and not _duong)


# ---- 7. Giao diện: thẻ key thường, không còn ô địa chỉ ----
_console = (ROOT / "dashboard" / "console.js").read_text(encoding="utf-8")
check("CANARY: giao diện không còn nhánh theo địa chỉ", "needs_host" not in _console)
check("CANARY: không còn nút Kiểm tra địa chỉ", "data-ph=" not in _console)
# Thiếu dòng này thì thẻ Ollama hiện "Đổi key (•••)" với bốn ký tự cuối của... không gì cả.
check("bảng key của giao diện biết ollama", '"ollama": "ollama_key"' in _console)
# deepseek đứng sau ollama trong danh sách - đừng khớp cứng `"ollama"]` vì sẽ vỡ khi thêm provider.
check("ollama vẫn nằm trong danh sách provider có MCP",
      'const MCP_PROVIDERS = ["anthropic-cli", "openrouter", "openai", "anthropic-api", "gemini", "groq", "ollama", "deepseek"]'
      in _console)


# ---- 8. Việc nền (aux_engine) cũng chạy được bằng Ollama Cloud ----
# Trước đây card Models có Ollama nhưng aux_engine quên đấu → chọn làm model việc nền
# thì availability báo "provider lạ" và lặng lẽ fallback về Claude (đòi /login).
import aux_engine  # noqa: E402

check("aux_engine coi ollama là provider API", "ollama" in aux_engine.API_PROVIDERS)
check("aux_engine map đúng ô key ollama",
      aux_engine._KEY_FIELD.get("ollama") == "ollama_key")
_S_OL = {"model": {"auxiliary": {"provider": "ollama", "model": "gpt-oss:120b-cloud"},
                   "ollama_key": "sk-cloud-test"}}
_ok, _why = aux_engine.availability(aux_engine.read_spec(_S_OL), _S_OL)
check("có key thì availability OK cho việc nền", _ok and not _why)
_fake = type("C", (), {"system_prompt": "S", "cwd": "/v", "javis_vault": "/v",
                       "javis_mode": "suggest", "tag": "reminder", "model": None})()
_out = aux_engine.swap(_fake, mode="suggest", settings=_S_OL)
# FallbackChain uỷ quyền attr sang mắt đầu → .provider/.model thấy được luôn.
check("swap việc nền dựng engine API ollama",
      getattr(_out, "provider", None) == "ollama"
      and getattr(_out, "model", None) == "gpt-oss:120b-cloud")

# ---- 9. Ollama thiếu key + Claude chưa login → KHÔNG fallback Claude (/login) ----
_real_ready = aux_engine._claude_session_ready
aux_engine._claude_session_ready = lambda: False
try:
    _S_NO = {"model": {"auxiliary": {"provider": "ollama", "model": "gpt-oss:120b-cloud"}}}
    _fake2 = type("C", (), {"system_prompt": "S", "cwd": "/v", "javis_vault": "/v",
                            "javis_mode": "suggest", "tag": "reminder", "model": None})()
    _out2 = aux_engine.swap(_fake2, mode="suggest", settings=_S_NO)
    check("ollama thiếu key không fallback Claude khi chưa login",
          _out2 is not _fake2 and getattr(_out2, "provider", None) == "none")
finally:
    aux_engine._claude_session_ready = _real_ready

# ---- 10. Ollama Local: num_ctx + rút system prompt việc nền ----
# Ca thật: nhắc hẹn gửi ~12k token system (CLAUDE.md) trong khi Ollama mặc định 4096 → 400.
import engine as _eng  # noqa: E402

check("num_ctx mặc định == 4096 (VPS 6GB không swap, tránh OOM)", _eng.ollama_local_num_ctx() == 4096)
check("extra có options.num_ctx",
      (_eng._ollama_local_extra().get("options") or {}).get("num_ctx", 0) == 4096)
check("extra giữ model nóng keep_alive",
      bool(_eng._ollama_local_extra().get("keep_alive")))
check("extra cắt num_predict",
      (_eng._ollama_local_extra().get("options") or {}).get("num_predict", 0) > 0)
check("summarize extra num_predict cao",
      (_eng._ollama_local_extra_summarize("javis-qwen3-8b").get("options") or {}).get("num_predict", 0) >= 2048)
check("summarize qwen3 tắt think",
      _eng._ollama_local_extra_summarize("javis-qwen3-8b").get("think") is False)
check("summarize model thường không ép think",
      "think" not in _eng._ollama_local_extra_summarize("llama3.2:3b"))
check("local giới hạn vòng tool",
      1 <= _eng.ollama_local_max_tool_rounds() <= 8)
_huge = "X" * 20000
_c = aux_engine._compact_ollama_local_sys(_huge, "/vault/test")
check("system prompt việc nền local được rút gọn",
      len(_c) < 2000 and "Javis" in _c and "/vault/test" in _c)
_short = "Ngắn thôi."
check("system prompt ngắn giữ nguyên",
      aux_engine._compact_ollama_local_sys(_short, None) == _short)

# ---- 11. Ollama Local: /api/chat native + adapter (v1 bỏ num_ctx) ----
# Ca thật sau #16: vẫn 12744 > 4096 vì /v1/chat/completions bỏ options.num_ctx.
check("native URL dùng /api/chat",
      _eng.ollama_local_native_url().endswith("/api/chat")
      if _eng.ollama_local_endpoint() else True)
_native = _eng._ollama_native_to_openai({
    "message": {
        "role": "assistant", "content": "",
        "tool_calls": [{"function": {"name": "javis_read_file",
                                     "arguments": {"path": "a.md"}}}],
    },
    "prompt_eval_count": 100, "eval_count": 5,
})
_msg = ((_native.get("choices") or [{}])[0].get("message") or {})
_tc = ((_msg.get("tool_calls") or [{}])[0])
check("adapter đổi tool_calls sang OpenAI shape",
      (_tc.get("function") or {}).get("name") == "javis_read_file"
      and isinstance((_tc.get("function") or {}).get("arguments"), str)
      and '"path"' in (_tc.get("function") or {}).get("arguments", "")
      and _tc.get("id"))
check("adapter map usage token",
      (_native.get("usage") or {}).get("prompt_tokens") == 100)

# ---- 12. Replay tool_calls về native: arguments phải là object ----
# Ca Telegram: Ollama (Local) 400 "Value looks like object, but can't find closing '}'"
# vì vòng 2 gửi lại arguments dạng JSON string (OpenAI shape).
_hist = [{
    "role": "assistant", "content": "",
    "tool_calls": [{
        "id": "c1", "type": "function",
        "function": {"name": "javis_read_file",
                     "arguments": json.dumps({"path": "a.md"}, ensure_ascii=False)},
    }],
}, {"role": "tool", "tool_call_id": "c1", "content": "ok"}]
_back = _eng._ollama_messages_for_native(_hist)
_args = ((_back[0].get("tool_calls") or [{}])[0].get("function") or {}).get("arguments")
check("replay native: arguments là object",
      isinstance(_args, dict) and _args.get("path") == "a.md")
check("replay native: role tool giữ nguyên",
      _back[1].get("role") == "tool")
check("parse args hỏng → vẫn object (không nổ)",
      isinstance(_eng._ollama_parse_tool_args("{not-json"), dict))
check("bắt lỗi Ollama thiếu closing brace như tool-syntax",
      _eng._is_tool_syntax_failure(
          'Value looks like object, but can\'t find closing \'}\' symbol'))


# ---- 13. Ollama Local: 500 unexpected EOF = runner OOM → hạ num_ctx ----
# Ca Telegram: Ollama (Local) 500 {"error":"... unexpected EOF"} trên VPS 5.8GB/0 swap.
_eof = '{"error":"an error was encountered while running the model: unexpected EOF"}'
check("nhận diện runner crash unexpected EOF",
      _eng._is_ollama_runner_crash(_eof))
check("không nhận nhầm lỗi thiếu } là runner crash",
      not _eng._is_ollama_runner_crash(
          "Value looks like object, but can't find closing '}' symbol"))
_ex = {"keep_alive": "10m", "options": {"num_ctx": 8192, "num_predict": 512}}
check("shrink 8192 → 4096",
      _eng._shrink_ollama_local_ctx(_ex) == 4096
      and _ex["options"]["num_ctx"] == 4096)
check("shrink 4096 → 2048",
      _eng._shrink_ollama_local_ctx(_ex) == 2048)
check("shrink chạm sàn thì dừng",
      _eng._shrink_ollama_local_ctx(_ex) is None)
check("payload bỏ key nội bộ _ctx_shrinks",
      "_ctx_shrinks" not in _eng._ollama_extra_for_payload(_ex))
_msg = _eng._ollama_runner_crash_user_msg(500, _eof)
check("thông báo EOF nói hết RAM",
      "RAM" in _msg and "500" in _msg)


# ---- 14. Ollama Local: HTTP timeout dài cho CPU (tránh ReadTimeout 180s) ----
_to = _eng.ollama_local_http_timeout()
check("HTTP timeout local >= 600s", float(_to.read) >= 600)
check("nhận diện ReadTimeout",
      _eng._is_ollama_timeout(httpx.ReadTimeout("timed out")))
check("nhận diện deadline exceeded",
      _eng._is_ollama_timeout(RuntimeError("Cancelled via cancel scope; reason: deadline exceeded")))
check("thông báo timeout nói CPU",
      "CPU" in _eng._ollama_timeout_user_msg(httpx.ReadTimeout("x")))
check("max tool rounds local <= 4",
      _eng.ollama_local_max_tool_rounds() <= 4)
check("num_predict local <= 256",
      (_eng._ollama_local_extra().get("options") or {}).get("num_predict", 0) <= 256)

print()
if _fails:
    print(f"THẤT BẠI {len(_fails)}: {_fails}")
    sys.exit(1)
print("OK - test_ollama: tất cả pass")
