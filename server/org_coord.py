"""Điều phối RAM: trần chỗ theo RAM máy, idle, hàng đợi. Không đụng volume."""
from __future__ import annotations

import os
import threading
import time
from pathlib import Path

import org_tenants as ot

RAM_MB = 768
MAX_RUNNING_DEFAULT = 6
IDLE_MINUTES_DEFAULT = 30
PARK_NAME = "javis-park"
# Gốc + Quan + Docker + OS + Caddy. Máy 6 GB còn chỗ cho ~3 Javis người.
RESERVE_MB = 2800
KEEP_FREE_MB = 400
AUTO_CAP = 8
PRESSURE_IDLE_SEC = 90
# Khi có người xếp hàng: máy nghỉ tối thiểu lâu thế này mới bị nhường chỗ (giây).
HANDOFF_MIN_SEC = 90
HANDOFF_CAP_SEC = 120


def idle_sec(idle_minutes: int | None = None) -> int:
    """Số giây vắng theo cài đặt «Tự tắt sau». 0 = không tự tắt định kỳ. Sàn 1 phút nếu >0."""
    if idle_minutes is None:
        idle_minutes = int(_stored()["idle_minutes"])
    try:
        m = int(idle_minutes or 0)
    except (TypeError, ValueError):
        m = 0
    if m <= 0:
        return 0
    return max(60, m * 60)


def evict_grace_sec(pressure: bool = False, idle_minutes: int | None = None) -> int:
    """Thời gian vắng tối thiểu trước khi tắt máy để nhường chỗ / hạ trần.

    Tôn trọng phút user cài (sàn 1 phút). Trước đây sàn cứng 5 phút nên để 5
    phút vẫn đúng, nhưng để 1-4 phút thì bị bỏ qua.
    """
    if pressure:
        return PRESSURE_IDLE_SEC
    sec = idle_sec(idle_minutes)
    if sec <= 0:
        # Không tự tắt định kỳ: khi hết chỗ vẫn có thể nhường máy nghỉ lâu (>15 phút).
        return 15 * 60
    return sec


def handoff_grace_sec(idle_minutes: int | None = None) -> int:
    """Khi có người xếp hàng hoặc cần nhường chỗ gấp: máy nghỉ sớm hơn vẫn được nhả.

    Ưu tiên người đang/vừa dùng (không đá dưới HANDOFF_MIN_SEC). Máy nghỉ lâu hơn
    mức này nhường cho người trong hàng đợi - linh hoạt RAM.
    """
    sec = idle_sec(idle_minutes)
    if sec <= 0:
        return PRESSURE_IDLE_SEC
    return max(HANDOFF_MIN_SEC, min(sec, HANDOFF_CAP_SEC))


_WAIT: dict[str, float] = {}
_WLOCK = threading.Lock()
_WAIT_LOADED = False
DISK_CACHE_SEC = 120
_DISK_CACHE: dict = {"t": 0.0, "total": 0, "free": 0, "path": ""}


def _hydrate_wait() -> None:
    """Nạp hàng đợi từ org-tenants.json (sống qua restart manager)."""
    global _WAIT, _WAIT_LOADED
    with _WLOCK:
        if _WAIT_LOADED:
            return
        try:
            raw = ot.load().get("wait_queue")
            if isinstance(raw, dict):
                cleaned: dict[str, float] = {}
                for k, v in raw.items():
                    s = str(k or "").strip().lower()
                    if not s:
                        continue
                    try:
                        cleaned[s] = float(v)
                    except (TypeError, ValueError):
                        cleaned[s] = time.time()
                _WAIT = cleaned
        except Exception:
            _WAIT = {}
        _WAIT_LOADED = True


def _save_wait_snap(snap: dict) -> None:
    try:
        data = ot.load()
        data["wait_queue"] = snap
        ot.save(data)
    except Exception as e:
        print(f"[org coord] không lưu hàng đợi: {e}", flush=True)


def _meminfo_mb() -> tuple[int, int]:
    total = 0
    avail = 0
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("MemTotal:"):
                total = int(line.split()[1]) // 1024
            elif line.startswith("MemAvailable:"):
                avail = int(line.split()[1]) // 1024
            if total and avail:
                break
    except Exception:
        return 0, 0
    return max(0, total), max(0, avail)


def host_mem_mb() -> tuple[int, int]:
    """(tổng MB, còn trống MB). 0,0 nếu không đọc được."""
    return _meminfo_mb()


def _disk_probe_path() -> str:
    """Ưu tiên ổ chứa STATE_DIR (não / sổ tổ chức), fallback /."""
    try:
        import config as cfgmod
        p = Path(cfgmod.STATE_DIR)
        p.mkdir(parents=True, exist_ok=True)
        return str(p.resolve())
    except Exception:
        return "/"


def host_disk_bytes(path: str | None = None) -> tuple[int, int, str]:
    """(tổng byte, còn trống byte, path đã đo). Cache ngắn để khỏi gọi statvfs mỗi request."""
    now = time.time()
    want = (path or "").strip() or _disk_probe_path()
    cached_path = str(_DISK_CACHE.get("path") or "")
    if (cached_path == want
            and now - float(_DISK_CACHE.get("t") or 0) < DISK_CACHE_SEC
            and int(_DISK_CACHE.get("total") or 0) > 0):
        return int(_DISK_CACHE["total"]), int(_DISK_CACHE["free"]), cached_path
    total = free = 0
    used_path = want
    for cand in (want, "/", "/data", "/brains"):
        try:
            st = os.statvfs(cand)
            tot = int(st.f_blocks) * int(st.f_frsize)
            fr = int(st.f_bavail) * int(st.f_frsize)
            if tot > 0:
                total, free, used_path = tot, fr, cand
                break
        except Exception:
            continue
    _DISK_CACHE["t"] = now
    _DISK_CACHE["total"] = total
    _DISK_CACHE["free"] = free
    _DISK_CACHE["path"] = used_path
    return total, free, used_path


def host_cpus() -> int:
    try:
        n = int(os.cpu_count() or 0)
    except Exception:
        n = 0
    return max(0, n)


def suggest_slots(total_mb: int) -> int:
    """Số chỗ Javis người an toàn từ RAM máy. Không đếm gốc và Quan."""
    try:
        t = int(total_mb or 0)
    except (TypeError, ValueError):
        t = 0
    room = t - RESERVE_MB - KEEP_FREE_MB
    n = room // RAM_MB
    return max(1, min(AUTO_CAP, n))


def _stored(data: dict | None = None) -> dict:
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
    return {"max_running": max(1, min(20, max_r)), "idle_minutes": max(0, min(24 * 60, idle))}


def effective_max(data: dict | None = None, total_mb: int | None = None) -> int:
    """Trần đang dùng: min(trần tay, chỗ RAM thật)."""
    hand = int(_stored(data)["max_running"])
    tot = int(total_mb) if total_mb is not None else host_mem_mb()[0]
    if tot < 512:
        return hand
    return max(1, min(hand, suggest_slots(tot)))


def coord(data: dict | None = None) -> dict:
    raw = data if isinstance(data, dict) else None
    s = _stored(raw)
    tot, avail = host_mem_mb()
    mx = effective_max(raw, tot if tot else None)
    disk_tot, disk_free, disk_path = host_disk_bytes()
    return {
        "max_running": s["max_running"],
        "idle_minutes": s["idle_minutes"],
        "ram_mb": RAM_MB,
        "reserve_mb": RESERVE_MB,
        "keep_free_mb": KEEP_FREE_MB,
        "effective_max": mx,
        "host_ram_mb": tot,
        "host_avail_mb": avail,
        "host_disk_total_bytes": disk_tot,
        "host_disk_free_bytes": disk_free,
        "host_disk_path": disk_path,
        "host_cpus": host_cpus(),
        "suggest": suggest_slots(tot) if tot else s["max_running"],
    }


def put_coord(max_running: int | None = None, idle_minutes: int | None = None) -> dict:
    data = ot.load()
    cur = _stored(data)
    if max_running is not None:
        cur["max_running"] = max(1, min(20, int(max_running)))
    if idle_minutes is not None:
        cur["idle_minutes"] = max(0, min(24 * 60, int(idle_minutes)))
    data["coord"] = {"max_running": cur["max_running"], "idle_minutes": cur["idle_minutes"]}
    _hydrate_wait()
    with _WLOCK:
        data["wait_queue"] = dict(_WAIT)
    ot.save(data)
    return coord(data)


def enqueue_wait(slug: str) -> int:
    s = (slug or "").strip().lower()
    if not s:
        return 0
    _hydrate_wait()
    with _WLOCK:
        _WAIT.setdefault(s, time.time())
        order = sorted(_WAIT, key=lambda k: _WAIT[k])
        pos = order.index(s) + 1
        snap = dict(_WAIT)
    _save_wait_snap(snap)
    return pos


def clear_wait(slug: str) -> None:
    s = (slug or "").strip().lower()
    _hydrate_wait()
    with _WLOCK:
        if s not in _WAIT:
            return
        _WAIT.pop(s, None)
        snap = dict(_WAIT)
    _save_wait_snap(snap)


def peek_waiter() -> str:
    _hydrate_wait()
    with _WLOCK:
        if not _WAIT:
            return ""
        return sorted(_WAIT, key=lambda k: _WAIT[k])[0]


def next_waiter() -> str:
    """Lấy người đầu hàng và xóa khỏi hàng. Dùng sau khi bật máy xong."""
    _hydrate_wait()
    with _WLOCK:
        if not _WAIT:
            return ""
        order = sorted(_WAIT, key=lambda k: _WAIT[k])
        s = order[0]
        _WAIT.pop(s, None)
        snap = dict(_WAIT)
    _save_wait_snap(snap)
    return s


def wait_len() -> int:
    _hydrate_wait()
    with _WLOCK:
        return len(_WAIT)


def slug_from_host(host: str) -> str:
    h = (host or "").split(":")[0].strip().lower()
    suf = "." + ot.domain_suffix()
    if not h.endswith(suf):
        return ""
    left = h[: -len(suf)]
    prefixes = [ot.host_prefix() + "-"]
    if "javis-" not in prefixes:
        prefixes.append("javis-")
    slug = ""
    for pre in prefixes:
        if left.startswith(pre):
            slug = left[len(pre):]
            break
    if not slug or ot.validate_slug(slug):
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


def snapshot(running: int, max_running: int | None = None, idle_minutes: int | None = None,
             ram_live: dict | None = None) -> dict:
    c = coord()
    n = max(0, int(running))
    idle = int(idle_minutes if idle_minutes is not None else c["idle_minutes"])
    hand = int(max_running if max_running is not None else c["max_running"])
    tot = int(c.get("host_ram_mb") or 0)
    if tot >= 512:
        eff = max(1, min(hand, suggest_slots(tot)))
    else:
        eff = hand
    live = ram_live if isinstance(ram_live, dict) else {}
    out = {
        "max_running": hand,
        "effective_max": eff,
        "idle_minutes": idle,
        "running": n,
        "waiting": wait_len(),
        "ram_mb": RAM_MB,
        "reserve_mb": RESERVE_MB,
        "keep_free_mb": KEEP_FREE_MB,
        "ram_est_mb": n * RAM_MB,
        "slots_left": max(0, eff - n),
        "host_ram_mb": tot,
        "host_avail_mb": int(c.get("host_avail_mb") or 0),
        "host_disk_total_bytes": int(c.get("host_disk_total_bytes") or 0),
        "host_disk_free_bytes": int(c.get("host_disk_free_bytes") or 0),
        "host_disk_path": str(c.get("host_disk_path") or ""),
        "host_cpus": int(c.get("host_cpus") or 0),
        "suggest": int(c.get("suggest") or hand),
        # Công thức cho UI: ngân sách máy người trên host
        "budget_people_mb": max(0, tot - RESERVE_MB - KEEP_FREE_MB) if tot else 0,
        "formula": (
            f"(RAM host - chừa {RESERVE_MB}MB gốc/Quan/OS - giữ trống {KEEP_FREE_MB}MB) "
            f"/ {RAM_MB}MB mỗi máy, trần {AUTO_CAP}"
        ),
    }
    if live:
        out["ram_live"] = live
        # Chỗ còn theo RAM thật: trống host + có thể lấy lại từ máy nghỉ
        try:
            fit = int(live.get("fit_more_est") or 0)
            out["slots_by_ram"] = max(0, fit)
            out["people_used_mb"] = int(live.get("people_used_mb") or 0)
            out["people_idle_mb"] = int(live.get("people_idle_mb") or 0)
            out["people_active_n"] = int(live.get("people_active_n") or 0)
            out["people_idle_n"] = int(live.get("people_idle_n") or 0)
        except (TypeError, ValueError):
            pass
    return out


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
