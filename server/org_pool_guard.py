"""Rate-limit + concurrency cho API pool trường (manager proxy /org/pool/*/chat).

Mỗi tenant (slug) có trần RPM và số lệnh song song; toàn hệ thống có trần global.
Cấu hình qua env (số nguyên dương):

  JAVIS_ORG_POOL_RPM                 mặc định 40  (lệnh / phút / máy)
  JAVIS_ORG_POOL_CONCURRENCY         mặc định 2   (song song / máy)
  JAVIS_ORG_POOL_GLOBAL_CONCURRENCY  mặc định 12  (song song toàn pool)
"""
from __future__ import annotations

import os
import threading
import time
from collections import defaultdict, deque

_LOCK = threading.Lock()
_HITS: dict[str, deque[float]] = defaultdict(deque)
_INFLIGHT: dict[str, int] = defaultdict(int)
_GLOBAL = 0


def _env_int(name: str, default: int, lo: int = 1, hi: int = 10_000) -> int:
    try:
        n = int(os.getenv(name) or default)
    except (TypeError, ValueError):
        n = default
    return max(lo, min(hi, n))


def rpm_limit() -> int:
    return _env_int("JAVIS_ORG_POOL_RPM", 40, 1, 600)


def conc_limit() -> int:
    return _env_int("JAVIS_ORG_POOL_CONCURRENCY", 2, 1, 32)


def global_conc_limit() -> int:
    return _env_int("JAVIS_ORG_POOL_GLOBAL_CONCURRENCY", 12, 1, 128)


def check_rate(slug: str) -> str | None:
    """None = được gọi; str = lý do từ chối (429)."""
    key = (slug or "").strip().lower() or "?"
    now = time.time()
    lim = rpm_limit()
    with _LOCK:
        q = _HITS[key]
        while q and now - q[0] > 60.0:
            q.popleft()
        if len(q) >= lim:
            # Không nói "quá tải / hỏng" — chỉ xếp hàng, mời chờ rồi gửi lại.
            return "Đang có nhiều yêu cầu cùng lúc. Chờ vài giây rồi gửi lại nhé — hệ thống vẫn chạy bình thường."
        q.append(now)
    return None


class Inflight:
    """Giữ chỗ concurrency; nếu không lấy được chỗ thì `.ok` = False và `.error` có lý do."""

    __slots__ = ("slug", "ok", "error")

    def __init__(self, slug: str):
        self.slug = (slug or "").strip().lower() or "?"
        self.ok = False
        self.error: str | None = None

    def __enter__(self) -> "Inflight":
        global _GLOBAL
        with _LOCK:
            gmax = global_conc_limit()
            if _GLOBAL >= gmax:
                self.error = (
                    "Hàng đợi đang hơi đông. Chờ vài giây rồi thử lại nhé — "
                    "không phải lỗi, chỉ cần đợi lượt."
                )
                return self
            cmax = conc_limit()
            if _INFLIGHT[self.slug] >= cmax:
                self.error = (
                    "Máy của bạn đang xử lý lệnh trước đó. "
                    "Chờ lệnh đó xong rồi gửi tiếp nhé."
                )
                return self
            _INFLIGHT[self.slug] += 1
            _GLOBAL += 1
            self.ok = True
        return self

    def __exit__(self, *exc) -> None:
        global _GLOBAL
        if not self.ok:
            return
        # Idempotent: stream path có thể gọi từ gen.finally + BackgroundTask.
        self.ok = False
        with _LOCK:
            _INFLIGHT[self.slug] = max(0, _INFLIGHT[self.slug] - 1)
            _GLOBAL = max(0, _GLOBAL - 1)


def snapshot() -> dict:
    with _LOCK:
        return {
            "rpm_limit": rpm_limit(),
            "concurrency_limit": conc_limit(),
            "global_concurrency_limit": global_conc_limit(),
            "global_inflight": _GLOBAL,
            "per_tenant_inflight": {k: v for k, v in _INFLIGHT.items() if v > 0},
        }


# Chỉ dùng trong test.
def _reset_for_tests() -> None:
    global _GLOBAL
    with _LOCK:
        _HITS.clear()
        _INFLIGHT.clear()
        _GLOBAL = 0
