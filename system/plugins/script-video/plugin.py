"""Plugin bundled: render mp4 từ kịch bản (ảnh AI + TTS + ffmpeg).

- javis_render_script_video: đầy đủ (ChatGPT ảnh từng cảnh nếu đã OAuth) + Edge-TTS
- javis_pixelle_generate: Pixelle API nếu sống; không thì fallback native
"""
from __future__ import annotations

import script_video as sv
import pixelle_client as px


def register(ctx):
    def _check_ffmpeg():
        import shutil
        if not shutil.which("ffmpeg"):
            return "Máy chưa có ffmpeg - image Docker Javis đã có; nếu chạy local hãy cài ffmpeg."
        return None

    async def _render_native(args, cctx):
        args = args or {}
        script = str(args.get("script") or "").strip()
        if not script:
            return ("ERROR: thiếu 'script'. Mỗi cảnh một đoạn (cách bằng dòng trống) hoặc mỗi dòng "
                    "một cảnh. Ví dụ: 'Hook.\\n\\nÝ 2.\\n\\nCTA.'")
        title = str(args.get("title") or "").strip()
        aspect = str(args.get("aspect") or "portrait")
        voice = str(args.get("voice") or "").strip()
        with_images = args.get("with_images", True)
        if isinstance(with_images, str):
            with_images = with_images.lower() not in ("0", "false", "no")
        require_images = args.get("require_images", True)
        if isinstance(require_images, str):
            require_images = require_images.lower() not in ("0", "false", "no")
        quality = str(args.get("image_quality") or "low")
        style = str(args.get("image_style") or "").strip()
        res = await sv.render_script_video(
            script=script,
            title=title,
            vault_root=getattr(cctx, "vault_root", "") or "",
            aspect=aspect,
            voice=voice,
            with_images=bool(with_images),
            image_quality=quality,
            image_style=style,
            require_images=bool(require_images) if with_images else False,
        )
        if not res.get("ok"):
            return "ERROR: " + str(res.get("error") or "render thất bại")
        rel = res["rel_path"]
        return (
            f"Đã render video {res.get('aspect')} · {res.get('scenes')} cảnh · "
            f"giọng {res.get('voice')} · {res.get('images_note')}. "
            f"File: {rel}. "
            f"HÃY NHÚNG cho user: [{title or 'video'}]({rel})"
        )

    async def _pixelle(args, cctx):
        args = args or {}
        script = str(args.get("script") or "").strip()
        if not script:
            return "ERROR: thiếu 'script' (mỗi cảnh một đoạn)."
        title = str(args.get("title") or "").strip() or "Javis video"
        # Ưu tiên image template nếu Pixelle có RunningHub; không thì static rồi fallback native có ảnh ChatGPT
        template = str(args.get("frame_template") or "1080x1920/image_default.html").strip()
        wait = args.get("wait", True)
        if isinstance(wait, str):
            wait = wait.lower() not in ("0", "false", "no")

        h = await px.health()
        if not h.get("ok"):
            native = await _render_native({
                "script": script, "title": title, "aspect": "portrait", "with_images": True,
            }, cctx)
            return (
                f"Pixelle chưa sẵn sàng ({h.get('error')}). "
                f"Đã fallback native (ảnh ChatGPT + TTS):\n{native}"
            )

        res = await px.generate_fixed(
            text=script,
            title=title,
            frame_template=template,
            prompt_prefix=str(args.get("prompt_prefix") or ""),
            wait=bool(wait),
            max_wait_sec=float(args.get("max_wait_sec") or 600),
        )
        if not res.get("ok"):
            native = await _render_native({
                "script": script, "title": title, "aspect": "portrait", "with_images": True,
            }, cctx)
            return (
                f"Pixelle lỗi (thường do thiếu RunningHub cho image_*): {res.get('error')}. "
                f"Đã fallback native có ảnh AI:\n{native}"
            )
        if not wait:
            return f"Đã xếp hàng Pixelle task_id={res.get('task_id')}."
        url = res.get("video_url") or ""
        return (
            f"Pixelle xong (template {template}). task_id={res.get('task_id')}. "
            f"video_url={url or '(xem task)'}. {str(res.get('result'))[:400]}"
        )

    ctx.register_tool(
        name="javis_render_script_video",
        description=(
            "Render VIDEO mp4 ĐẦY ĐỦ: ảnh từng cảnh (ChatGPT hoặc Pollinations) + "
            "Edge-TTS + chữ overlay. Mặc định BẮT BUỘC có ảnh - không trả video chỉ chữ. "
            "Tham số: script, title, aspect, voice, with_images (true), require_images (true), "
            "image_quality. Sau khi gọi đưa attachments/... cho user."
        ),
        handler=_render_native,
        min_mode="safe",
        check_fn=_check_ffmpeg,
        schema={
            "type": "object",
            "properties": {
                "script": {"type": "string"},
                "title": {"type": "string"},
                "aspect": {"type": "string", "enum": ["portrait", "landscape", "square"]},
                "voice": {"type": "string"},
                "with_images": {"type": "boolean", "description": "Mặc định true"},
                "require_images": {
                    "type": "boolean",
                    "description": "Mặc định true - lỗi nếu thiếu ảnh, không trả video chữ trơn",
                },
                "image_quality": {"type": "string", "enum": ["low", "medium", "high"]},
                "image_style": {"type": "string", "description": "Prefix style ảnh tiếng Anh"},
            },
            "required": ["script"],
        },
    )

    ctx.register_tool(
        name="javis_pixelle_generate",
        description=(
            "Render qua Pixelle API mode=fixed. Thiếu RunningHub/Pixelle chết → "
            "fallback javis_render_script_video (có ảnh ChatGPT)."
        ),
        handler=_pixelle,
        min_mode="safe",
        schema={
            "type": "object",
            "properties": {
                "script": {"type": "string"},
                "title": {"type": "string"},
                "frame_template": {"type": "string"},
                "prompt_prefix": {"type": "string"},
                "wait": {"type": "boolean"},
                "max_wait_sec": {"type": "number"},
            },
            "required": ["script"],
        },
    )
