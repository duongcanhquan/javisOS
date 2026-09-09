"""Gemini STT: model 2.5-flash chết với user mới → đổi sang 3.6; đừng đọc lỗi Google cho user.

    python tests/run.py stt_gemini

Google trả 404 `This model models/gemini-2.5-flash is no longer available to new users`.
Hai chỗ dễ vỡ:
  1. Câu 'no longer available' không có chữ 'not found' → code cũ dừng luôn, không thử model kế.
  2. `noi_voi_javis` nhét nguyên dump API → Javis đọc model id cho người dùng thay vì nhờ gõ chữ.
"""
from _paths import SERVER  # noqa: E402,F401
import asyncio
import os
import tempfile

os.environ.setdefault("JAVIS_STATE_DIR", tempfile.mkdtemp(prefix="javis-stt-gem-"))

import stt  # noqa: E402

_fails = []
_LOI_25 = ("This model models/gemini-2.5-flash is no longer available to new users. "
           "Please update your code to use models/gemini-3.6-flash for the latest "
           "features and improvements. We recommend you to use the Int")


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        _fails.append(name)


def chay(coro):
    return asyncio.get_event_loop_policy().new_event_loop().run_until_complete(coro)


class _Resp:
    def __init__(self, code, data):
        self.status_code = code
        self._d = data
        self.text = str(data)

    def json(self):
        return self._d


class _GeminiFake:
    goi = []
    bang = {}

    def __init__(self, *a, **k):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def post(self, url, headers=None, data=None, files=None, params=None, json=None):
        _GeminiFake.goi.append(url)
        for k, v in _GeminiFake.bang.items():
            if k in url:
                return _Resp(*v)
        return _Resp(404, {"error": {"message": "not found"}})


def _ok_text(s):
    return {"candidates": [{"content": {"parts": [{"text": s}]}}]}


check("danh sách STT không còn gemini-2.5-flash",
      "gemini-2.5-flash" not in stt.STT_GEMINI_MODELS)
check("ưu tiên gemini-3.6-flash",
      stt.STT_GEMINI_MODELS[0] == "gemini-3.6-flash")

_dong = stt.loi_thanh_dong("loi", _LOI_25)
check("lỗi model chết -> nhờ gõ chữ", "gõ chữ" in _dong)
check("lỗi model chết -> báo chỗ nghe giọng trục trặc", "nghe giọng" in _dong and "trục trặc" in _dong)
check("lỗi model chết -> KHÔNG nhét gemini-2.5-flash vào lời dặn",
      "gemini-2.5-flash" not in _dong)
check("lỗi model chết -> KHÔNG nhét 'Please update your code'",
      "Please update" not in _dong and "no longer available" not in _dong)
check("lỗi ngắn vẫn giữ lý do (mạng chết)",
      "mạng chết" in stt.loi_thanh_dong("loi", "mạng chết"))

_that = stt.httpx.AsyncClient
stt.httpx.AsyncClient = _GeminiFake
try:
    _GeminiFake.goi.clear()
    _GeminiFake.bang = {
        "gemini-3.6-flash": (200, _ok_text("  họp lúc chín  ")),
        "gemini-2.5-flash": (404, {"error": {"message": _LOI_25}}),
    }
    kq = chay(stt.gemini_nghe(b"audio", "voice.ogg", "key-gem"))
    check("3.6 sống -> nghe được, không đụng 2.5",
          kq.get("ok") and kq.get("text") == "họp lúc chín")
    check("3.6 sống -> URL gọi 3.6-flash",
          any("gemini-3.6-flash" in u for u in _GeminiFake.goi))
    check("3.6 sống -> không gọi 2.5-flash",
          not any("gemini-2.5-flash" in u for u in _GeminiFake.goi))

    _GeminiFake.goi.clear()
    _GeminiFake.bang = {
        "gemini-3.6-flash": (404, {"error": {"message": "model not found"}}),
        "gemini-2.5-flash": (404, {"error": {"message": _LOI_25}}),
        "gemini-3.5-flash": (200, _ok_text("xin chào")),
    }
    kq = chay(stt.gemini_nghe(b"audio", "voice.ogg", "key-gem"))
    check("3.6 404 + 2.5 chết -> nhảy sang 3.5 chứ không dừng ở dump Google",
          kq.get("ok") and kq.get("text") == "xin chào")
    check("không gọi gemini-2.5-flash (đã remap/bỏ)",
          not any("gemini-2.5-flash" in u for u in _GeminiFake.goi))

    _GeminiFake.goi.clear()
    _GeminiFake.bang = {
        "gemini-3.6-flash": (404, {"error": {"message": _LOI_25}}),
        "gemini-3.5-flash": (404, {"error": {"message": _LOI_25}}),
        "gemini-3.5-flash-lite": (404, {"error": {"message": _LOI_25}}),
    }
    kq = chay(stt.gemini_nghe(b"audio", "voice.ogg", "key-gem"))
    check("hết model -> không ok", not kq.get("ok"))
    _cau = kq.get("noi_voi_javis") or ""
    check("hết model -> nhờ gõ chữ, báo trục trặc",
          "gõ chữ" in _cau and "trục trặc" in _cau)
    check("hết model -> không đọc dump Google",
          "gemini-2.5-flash" not in _cau and "Please update" not in _cau)

    _GeminiFake.goi.clear()
    _GeminiFake.bang = {
        "gemini-3.6-flash": (200, _ok_text("đã đổi model")),
        "gemini-2.5-flash": (404, {"error": {"message": _LOI_25}}),
    }
    kq = chay(stt.gemini_nghe(b"audio", "v.ogg", "key-gem", model="gemini-2.5-flash"))
    check("caller ghim 2.5-flash -> vẫn gọi 3.6",
          kq.get("ok") and any("gemini-3.6-flash" in u for u in _GeminiFake.goi))
    check("caller ghim 2.5-flash -> không POST 2.5",
          not any("gemini-2.5-flash" in u for u in _GeminiFake.goi))
finally:
    stt.httpx.AsyncClient = _that


if _fails:
    raise SystemExit(f"\nFAIL - test_stt_gemini: {len(_fails)} lỗi: {_fails}")
print("\nOK - test_stt_gemini: tất cả pass")
