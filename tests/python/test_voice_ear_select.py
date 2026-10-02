"""Tai nghe lại trên bản fork: chọn tai, và chỉ mic chat (nguon=mic) đi đường đó.

    python tests/run.py voice_ear_select

Cuộc họp POST /stt không gửi nguon, nên không được bị tai kéo sang Groq.
"""
from _paths import ROOT, SERVER  # noqa: E402,F401
import json
import os
import tempfile

os.environ.setdefault("JAVIS_STATE_DIR", tempfile.mkdtemp(prefix="javis-ear-"))

import main  # noqa: E402
import nghe_sua  # noqa: E402
import stt  # noqa: E402
import voice_ear  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

client = TestClient(main.app, base_url="http://127.0.0.1")
_fails = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        _fails.append(name)


KEY = {"groq_api_key": "gsk_test"}

check("thiếu khoá -> auto", voice_ear.setting({}) == "auto")
check("stt_provider=browser bị bỏ qua -> auto",
      voice_ear.setting({"voice": {"stt_provider": "browser"}}) == "auto")
check("stt_provider=groq coi là đã chọn groq",
      voice_ear.setting({"voice": {"stt_provider": "groq"}}) == "groq")
check("ear=off thắng khoá cũ",
      voice_ear.setting({"voice": {"ear": "off", "stt_provider": "groq"}}) == "off")

r = voice_ear.select_ear({"model": {}, "voice": {}})
check("auto, không key -> không tai", r["provider"] == "" and r["reason"] == voice_ear.REASON_NONE)
r = voice_ear.select_ear({"model": KEY, "voice": {}}, "anthropic-cli")
check("auto, có key Groq -> tai Groq", r["provider"] == "groq" and r["kind"] == "upload")
r = voice_ear.select_ear({"model": KEY, "voice": {"ear": "off"}})
check("off thắng cả khi có key", r["provider"] == "" and r["reason"] == voice_ear.REASON_OFF)

_goc_mcp = voice_ear._mcp_labels
voice_ear._mcp_labels = lambda: ["Pancake POS", "Gmail", "javis"]
tv = voice_ear.vocab({"voice": {"hotwords": "Webcake"}})
check("từ mồi có tên trợ lý, từ người dùng và tên MCP",
      "Javis" in tv and "Webcake" in tv and "Pancake POS" in tv)
check("lớp sửa mờ không nhận tên MCP",
      "Pancake POS" not in nghe_sua.tu_vung({"voice": {"hotwords": "Webcake"}}))
voice_ear._mcp_labels = _goc_mcp

_goc_cfg, _goc_nghe = main.cfgmod.read_settings, stt.groq_nghe
calls = []


async def fake_nghe(data, ten, key, model="", ngon_ngu=None, hotwords=""):
    calls.append({"key": key, "model": model, "lang": ngon_ngu, "hotwords": hotwords})
    return {"ok": True, "text": "Mở dashboard Facebook Ads", "model": model or "whisper-large-v3"}

stt.groq_nghe = fake_nghe
main.cfgmod.read_settings = lambda: {"model": dict(KEY), "voice": {}}

r = client.get("/voice/ear").json()
check("/voice/ear: auto + key -> groq upload", r.get("ok") and r.get("provider") == "groq" and r.get("kind") == "upload")

r = client.post("/stt", files={"file": ("v.webm", b"OggS-fake-audio", "audio/webm")},
                data={"lang": "vi-VN", "draft": "Mở double Facebook add", "nguon": "mic"})
body = r.json()
check("mic: chạy tai, model đầy đủ, giữ chữ tai khi gần bản nháp",
      body.get("ok") is True and body.get("text") == "Mở dashboard Facebook Ads"
      and calls and calls[-1]["model"] == stt.STT_MODEL_CHUAN)

# Cuộc họp không gửi nguon. Không POST file lần hai: TestClient hay kẹt ở multipart
# (Skipping data after last boundary). Soi mã nguồn là đủ để khóa đường đó.
src = (ROOT / "server" / "main.py").read_text(encoding="utf-8")
mic_at = src.find('if nguon == "mic"')
meet_at = src.find("stt.pick_provider", mic_at if mic_at > 0 else 0)
check("đường mic đứng trước đường cuộc họp, cuộc họp vẫn gọi pick_provider",
      mic_at > 0 and meet_at > mic_at)

calls.clear()
main.cfgmod.read_settings = lambda: {"model": dict(KEY), "voice": {"ear": "off"}}
r = client.post("/stt", files={"file": ("v.webm", b"OggS-fake-audio", "audio/webm")},
                data={"lang": "vi-VN", "draft": "xin chào", "nguon": "mic"})
body = r.json()
check("mic tai tắt: không gọi Groq, giữ đường ok=false",
      not calls and body.get("ok") is False and body.get("ly_do") == "tai_tat")

store = {"model": {}, "voice": {}}
main.cfgmod.read_settings = lambda: store
_goc_write = main.cfgmod.write_settings
main.cfgmod.write_settings = lambda cfg: store.update(cfg)
try:
    client.post("/settings", data={"section": "voice", "data": json.dumps({"ear": "groq"})})
    check("POST /settings lưu ear=groq", store.get("voice", {}).get("ear") == "groq")
    client.post("/settings", data={"section": "voice", "data": json.dumps({"ear": "lạ"})})
    check("giá trị ear lạ bị bỏ", store.get("voice", {}).get("ear") == "groq")
finally:
    main.cfgmod.write_settings = _goc_write

stt.groq_nghe, main.cfgmod.read_settings = _goc_nghe, _goc_cfg

if _fails:
    print("\nFAIL:", len(_fails), _fails)
    raise SystemExit(1)
print("\nOK - tai nghe lại")
