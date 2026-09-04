"""Plugin bundled: render mp4 từ kịch bản (Edge-TTS + ffmpeg) cho mọi engine.

Tool javis_render_script_video - đường CHẮC CHẮN ra video khi thiếu Pixelle :8000.
min_mode=safe vì tạo file + gọi Edge-TTS mạng.
"""
from __future__ import annotations

import script_video as sv


def register(ctx):
    def _check():
        import shutil
        if not shutil.which("ffmpeg"):
            return "Máy chưa có ffmpeg - image Docker Javis đã có; nếu chạy local hãy cài ffmpeg."
        return None

    async def _render(args, cctx):
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

    ctx.register_tool(
        name="javis_render_script_video",
        description=(
            "Render VIDEO mp4 từ kịch bản chữ (Edge-TTS tiếng Việt + khung chữ + ffmpeg). "
            "KHÔNG cần Pixelle. Tham số: script (bắt buộc, mỗi cảnh một đoạn), title, "
            "aspect (portrait|landscape|square), voice (vd vi-VN-HoaiMyNeural / vi-VN-NamMinhNeural). "
            "Sau khi gọi, đưa đường dẫn attachments/... cho user."
        ),
        handler=_render,
        min_mode="safe",
        check_fn=_check,
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
