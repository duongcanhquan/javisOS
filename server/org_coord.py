"""Điều phối RAM: trần số máy chạy, idle, bóc slug từ hostname. Không đụng volume."""
from __future__ import annotations

import time
from pathlib import Path

import org_tenants as ot

RAM_MB = 768
MAX_RUNNING_DEFAULT = 6
IDLE_MINUTES_DEFAULT = 30
PARK_NAME = "javis-park"


def coord(data: dict | None = None) -> dict:
    raw = data if isinstance(data, dict) else ot.load()
    c = raw.get("coord") if isinstance(raw.get("coord"), dict) else {}
    try:
        max_r = int(c.get("max_running") if c.get("max_running") is not None else MAX_RUNNING_DEFAULT)
    except (TypeError, ValueError):
        max_r = MAX_RUNNING_DEFAULT
    try:
        idle = int(c.get("idle_minutes") if c.get("idle_minutes") is not None else IDLE_MINUTES_DEFAULT)
    except (TypeError, ValueError):
        idle = IDLE_MINUTES_DEFAULT
    max_r = max(1, min(20, max_r))
    idle = max(0, min(24 * 60, idle))
    return {"max_running": max_r, "idle_minutes": idle, "ram_mb": RAM_MB}


def put_coord(max_running: int | None = None, idle_minutes: int | None = None) -> dict:
    data = ot.load()
    cur = coord(data)
    if max_running is not None:
        cur["max_running"] = max(1, min(20, int(max_running)))
    if idle_minutes is not None:
        cur["idle_minutes"] = max(0, min(24 * 60, int(idle_minutes)))
    data["coord"] = {"max_running": cur["max_running"], "idle_minutes": cur["idle_minutes"]}
    ot.save(data)
    return coord(data)


def slug_from_host(host: str) -> str:
    h = (host or "").split(":")[0].strip().lower()
    suf = "." + ot.domain_suffix()
    if not h.endswith(suf):
        return ""
    left = h[: -len(suf)]
    pre = ot.host_prefix() + "-"
    if not left.startswith(pre):
        return ""
    slug = left[len(pre):]
    if ot.validate_slug(slug):
        return ""
    return slug


def touch_last_active() -> None:
    import config as cfgmod
    p = Path(cfgmod.STATE_DIR) / "org-last-active"
    now = time.time()
    try:
        if p.is_file() and now - p.stat().st_mtime < 60:
            return
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(str(int(now)), encoding="utf-8")
    except Exception:
        pass


def snapshot(running: int, max_running: int | None = None, idle_minutes: int | None = None) -> dict:
    c = coord()
    mx = int(max_running if max_running is not None else c["max_running"])
    idle = int(idle_minutes if idle_minutes is not None else c["idle_minutes"])
    n = max(0, int(running))
    return {
        "max_running": mx,
        "idle_minutes": idle,
        "running": n,
        "ram_mb": RAM_MB,
        "ram_est_mb": n * RAM_MB,
        "slots_left": max(0, mx - n),
    }


def wake_html(host: str, title: str, body: str, refresh: int = 4) -> str:
    h = (host or "").replace("<", "").replace(">", "").replace('"', "")
    t = (title or "").replace("<", "").replace(">", "")
    b = (body or "").replace("<", "").replace(">", "")
    try:
        r = int(refresh)
    except (TypeError, ValueError):
        r = 4
    meta = ""
    more = f'<p><a href="https://{h}/">Thử mở lại</a></p>'
    if r > 0:
        r = max(2, min(15, r))
        meta = f'<meta http-equiv="refresh" content="{r};url=https://{h}/">'
        more = f"<p>Trang tự mở lại sau {r} giây. <a href=\"https://{h}/\">Mở ngay</a></p>"
    return (
        "<!doctype html><html lang=\"vi\"><head><meta charset=\"utf-8\">"
        f"{meta}"
        f"<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        f"<title>{t}</title></head>"
        "<body style=\"font-family:sans-serif;max-width:36rem;margin:15vh auto;padding:0 16px;line-height:1.45\">"
        f"<h1 style=\"font-size:1.35rem\">{t}</h1><p>{b}</p>"
        f"{more}"
        "</body></html>"
    )
