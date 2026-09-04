"""Render short video từ kịch bản cố định - chạy TRONG Javis (không cần Pixelle).

Pipeline: tách cảnh → Edge-TTS (vi-VN) → khung chữ Pillow → ffmpeg ghép mp4.
Mục tiêu: LUÔN ra được file khi có ffmpeg + mạng (Edge-TTS) - không phụ thuộc
RunningHub/Comfy/Pixelle :8000.
"""
from __future__ import annotations

import asyncio
import re
import shutil
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---- kích thước ----
_SIZES = {
    "portrait": (1080, 1920),
    "landscape": (1920, 1080),
    "square": (1080, 1080),
}

_DEFAULT_VOICE = "vi-VN-HoaiMyNeural"
_MAX_SCENES = 20
_MAX_CHARS_SCENE = 280


def tach_canh(script: str) -> List[str]:
    """Tách kịch bản thành các cảnh. Ưu tiên đoạn trống; không có thì theo dòng."""
    raw = (script or "").replace("\r\n", "\n").strip()
    if not raw:
        return []
    if "\n\n" in raw:
        parts = re.split(r"\n\s*\n+", raw)
    else:
        parts = raw.split("\n")
    out = []
    for p in parts:
        t = re.sub(r"\s+", " ", p).strip()
        if not t:
            continue
        if len(t) > _MAX_CHARS_SCENE:
            t = t[: _MAX_CHARS_SCENE - 1].rstrip() + "…"
        out.append(t)
        if len(out) >= _MAX_SCENES:
            break
    return out


def _font_path() -> Optional[str]:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for c in candidates:
        if Path(c).is_file():
            return c
    return None


def _wrap_text(draw, text: str, font, max_width: int) -> List[str]:
    words = text.split()
    if not words:
        return [""]
    lines: List[str] = []
    cur = words[0]
    for w in words[1:]:
        trial = cur + " " + w
        bbox = draw.textbbox((0, 0), trial, font=font)
        if bbox[2] - bbox[0] <= max_width:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def ve_khung(text: str, size: Tuple[int, int], title: str = "",
             bg: Tuple[int, int, int] = (18, 24, 38),
             fg: Tuple[int, int, int] = (245, 247, 250),
             accent: Tuple[int, int, int] = (56, 189, 248)) -> "Image.Image":
    from PIL import Image, ImageDraw, ImageFont

    w, h = size
    img = Image.new("RGB", (w, h), bg)
    draw = ImageDraw.Draw(img)
    # Dải accent trên
    draw.rectangle([0, 0, w, max(12, h // 80)], fill=accent)

    fp = _font_path()
    title_size = max(36, w // 22)
    body_size = max(42, w // 18)
    if fp:
        font_title = ImageFont.truetype(fp, title_size)
        font_body = ImageFont.truetype(fp, body_size)
    else:
        font_title = ImageFont.load_default()
        font_body = ImageFont.load_default()

    pad = w // 12
    max_w = w - 2 * pad
    y = h // 6
    if title:
        for line in _wrap_text(draw, title, font_title, max_w)[:2]:
            bbox = draw.textbbox((0, 0), line, font=font_title)
            tw = bbox[2] - bbox[0]
            draw.text(((w - tw) // 2, y), line, font=font_title, fill=accent)
            y += (bbox[3] - bbox[1]) + 16
        y += h // 40

    lines = _wrap_text(draw, text, font_body, max_w)
    # Căn giữa khối chữ theo chiều dọc phần còn lại
    line_h = 0
    heights = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font_body)
        lh = bbox[3] - bbox[1]
        heights.append(lh)
        line_h += lh + 18
    start_y = max(y, (h - line_h) // 2)
    cy = start_y
    for line, lh in zip(lines, heights):
        bbox = draw.textbbox((0, 0), line, font=font_body)
        tw = bbox[2] - bbox[0]
        draw.text(((w - tw) // 2, cy), line, font=font_body, fill=fg)
        cy += lh + 18
    return img


async def _tts_file(text: str, dest: Path, voice: str) -> None:
    import edge_tts
    communicate = edge_tts.Communicate(text, voice=voice)
    await communicate.save(str(dest))


def _ffprobe_duration(path: Path) -> float:
    try:
        out = subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
        return max(0.8, float(out or "0") or 0.8)
    except Exception:
        return 3.0


def _run_ffmpeg(args: List[str]) -> None:
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout or "ffmpeg lỗi")[-800:])


async def render_script_video(
    *,
    script: str,
    title: str = "",
    vault_root: str = "",
    aspect: str = "portrait",
    voice: str = "",
    filename: str = "",
) -> Dict[str, Any]:
    """Render mp4 từ kịch bản. Trả {ok, rel_path, path, scenes, error?}."""
    if not shutil.which("ffmpeg"):
        return {"ok": False, "error": "Máy chưa có ffmpeg - cần cài để ghép video."}
    scenes = tach_canh(script)
    if not scenes:
        return {"ok": False, "error": "Kịch bản trống - cần ít nhất 1 câu/cảnh."}
    if len(scenes) > _MAX_SCENES:
        scenes = scenes[:_MAX_SCENES]

    size = _SIZES.get((aspect or "portrait").lower(), _SIZES["portrait"])
    voice = (voice or _DEFAULT_VOICE).strip() or _DEFAULT_VOICE
    root = Path(vault_root) if vault_root else Path(".")
    att = root / "attachments"
    att.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", (filename or title or "video").lower()).strip("-")[:40] or "video"
    out_name = f"{time.strftime('%Y-%m-%d')}_{slug}_{uuid.uuid4().hex[:6]}.mp4"
    out_path = att / out_name

    work = Path(tempfile.mkdtemp(prefix="javis-svideo-"))
    try:
        clip_paths: List[Path] = []
        for i, line in enumerate(scenes):
            audio = work / f"a{i:02d}.mp3"
            await _tts_file(line, audio, voice)
            dur = _ffprobe_duration(audio) + 0.35  # nghỉ ngắn cuối cảnh
            frame = work / f"f{i:02d}.png"
            show_title = title if i == 0 else ""
            ve_khung(line, size, title=show_title).save(frame, "PNG")
            clip = work / f"c{i:02d}.mp4"
            # loop ảnh + audio, scale đúng size, yuv420p
            _run_ffmpeg([
                "ffmpeg", "-y",
                "-loop", "1", "-i", str(frame),
                "-i", str(audio),
                "-c:v", "libx264", "-tune", "stillimage",
                "-c:a", "aac", "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                "-shortest",
                "-t", f"{dur:.3f}",
                "-vf", f"scale={size[0]}:{size[1]}",
                str(clip),
            ])
            clip_paths.append(clip)

        lst = work / "list.txt"
        lst.write_text("".join(f"file '{p}'\n" for p in clip_paths), encoding="utf-8")
        _run_ffmpeg([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(lst), "-c", "copy", str(out_path),
        ])
        rel = f"attachments/{out_name}"
        return {
            "ok": True,
            "rel_path": rel,
            "path": str(out_path),
            "scenes": len(scenes),
            "aspect": f"{size[0]}x{size[1]}",
            "voice": voice,
            "title": title or "",
        }
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}
    finally:
        shutil.rmtree(work, ignore_errors=True)


def render_script_video_sync(**kw) -> Dict[str, Any]:
    return asyncio.run(render_script_video(**kw))
