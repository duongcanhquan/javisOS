"""Nghe tin thoại: file âm thanh -> chữ (speech-to-text).

Ưu tiên phổ thông (không bắt buộc Groq):
  1) Google Gemini (API) — cùng key trang Models mà nhiều người đã dùng để chat
  2) OpenAI Whisper (nếu có openai_api_key)
  3) Groq Whisper — chỉ nếu còn key cũ (tuỳ chọn, không khuyến nghị)

Mic cuộc họp / chat dashboard ưu tiên Moonshine local + Web Speech trình duyệt;
module này chỉ phục vụ upload / đoạn MediaRecorder / tin thoại Telegram·Zalo.

Trả về LUÔN dict có `ok`. Hỏng thì `ly_do` + `noi_voi_javis` — không ném ngoại lệ.
"""
from __future__ import annotations

import base64
import sys
from typing import Any, Optional

import httpx

STT_MAC_DINH = "vi"
MAX_STT_MB = 24
STT_TIMEOUT = 120.0

# Legacy Groq Whisper (tuỳ chọn)
GROQ_STT_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
STT_MODEL_MAC_DINH = "whisper-large-v3-turbo"
STT_MODEL_CHUAN = "whisper-large-v3"
OPENAI_STT_URL = "https://api.openai.com/v1/audio/transcriptions"
OPENAI_WHISPER_MODEL = "whisper-1"

# Gemini multimodal — thử lần lượt. Không liệt kê 2.5-flash: Google ngừng bán cho user mới
# (404 `no longer available` — câu đó không có chữ 'not found' nên loop cũ dừng luôn).
STT_GEMINI_MODELS = (
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
)

# Câu Google khi model chết: phải skip, không trả dump cho LLM đọc thành tiếng.
_SKIP_MODEL_MSG = (
    "not found", "not supported for", "unknown model",
    "no longer available", "not available to new users",
    "update your code", "is not available",
)
_DUMP_API_MSG = (
    "no longer available", "not available to new users",
    "please update your code", "models/gemini", "models/",
    "invalid argument", "request contains an invalid",
)
_PAYLOAD_MSG = (
    "invalid argument", "invalid mime", "unsupported mime",
    "unsupported audio", "invalid audio",
)

_PROMPT_VI = ("Tiếng Việt có dấu. Ghi đúng chính tả và dấu thanh. "
              "Giữ nguyên tên riêng và từ kỹ thuật tiếng Anh nếu có.")
_PROMPT_EN = ("Transcribe clearly in English. Keep proper nouns and technical terms.")

_HD_THIEU_KEY = (
    "[Người dùng vừa gửi TIN THOẠI. Javis chưa nghe được vì chưa có API key Groq để chuyển "
    "giọng thành chữ. Hãy nói với họ: vào trang Models, dán API key Groq rồi lưu; "
    "dashboard/cuộc họp cũng dùng Moonshine local + nhận giọng trình duyệt (Chrome/Edge) "
    "không cần key. Trong lúc chờ nhờ họ gõ chữ. Nếu đang đóng vai người thật nói với khách "
    "thì CHỈ nhờ họ gõ chữ, đừng nhắc API key hay dashboard.]")

MARK_THOAI = "[Tin THOẠI"


def khoi_thoai(nghe, kenh):
    """Câu đã nghe + dòng dặn — đưa thẳng vào lượt chat."""
    dan = (MARK_THOAI + f" qua {kenh}. Javis đã nghe thành chữ (có thể nhầm vài từ) - câu ở "
           "dưới. Cứ làm theo như user gõ tay. Nếu việc sắp làm có tác động RA NGOÀI (gửi "
           "tin, đăng bài, đặt lịch, tiêu tiền, sửa file) thì mở đầu bằng một dòng "
           "\"Mình nghe: ...\" rồi hỏi xác nhận trước khi làm.]")
    return dan + "\n" + str(nghe or "").strip()


def _mb(n):
    return round(n / (1024 * 1024), 1)


def _chi_tiet_an_toan(chi_tiet: str) -> str:
    """Bỏ dump API (model id, 'update your code') khỏi lời dặn LLM — user chỉ cần gõ chữ."""
    s = (chi_tiet or "").strip()
    if not s:
        return ""
    low = s.lower()
    if any(x in low for x in _DUMP_API_MSG):
        return ""
    return s[:200]


def _doi_model_khac(status: int, msg: str) -> bool:
    """404 luôn thử model kế. 400 chỉ khi câu lỗi nói model chết — không phải MIME audio hỏng."""
    if status == 404:
        return True
    low = (msg or "").lower()
    if status != 400:
        return False
    if any(x in low for x in _PAYLOAD_MSG):
        return False
    return any(x in low for x in _SKIP_MODEL_MSG)


def _loi_payload(msg: str) -> bool:
    low = (msg or "").lower()
    return any(x in low for x in _PAYLOAD_MSG)


def _doi_id_gemini(mdl: str) -> str:
    """2.5-flash (và id cũ khác) → id còn mở. Trùng bảng chat engine."""
    m = (mdl or "").strip()
    if m.startswith("models/"):
        m = m[len("models/"):]
    try:
        from engine import gemini_resolve_model
        return gemini_resolve_model(m)
    except Exception:
        bang = {
            "gemini-2.5-flash": "gemini-3.6-flash",
            "gemini-2.5-flash-lite": "gemini-3.5-flash-lite",
            "gemini-2.0-flash": "gemini-3.6-flash",
            "gemini-2.0-flash-001": "gemini-3.6-flash",
            "gemini-1.5-flash": "gemini-3.6-flash",
        }
        return bang.get(m, m) or "gemini-3.6-flash"


def _danh_sach_model_gemini(model: str = "") -> list[str]:
    raw = []
    if (model or "").strip():
        raw.append(model)
    raw.extend(STT_GEMINI_MODELS)
    out, seen = [], set()
    for m in raw:
        m = _doi_id_gemini(m)
        if m and m not in seen:
            seen.add(m)
            out.append(m)
    return out


def loi_thanh_dong(ly_do, chi_tiet=""):
    if ly_do == "thieu_key":
        return _HD_THIEU_KEY
    if ly_do == "qua_lon":
        return ("[Người dùng gửi một tin thoại quá dài để Javis nghe " + chi_tiet + ". "
                "Nhờ họ thu ngắn lại hoặc gõ chữ.]")
    if ly_do == "khong_nghe_ro":
        return ("[Người dùng gửi tin thoại nhưng Javis nghe không ra chữ nào (có thể im lặng "
                "hoặc quá ồn). Nhờ họ thu lại gần micro hơn, hoặc gõ chữ.]")
    ct = _chi_tiet_an_toan(chi_tiet)
    if ct:
        return ("[Người dùng gửi tin thoại nhưng Javis nghe hỏng: " + ct +
                ". Nhờ họ gõ chữ, và báo là chỗ nghe giọng đang trục trặc.]")
    return ("[Người dùng gửi tin thoại nhưng Javis nghe hỏng. "
            "Nhờ họ gõ chữ, và báo là chỗ nghe giọng đang trục trặc.]")


def _sniff_audio(data) -> str:
    """Đọc magic bytes. Telegram/Zalo thoại là Ogg/Opus — Gemini hiểu audio/ogg là Vorbis."""
    b = data or b""
    if len(b) < 4:
        return ""
    if b[:4] == b"OggS":
        head = b[:1024]
        if b"OpusHead" in head:
            return "audio/opus"
        if b"vorbis" in head:
            return "audio/ogg"
        return "audio/opus"
    if b[:4] == b"RIFF" and len(b) >= 12 and b[8:12] == b"WAVE":
        return "audio/wav"
    if b[:4] == b"fLaC":
        return "audio/flac"
    if b[:3] == b"ID3" or (len(b) >= 2 and b[0] == 0xFF and (b[1] & 0xE0) == 0xE0):
        return "audio/mp3"
    if b[:4] == b"\x1aE\xdf\xa3":
        return "audio/webm"
    return ""


def _mime(ten_file: str, data=b"") -> str:
    sniffed = _sniff_audio(data)
    if sniffed:
        return sniffed
    n = (ten_file or "").lower()
    if n.endswith(".webm"):
        return "audio/webm"
    if n.endswith(".opus"):
        return "audio/opus"
    if n.endswith(".ogg") or n.endswith(".oga"):
        return "audio/ogg"
    if n.endswith(".mp3"):
        return "audio/mpeg"
    if n.endswith(".wav"):
        return "audio/wav"
    if n.endswith(".m4a") or n.endswith(".mp4") or n.endswith(".aac"):
        return "audio/mp4"
    if n.endswith(".flac"):
        return "audio/flac"
    return "audio/webm"


def _mime_candidates(ten_file: str, data=b"") -> list[str]:
    primary = _mime(ten_file, data)
    extra = []
    if primary == "audio/opus":
        extra = ["audio/ogg", "audio/ogg; codecs=opus"]
    elif primary == "audio/ogg":
        extra = ["audio/opus", "audio/ogg; codecs=opus"]
    elif primary == "audio/webm":
        extra = ["audio/opus", "audio/ogg"]
    out, seen = [], set()
    for m in [primary] + extra:
        if m and m not in seen:
            seen.add(m)
            out.append(m)
    return out


def _check_bytes(data, ten_file="") -> Optional[dict]:
    if not data:
        return {"ok": False, "ly_do": "rong", "noi_voi_javis": loi_thanh_dong("loi", "file rỗng")}
    if len(data) > MAX_STT_MB * 1024 * 1024:
        ct = f"({_mb(len(data))}MB, trần {MAX_STT_MB}MB)"
        return {"ok": False, "ly_do": "qua_lon", "noi_voi_javis": loi_thanh_dong("qua_lon", ct)}
    return None


def _goi_y_ngon(ngon_ngu) -> str:
    """None → mặc định vi; '' → không gợi ý; còn lại → mã ngôn ngữ."""
    if ngon_ngu is None:
        return STT_MAC_DINH
    return ngon_ngu if isinstance(ngon_ngu, str) else STT_MAC_DINH


def _prompt_cho(goi_y: str, prompt) -> str:
    if prompt is not None:
        return prompt
    if goi_y == "vi" or (not goi_y and STT_MAC_DINH == "vi"):
        return _PROMPT_VI
    if goi_y == "en":
        return _PROMPT_EN
    return ""


def pick_provider(model_cfg: Optional[dict]) -> dict[str, Any]:
    """Chọn nhà STT từ khối settings['model']. Không bắt buộc Groq."""
    m = model_cfg or {}
    gem = (m.get("gemini_api_key") or "").strip()
    if gem:
        return {"provider": "gemini", "key": gem, "label": "Gemini", "available": True}
    oai = (m.get("openai_api_key") or "").strip()
    if oai:
        return {"provider": "openai", "key": oai, "label": "OpenAI Whisper", "available": True}
    groq = (m.get("groq_api_key") or "").strip()
    if groq:
        return {"provider": "groq", "key": groq, "label": "Groq Whisper", "available": True}
    return {
        "provider": None, "key": "", "label": "", "available": False,
        "hint": "Models → Google Gemini (API) — hoặc dùng Web Speech / Moonshine trên dashboard.",
    }


def status_from_settings(model_cfg: Optional[dict]) -> dict[str, Any]:
    p = pick_provider(model_cfg)
    return {
        "ok": True,
        "available": bool(p.get("available")),
        "provider": p.get("provider"),
        "label": p.get("label") or "",
        "hint": p.get("hint") or (
            "Cloud STT: " + (p.get("label") or "") + ". Cuộc họp ưu tiên Moonshine + Web Speech."
        ),
    }


async def gemini_nghe(data, ten_file, api_key, ngon_ngu=None, prompt=None, model=""):
    """STT qua Gemini generateContent (inline audio)."""
    bad = _check_bytes(data, ten_file)
    if bad:
        return bad
    if not api_key:
        return {"ok": False, "ly_do": "thieu_key", "noi_voi_javis": loi_thanh_dong("thieu_key")}

    goi_y = _goi_y_ngon(ngon_ngu)
    tip = _prompt_cho(goi_y, prompt)
    if goi_y == "vi":
        instruct = ("Chuyển toàn bộ đoạn âm thanh sau thành chữ tiếng Việt có dấu. "
                    "Chỉ trả về nội dung đã nghe, không giải thích, không dịch sang ngôn ngữ khác.")
    elif goi_y == "en":
        instruct = ("Transcribe the following audio to English text only. "
                    "No explanation, no translation into another language.")
    elif goi_y:
        instruct = (f"Transcribe the following audio. Prefer language code '{goi_y}'. "
                    "Return only the transcript text.")
    else:
        instruct = ("Transcribe the following audio in its original language. "
                    "Return only the transcript text.")
    if tip:
        instruct = instruct + " " + tip

    b64 = base64.b64encode(data).decode("ascii")
    models = _danh_sach_model_gemini(model)
    last_err = ""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(STT_TIMEOUT)) as c:
            for mime in _mime_candidates(ten_file, data):
                body = {
                    "contents": [{
                        "role": "user",
                        "parts": [
                            {"text": instruct},
                            {"inline_data": {"mime_type": mime, "data": b64}},
                        ],
                    }],
                    "generationConfig": {"temperature": 0.0},
                }
                doi_mime = False
                for mdl in models:
                    if not mdl:
                        continue
                    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
                           f"{mdl}:generateContent")
                    r = await c.post(url, params={"key": api_key}, json=body)
                    d: dict = {}
                    try:
                        d = r.json()
                    except Exception:
                        pass
                    if r.status_code != 200:
                        err = d.get("error") if isinstance(d, dict) else None
                        msg = ""
                        if isinstance(err, dict):
                            msg = str(err.get("message") or err)
                        else:
                            msg = str(err or r.text or f"HTTP {r.status_code}")
                        last_err = msg
                        if _doi_model_khac(r.status_code, msg):
                            print(f"[stt gemini] skip {mdl}: {msg[:160]}", file=sys.stderr)
                            continue
                        if _loi_payload(msg):
                            print(f"[stt gemini] mime {mime}: {msg[:160]}", file=sys.stderr)
                            doi_mime = True
                            break
                        print(f"[stt gemini] {mdl}: {msg[:200]}", file=sys.stderr)
                        return {"ok": False, "ly_do": "loi",
                                "noi_voi_javis": loi_thanh_dong("loi", msg[:200])}
                    text = ""
                    for cand in (d.get("candidates") or []):
                        parts = ((cand.get("content") or {}).get("parts") or [])
                        for p in parts:
                            if isinstance(p, dict) and p.get("text"):
                                text += str(p["text"])
                    text = text.strip()
                    if not text:
                        fb = d.get("promptFeedback") or {}
                        last_err = str(fb.get("blockReason") or "empty transcript")
                        continue
                    return {"ok": True, "text": text, "model": mdl, "provider": "gemini"}
                if doi_mime:
                    continue
    except Exception as e:
        loi = f"{type(e).__name__}: {e}"
        print(f"[stt gemini] {loi}", file=sys.stderr)
        return {"ok": False, "ly_do": "loi", "noi_voi_javis": loi_thanh_dong("loi", loi[:200])}

    if last_err:
        return {"ok": False, "ly_do": "loi",
                "noi_voi_javis": loi_thanh_dong("loi", last_err[:200])}
    return {"ok": False, "ly_do": "khong_nghe_ro",
            "noi_voi_javis": loi_thanh_dong("khong_nghe_ro")}


async def openai_nghe(data, ten_file, api_key, ngon_ngu=None, prompt=None,
                      model=""):
    """OpenAI Whisper HTTP API."""
    bad = _check_bytes(data, ten_file)
    if bad:
        return bad
    if not api_key:
        return {"ok": False, "ly_do": "thieu_key", "noi_voi_javis": loi_thanh_dong("thieu_key")}
    mdl = model or OPENAI_WHISPER_MODEL
    goi_y = _goi_y_ngon(ngon_ngu)
    form: dict[str, Any] = {"model": mdl, "response_format": "json"}
    if goi_y:
        form["language"] = goi_y
    tip = _prompt_cho(goi_y, prompt)
    if tip:
        form["prompt"] = tip
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(STT_TIMEOUT)) as c:
            r = await c.post(
                OPENAI_STT_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                data=form,
                files={"file": (ten_file or "voice.webm", data, _mime(ten_file, data))},
            )
        d = {}
        try:
            d = r.json()
        except Exception:
            pass
        if r.status_code != 200:
            ly = ((d.get("error") or {}).get("message") if isinstance(d.get("error"), dict)
                  else d.get("error")) or f"OpenAI HTTP {r.status_code}"
            print(f"[stt openai] {ly}", file=sys.stderr)
            return {"ok": False, "ly_do": "loi", "noi_voi_javis": loi_thanh_dong("loi", str(ly)[:200])}
        text = str(d.get("text") or "").strip()
        if not text:
            return {"ok": False, "ly_do": "khong_nghe_ro",
                    "noi_voi_javis": loi_thanh_dong("khong_nghe_ro")}
        return {"ok": True, "text": text, "model": mdl, "provider": "openai"}
    except Exception as e:
        loi = f"{type(e).__name__}: {e}"
        print(f"[stt openai] {loi}", file=sys.stderr)
        return {"ok": False, "ly_do": "loi", "noi_voi_javis": loi_thanh_dong("loi", loi[:200])}


async def groq_nghe(data, ten_file, api_key, model="", ngon_ngu=None, prompt=None,
                    temperature=0.0):
    """Whisper qua Groq — giữ tương thích; không còn là đường mặc định."""
    bad = _check_bytes(data, ten_file)
    if bad:
        return bad
    if not api_key:
        return {"ok": False, "ly_do": "thieu_key", "noi_voi_javis": loi_thanh_dong("thieu_key")}

    mdl = model or STT_MODEL_MAC_DINH
    form = {"model": mdl, "response_format": "json", "temperature": str(temperature)}
    goi_y = _goi_y_ngon(ngon_ngu)
    if goi_y:
        form["language"] = goi_y
    tip = _prompt_cho(goi_y, prompt)
    if tip:
        form["prompt"] = tip
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(STT_TIMEOUT)) as c:
            r = await c.post(GROQ_STT_URL,
                             headers={"Authorization": f"Bearer {api_key}"},
                             data=form,
                             files={"file": (ten_file or "voice.ogg", data)})
        d = {}
        try:
            d = r.json()
        except Exception:
            pass
        if r.status_code != 200:
            ly = ((d.get("error") or {}).get("message") if isinstance(d.get("error"), dict)
                  else d.get("error")) or f"Groq HTTP {r.status_code}"
            print(f"[stt groq] {ly}", file=sys.stderr)
            return {"ok": False, "ly_do": "loi", "noi_voi_javis": loi_thanh_dong("loi", str(ly)[:200])}
        text = str(d.get("text") or "").strip()
        if not text:
            return {"ok": False, "ly_do": "khong_nghe_ro",
                    "noi_voi_javis": loi_thanh_dong("khong_nghe_ro")}
        return {"ok": True, "text": text, "model": mdl, "provider": "groq"}
    except Exception as e:
        loi = f"{type(e).__name__}: {e}"
        print(f"[stt groq] {loi}", file=sys.stderr)
        return {"ok": False, "ly_do": "loi", "noi_voi_javis": loi_thanh_dong("loi", loi[:200])}


async def nghe(data, ten_file, model_cfg, ngon_ngu=None, prompt=None,
               prefer_quality: bool = False):
    """Điểm vào thống nhất: Gemini → OpenAI → Groq theo key có sẵn.

    Gemini hỏng MIME (tin thoại Telegram Ogg/Opus) thì vẫn thử Whisper nếu có key.
    prefer_quality: với Groq dùng large-v3 (dashboard/cuộc họp); kênh chat giữ turbo.
    """
    m = model_cfg or {}
    gem = (m.get("gemini_api_key") or "").strip()
    oai = (m.get("openai_api_key") or "").strip()
    groq = (m.get("groq_api_key") or "").strip()
    if not (gem or oai or groq):
        return {"ok": False, "ly_do": "thieu_key", "noi_voi_javis": loi_thanh_dong("thieu_key")}
    last = None
    if gem:
        last = await gemini_nghe(data, ten_file, gem, ngon_ngu=ngon_ngu, prompt=prompt)
        if last.get("ok"):
            return last
    if oai:
        last = await openai_nghe(data, ten_file, oai, ngon_ngu=ngon_ngu, prompt=prompt)
        if last.get("ok"):
            return last
    if groq:
        mdl = STT_MODEL_CHUAN if prefer_quality else STT_MODEL_MAC_DINH
        last = await groq_nghe(data, ten_file, groq, model=mdl, ngon_ngu=ngon_ngu, prompt=prompt)
        if last.get("ok"):
            return last
    return last or {"ok": False, "ly_do": "loi", "noi_voi_javis": loi_thanh_dong("loi")}
