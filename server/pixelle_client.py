"""Client gọi Pixelle-Video API (nếu PIXELLE_API_BASE sống)."""
from __future__ import annotations

import asyncio
import os
import time
from typing import Any, Dict, Optional

import httpx

_DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=5.0)


def api_base() -> str:
    return (os.environ.get("PIXELLE_API_BASE") or "").strip().rstrip("/")


async def health(base: Optional[str] = None) -> Dict[str, Any]:
    b = (base or api_base()).rstrip("/")
    if not b:
        return {"ok": False, "error": "PIXELLE_API_BASE trống"}
    try:
        async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as c:
            r = await c.get(f"{b}/health")
            if r.status_code == 200:
                return {"ok": True, "base": b, "body": r.text[:200]}
            return {"ok": False, "error": f"HTTP {r.status_code}", "base": b}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}", "base": b}


async def generate_fixed(
    *,
    text: str,
    title: str = "",
    frame_template: str = "1080x1920/static_default.html",
    prompt_prefix: str = "",
    base: Optional[str] = None,
    wait: bool = True,
    poll_sec: float = 3.0,
    max_wait_sec: float = 600.0,
) -> Dict[str, Any]:
    """Gửi mode=fixed. wait=True thì poll tới completed/failed."""
    b = (base or api_base()).rstrip("/")
    if not b:
        return {"ok": False, "error": "PIXELLE_API_BASE trống - chạy setup-pixelle-vps.sh / bật profile pixelle"}
    h = await health(b)
    if not h.get("ok"):
        return {"ok": False, "error": f"Pixelle không sống: {h.get('error')}", "base": b}

    body: Dict[str, Any] = {
        "text": text,
        "mode": "fixed",
        "title": title or "Javis video",
        "frame_template": frame_template,
        "bgm_volume": 0.3,
    }
    if prompt_prefix:
        body["prompt_prefix"] = prompt_prefix

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=10.0)) as c:
            r = await c.post(f"{b}/api/video/generate/async", json=body)
            if r.status_code >= 400:
                return {"ok": False, "error": f"async HTTP {r.status_code}: {r.text[:400]}", "base": b}
            data = r.json() if r.content else {}
            task_id = data.get("task_id") or data.get("id") or (data.get("data") or {}).get("task_id")
            if not task_id:
                return {"ok": False, "error": f"Không có task_id: {str(data)[:400]}", "base": b}
            if not wait:
                return {"ok": True, "task_id": task_id, "status": "queued", "base": b}

            deadline = time.monotonic() + max_wait_sec
            last: Dict[str, Any] = {}
            while time.monotonic() < deadline:
                tr = await c.get(f"{b}/api/tasks/{task_id}")
                last = tr.json() if tr.content else {}
                st = str(last.get("status") or (last.get("data") or {}).get("status") or "").lower()
                if st in ("completed", "success", "done", "finished"):
                    result = last.get("result") or (last.get("data") or {}).get("result") or last
                    return {
                        "ok": True,
                        "task_id": task_id,
                        "status": st,
                        "result": result,
                        "base": b,
                        "video_url": (
                            (result or {}).get("video_url")
                            or (result or {}).get("url")
                            or last.get("video_url")
                        ),
                    }
                if st in ("failed", "error", "cancelled"):
                    return {
                        "ok": False,
                        "task_id": task_id,
                        "error": str(last.get("error") or last.get("message") or last)[:500],
                        "base": b,
                    }
                await asyncio.sleep(poll_sec)
            return {"ok": False, "task_id": task_id, "error": f"timeout {max_wait_sec}s", "last": last, "base": b}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}", "base": b}
