# -*- coding: utf-8 -*-
"""ZeroTTS (zeroweight-ai) - nhà cung cấp TTS tiếng Việt tuỳ chọn.

Không nằm trong requirements.txt: gói kéo onnxruntime + tải ~900MB weights lần đầu.
Cài khi cần: `pip install zerotts`. Thiếu gói / lỗi sinh giọng → caller fallback Edge.

API công khai chỉ dùng stdlib + lazy import zerotts, để `import main` vẫn nhẹ
(test_khoi_dong_nhe). Không promise nhân bản giọng từ audio: encoder chưa mở nguồn;
chỉ dùng preset (maichi, …) hoặc zip latent đã có sẵn trên máy.
"""
from __future__ import annotations

import asyncio
import io
import os
import sys
import threading
import wave
from typing import Any

# Preset kèm weights (docs/VOICES.md). UI hiện list này cả khi chưa cài gói.
PRESET_VOICES: list[dict[str, str]] = [
    {"id": "maichi", "name": "Mai Chi", "gender": "nu",
     "tags": "tre, ke chuyen, nhe nhang"},
    {"id": "baotrang", "name": "Bao Trang", "gender": "nu",
     "tags": "truong thanh, tin tuc, ro rang"},
    {"id": "kimoanh", "name": "Kim Oanh", "gender": "nu",
     "tags": "trung nien, ke chuyen, am ap"},
    {"id": "hamy", "name": "Ha My", "gender": "nu",
     "tags": "tre, hoat hinh, bieu cam"},
    {"id": "giahuy", "name": "Gia Huy", "gender": "nam",
     "tags": "tre, ke chuyen, tram am"},
    {"id": "huuduc", "name": "Huu Duc", "gender": "nam",
     "tags": "lon tuoi, ke chuyen, diem dam"},
    {"id": "quangminh", "name": "Quang Minh", "gender": "nam",
     "tags": "tre, tin tuc, dut khoat"},
    {"id": "tiendat", "name": "Tien Dat", "gender": "nam",
     "tags": "tre, binh luan, soi noi"},
]

DEFAULT_VOICE = "maichi"
DEFAULT_MODEL = "zeroweight-ai/ZeroTTS"

_lock = threading.Lock()
_engine: Any = None
_load_error: str | None = None


def available() -> bool:
    """True nếu package `zerotts` import được (chưa chắc đã tải weights)."""
    if "zerotts" in sys.modules:
        return True
    try:
        import importlib.util
        return importlib.util.find_spec("zerotts") is not None
    except Exception:
        return False


def preset_voices() -> list[dict[str, str]]:
    return list(PRESET_VOICES)


def status() -> dict:
    """Trạng thái nhẹ cho GET /settings - không nạp model."""
    return {
        "available": available(),
        "loaded": _engine is not None,
        "load_error": _load_error,
        "voices": preset_voices(),
        "default_voice": DEFAULT_VOICE,
        "hint": (
            "pip install zerotts  (weights ~900MB lần đầu từ Hugging Face)"
            if not available()
            else ""
        ),
    }


def reset_engine_for_tests() -> None:
    """Chỉ dùng trong unit test."""
    global _engine, _load_error
    with _lock:
        _engine = None
        _load_error = None


def _model_id() -> str:
    return (os.environ.get("JAVIS_ZEROTTS_MODEL") or DEFAULT_MODEL).strip() or DEFAULT_MODEL


def _get_engine():
    """Nạp ZeroTTS một lần (thread-safe). Lỗi giữ lại để lần sau fail nhanh."""
    global _engine, _load_error
    with _lock:
        if _engine is not None:
            return _engine
        if _load_error:
            raise RuntimeError(_load_error)
        try:
            from zerotts import ZeroTTS  # type: ignore
            _engine = ZeroTTS.from_pretrained(_model_id())
            return _engine
        except Exception as e:
            _load_error = f"{type(e).__name__}: {e}"
            raise RuntimeError(_load_error) from e


def _looks_vietnamese(text: str) -> bool:
    return any(
        c in text
        for c in "àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ"
                 "ÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ"
    )


def _prepare_segments(text: str) -> list[str]:
    """Chuẩn hoá + cắt đoạn dài (model train theo utterance, không phải đoạn văn)."""
    raw = (text or "").strip()
    if not raw:
        return []
    normed = raw
    if _looks_vietnamese(raw):
        try:
            from zerotts import normalize_vi_text  # type: ignore
            normed = normalize_vi_text(raw) or raw
        except Exception:
            normed = raw
    try:
        from zerotts.chunking import (  # type: ignore
            chunk_text,
            clean_segment_punctuation,
            normalize_punctuation,
        )
        parts = [
            clean_segment_punctuation(s)
            for s in chunk_text(normalize_punctuation(normed), max_chunk_sec=15)
        ]
        parts = [p.strip() for p in parts if p and p.strip()]
        return parts or [normed]
    except Exception:
        # Fallback thô: cắt theo câu nếu quá dài
        if len(normed) <= 400:
            return [normed]
        out: list[str] = []
        buf = ""
        for part in normed.replace("!", ".").replace("?", ".").split("."):
            piece = part.strip()
            if not piece:
                continue
            cand = (buf + ". " + piece).strip(". ").strip()
            if buf and len(cand) > 280:
                out.append(buf)
                buf = piece
            else:
                buf = cand
        if buf:
            out.append(buf)
        return out or [normed]


def _as_float_list(audio) -> list[float]:
    """Đưa (1,T)/(T,)/list về list[float] phẳng - không bắt buộc numpy lúc test mock."""
    try:
        import numpy as np
        return np.asarray(audio, dtype="float32").reshape(-1).tolist()
    except Exception:
        if audio is None:
            return []
        if isinstance(audio, (bytes, bytearray)):
            return []
        # nested list / tuple
        out: list[float] = []
        stack = [audio]
        while stack:
            cur = stack.pop()
            if isinstance(cur, (list, tuple)):
                stack.extend(reversed(cur))
            else:
                try:
                    out.append(float(cur))
                except Exception:
                    pass
        return out


def _float_audio_to_wav_bytes(audio, sample_rate: int) -> bytes:
    """float32 [-1,1] → WAV PCM16 mono. Stdlib only (array + wave)."""
    import array
    samples = _as_float_list(audio)
    pcm = array.array("h")
    for x in samples:
        v = int(max(-1.0, min(1.0, float(x))) * 32767.0)
        if v > 32767:
            v = 32767
        elif v < -32768:
            v = -32768
        pcm.append(v)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(int(sample_rate))
        w.writeframes(pcm.tobytes())
    return buf.getvalue()


def _concat_float(chunks: list) -> list[float]:
    out: list[float] = []
    for c in chunks:
        if c is None:
            continue
        out.extend(_as_float_list(c))
    return out


def synthesize_sync(text: str, voice: str | None = None) -> tuple[bytes, str]:
    """Sinh WAV bytes. Trả (audio_bytes, media_type). Chạy sync - gọi qua to_thread."""
    if not available():
        raise RuntimeError(
            "Chưa cài ZeroTTS. Chạy: pip install zerotts "
            "(lần đầu tải ~900MB weights từ Hugging Face)."
        )
    segments = _prepare_segments(text)
    if not segments:
        raise RuntimeError("ZeroTTS: văn bản rỗng.")
    vid = (voice or "").strip() or DEFAULT_VOICE
    engine = _get_engine()
    sr = int(getattr(engine, "sample_rate", 48000) or 48000)
    waves = []
    for seg in segments:
        waves.append(engine.synthesize(seg, voice=vid))
    audio = _concat_float(waves)
    if not audio:
        raise RuntimeError("ZeroTTS trả audio rỗng.")
    return _float_audio_to_wav_bytes(audio, sr), "audio/wav"


async def synthesize(text: str, voice: str | None = None) -> tuple[bytes, str]:
    """Async wrapper - không chặn event loop bằng CPU ONNX."""
    return await asyncio.to_thread(synthesize_sync, text, voice)
