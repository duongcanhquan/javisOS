"""Render short video từ kịch bản - chạy TRONG Javis.

Pipeline đầy đủ:
  tách cảnh → (tuỳ chọn) ảnh AI ChatGPT từng cảnh → Edge-TTS → overlay chữ → ffmpeg → mp4

Không phụ thuộc Pixelle/RunningHub. Thiếu ChatGPT OAuth thì vẫn ra video khung chữ.
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

_SIZES = {
    "portrait": (1080, 1920),
    "landscape": (1920, 1080),
    "square": (1080, 1080),
}

_DEFAULT_VOICE = "vi-VN-HoaiMyNeural"
_MAX_SCENES = 20
_MAX_CHARS_SCENE = 280
_DEFAULT_STYLE = (
    "Vertical marketing still for Vietnamese education brand, photorealistic, "
    "bright campus and students, modern classroom or workshop, NO text, NO watermark, "
    "cinematic lighting, clean composition"
)


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


def prompt_anh(narration: str, style: str = "") -> str:
    """Prompt tiếng Anh cho ảnh cảnh - không nhúng chữ Việt vào ảnh (overlay sau)."""
    st = (style or _DEFAULT_STYLE).strip()
    nar = re.sub(r"\s+", " ", (narration or "").strip())[:180]
    return (
        f"{st}. Scene idea (illustrate visually, do not render any letters or logos): {nar}"
    )


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
             accent: Tuple[int, int, int] = (56, 189, 248),
             bg_image: Optional[str] = None) -> "Image.Image":
    """Khung chữ thuần hoặc overlay chữ lên ảnh nền (đầy đủ)."""
    from PIL import Image, ImageDraw, ImageFont, ImageEnhance

    w, h = size
    if bg_image and Path(bg_image).is_file():
        base = Image.open(bg_image).convert("RGB")
        # cover-crop về đúng size
        bw, bh = base.size
        scale = max(w / bw, h / bh)
        nw, nh = int(bw * scale), int(bh * scale)
        base = base.resize((nw, nh), Image.Resampling.LANCZOS)
        left, top = (nw - w) // 2, (nh - h) // 2
        img = base.crop((left, top, left + w, top + h))
        # tối nhẹ để chữ đọc được
        img = ImageEnhance.Brightness(img).enhance(0.72)
    else:
        img = Image.new("RGB", (w, h), bg)

    draw = ImageDraw.Draw(img, "RGBA") if False else ImageDraw.Draw(img)
    # Thanh gradient tối dưới (vẽ bằng layer)
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    band_top = int(h * 0.52)
    for y in range(band_top, h):
        a = int(40 + 180 * ((y - band_top) / max(1, h - band_top)))
        od.line([(0, y), (w, y)], fill=(0, 0, 0, min(220, a)))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Dải accent trên
    draw.rectangle([0, 0, w, max(12, h // 80)], fill=accent)

    fp = _font_path()
    title_size = max(34, w // 24)
    body_size = max(40, w // 20)
    if fp:
        font_title = ImageFont.truetype(fp, title_size)
        font_body = ImageFont.truetype(fp, body_size)
    else:
        font_title = ImageFont.load_default()
        font_body = ImageFont.load_default()

    pad = w // 12
    max_w = w - 2 * pad
    y = max(40, h // 18)
    if title:
        for line in _wrap_text(draw, title, font_title, max_w)[:2]:
            bbox = draw.textbbox((0, 0), line, font=font_title)
            tw = bbox[2] - bbox[0]
            # bóng chữ
            draw.text(((w - tw) // 2 + 2, y + 2), line, font=font_title, fill=(0, 0, 0))
            draw.text(((w - tw) // 2, y), line, font=font_title, fill=accent)
            y += (bbox[3] - bbox[1]) + 14

    lines = _wrap_text(draw, text, font_body, max_w)
    heights = []
    line_h = 0
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font_body)
        lh = bbox[3] - bbox[1]
        heights.append(lh)
        line_h += lh + 16
    # Chữ nằm nửa dưới
    start_y = max(int(h * 0.58), h - line_h - h // 10)
    cy = start_y
    for line, lh in zip(lines, heights):
        bbox = draw.textbbox((0, 0), line, font=font_body)
        tw = bbox[2] - bbox[0]
        draw.text(((w - tw) // 2 + 2, cy + 2), line, font=font_body, fill=(0, 0, 0))
        draw.text(((w - tw) // 2, cy), line, font=font_body, fill=fg)
        cy += lh + 16
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


def _chatgpt_san_sang() -> bool:
    try:
        import openai_oauth
        c = openai_oauth.valid_creds()
        return bool(c and c.get("access_token"))
    except Exception:
        return False


async def _gen_anh_canh(narration: str, vault_root: str, aspect: str,
                        quality: str, style: str) -> Optional[str]:
    """Tạo ảnh AI cho 1 cảnh. Trả abs_path hoặc None."""
    try:
        import image_gen
        ar = "portrait" if aspect == "portrait" else (
            "landscape" if aspect == "landscape" else "square")
        res = await image_gen.generate_chatgpt(
            prompt_anh(narration, style),
            aspect_ratio=ar,
            quality=quality,
            vault_root=vault_root or None,
        )
        if res.get("ok") and res.get("abs_path"):
            return str(res["abs_path"])
    except Exception:
        return None
    return None


async def render_script_video(
    *,
    script: str,
    title: str = "",
    vault_root: str = "",
    aspect: str = "portrait",
    voice: str = "",
    filename: str = "",
    with_images: bool = True,
    image_quality: str = "low",
    image_style: str = "",
) -> Dict[str, Any]:
    """Render mp4 từ kịch bản. with_images=True → ảnh AI từng cảnh (ChatGPT OAuth)."""
    if not shutil.which("ffmpeg"):
        return {"ok": False, "error": "Máy chưa có ffmpeg - cần cài để ghép video."}
    scenes = tach_canh(script)
    if not scenes:
        return {"ok": False, "error": "Kịch bản trống - cần ít nhất 1 câu/cảnh."}
    if len(scenes) > _MAX_SCENES:
        scenes = scenes[:_MAX_SCENES]

    size = _SIZES.get((aspect or "portrait").lower(), _SIZES["portrait"])
    aspect_key = (aspect or "portrait").lower()
    if aspect_key not in _SIZES:
        aspect_key = "portrait"
    voice = (voice or _DEFAULT_VOICE).strip() or _DEFAULT_VOICE
    root = Path(vault_root) if vault_root else Path(".")
    att = root / "attachments"
    att.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", (filename or title or "video").lower()).strip("-")[:40] or "video"
    out_name = f"{time.strftime('%Y-%m-%d')}_{slug}_{uuid.uuid4().hex[:6]}.mp4"
    out_path = att / out_name

    want_images = bool(with_images)
    images_ok = 0
    images_skip_reason = ""
    if want_images and not _chatgpt_san_sang():
        want_images = False
        images_skip_reason = "Chưa kết nối ChatGPT OAuth - fallback khung chữ."

    work = Path(tempfile.mkdtemp(prefix="javis-svideo-"))
    try:
        clip_paths: List[Path] = []
        for i, line in enumerate(scenes):
            audio = work / f"a{i:02d}.mp3"
            await _tts_file(line, audio, voice)
            dur = _ffprobe_duration(audio) + 0.35

            bg_path = None
            if want_images:
                bg_path = await _gen_anh_canh(
                    line, str(root), aspect_key, image_quality or "low", image_style)
                if bg_path:
                    images_ok += 1

            frame = work / f"f{i:02d}.png"
            show_title = title if i == 0 else ""
            ve_khung(line, size, title=show_title, bg_image=bg_path).save(frame, "PNG")
            clip = work / f"c{i:02d}.mp4"
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
            "images": images_ok,
            "with_images": bool(with_images),
            "images_note": images_skip_reason or (
                f"{images_ok}/{len(scenes)} cảnh có ảnh AI" if with_images else "tắt ảnh AI"
            ),
        }
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}
    finally:
        shutil.rmtree(work, ignore_errors=True)


def render_script_video_sync(**kw) -> Dict[str, Any]:
    return asyncio.run(render_script_video(**kw))
