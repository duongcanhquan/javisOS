"""Plugin bundled: render mp4 từ kịch bản.

- javis_render_script_video: Edge-TTS + ffmpeg (luôn có trong Javis)
- javis_pixelle_generate: gọi Pixelle API nếu :8000 sống; không thì fallback native
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
        res = await sv.render_script_video(
            script=script,
            title=title,
            vault_root=getattr(cctx, "vault_root", "") or "",
            aspect=aspect,
            voice=voice,
        )
        if not res.get("ok"):
            return "ERROR: " + str(res.get("error") or "render thất bại")
        rel = res["rel_path"]
        return (
            f"Đã render video {res.get('aspect')} · {res.get('scenes')} cảnh · giọng {res.get('voice')}. "
            f"File: {rel}. "
            f"HÃY NHÚNG cho user xem: [{title or 'video'}]({rel}) "
            f"(dashboard mở/tải qua /files/raw)."
        )

    async def _pixelle(args, cctx):
        args = args or {}
        script = str(args.get("script") or "").strip()
        if not script:
            return "ERROR: thiếu 'script' (mỗi cảnh một đoạn)."
        title = str(args.get("title") or "").strip() or "Javis video"
        template = str(args.get("frame_template") or "1080x1920/static_default.html").strip()
        wait = args.get("wait", True)
        if isinstance(wait, str):
            wait = wait.lower() not in ("0", "false", "no")

        h = await px.health()
        if not h.get("ok"):
            native = await _render_native({
                "script": script, "title": title, "aspect": "portrait",
            }, cctx)
            return (
                f"Pixelle chưa sẵn sàng ({h.get('error')}). "
                f"Đã fallback sang render native trong Javis:\n{native}"
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
                "script": script, "title": title, "aspect": "portrait",
            }, cctx)
            return (
                f"Pixelle lỗi: {res.get('error')}. "
                f"Đã fallback native:\n{native}"
            )
        if not wait:
            return f"Đã xếp hàng Pixelle task_id={res.get('task_id')} — poll /api/tasks/{{id}}."
        url = res.get("video_url") or ""
        return (
            f"Pixelle xong (template {template}). "
            f"task_id={res.get('task_id')}. "
            f"video_url={url or '(xem result trong task)'}. "
            f"Chi tiết: {str(res.get('result'))[:500]}"
        )

    ctx.register_tool(
        name="javis_render_script_video",
        description=(
            "Render VIDEO mp4 từ kịch bản chữ (Edge-TTS tiếng Việt + khung chữ + ffmpeg). "
            "KHÔNG cần Pixelle. Tham số: script (bắt buộc, mỗi cảnh một đoạn), title, "
            "aspect (portrait|landscape|square), voice (vd vi-VN-HoaiMyNeural / vi-VN-NamMinhNeural). "
            "Sau khi gọi, đưa đường dẫn attachments/... cho user."
        ),
        handler=_render_native,
        min_mode="safe",
        check_fn=_check_ffmpeg,
        schema={
            "type": "object",
            "properties": {
                "script": {
                    "type": "string",
                    "description": "Kịch bản: mỗi cảnh một đoạn (cách dòng trống) hoặc mỗi dòng một cảnh",
                },
                "title": {"type": "string", "description": "Tiêu đề hiện cảnh đầu (tuỳ chọn)"},
                "aspect": {
                    "type": "string",
                    "enum": ["portrait", "landscape", "square"],
                    "description": "Tỉ lệ, mặc định portrait 1080x1920",
                },
                "voice": {
                    "type": "string",
                    "description": "Edge-TTS voice, mặc định vi-VN-HoaiMyNeural",
                },
            },
            "required": ["script"],
        },
    )

    ctx.register_tool(
        name="javis_pixelle_generate",
        description=(
            "Render video qua Pixelle API (PIXELLE_API_BASE) mode=fixed. "
            "Template mặc định static_default (không cần RunningHub). "
            "Nếu Pixelle chết → tự fallback javis_render_script_video. "
            "Tham số: script, title, frame_template, prompt_prefix, wait."
        ),
        handler=_pixelle,
        min_mode="safe",
        schema={
            "type": "object",
            "properties": {
                "script": {"type": "string"},
                "title": {"type": "string"},
                "frame_template": {
                    "type": "string",
                    "description": "vd 1080x1920/static_default.html hoặc image_default.html",
                },
                "prompt_prefix": {"type": "string"},
                "wait": {"type": "boolean", "description": "Chờ xong (mặc định true)"},
                "max_wait_sec": {"type": "number"},
            },
            "required": ["script"],
        },
    )
