"""OpenMAIC path helpers — khớp lop-hoc.md khi slug lệch / thiếu tiền tố."""
from __future__ import annotations

from pathlib import Path


def score_lop_hoc_candidates(
    wanted: str, candidates: list[str]
) -> list[tuple[int, str]]:
    """Chấm điểm path lop-hoc.md gần đúng (slug thiếu tiền tố / typo)."""
    wanted_l = (wanted or "").lower().replace("\\", "/").lstrip("/")
    needle = Path(wanted_l).name
    parent_hint = Path(wanted_l).parent.name if "/" in wanted_l else ""
    found: list[tuple[int, str]] = []
    for rel in candidates:
        low = (rel or "").lower().replace("\\", "/")
        folder = Path(low).parent.name
        score = 0
        if needle and needle in low:
            score += 2
        if parent_hint:
            if folder == parent_hint:
                score += 10
            elif folder.endswith("-" + parent_hint) or parent_hint in folder:
                # marketing-thuc-chien → digital-marketing-thuc-chien
                score += 6
            elif parent_hint in low:
                score += 3
        if "marketing" in low and "marketign" in wanted_l:
            score += 4
        if score or low.endswith("/lop-hoc.md"):
            found.append((score, rel))
    found.sort(key=lambda x: (-x[0], x[1]))
    return found


def pick_best_lop_hoc(wanted: str, candidates: list[str]) -> str | None:
    """Chọn 1 path rõ ràng hơn các path khác; không đoán khi hòa điểm."""
    ranked = score_lop_hoc_candidates(wanted, candidates)
    if not ranked:
        return None
    best_s, best_r = ranked[0]
    # Cần khớp slug (suffix/prefix) — không lấy chỉ vì cùng tên file lop-hoc.md (+2).
    if best_s < 6:
        return None
    if len(ranked) > 1 and ranked[1][0] >= best_s:
        return None
    if len(ranked) > 1 and best_s - ranked[1][0] < 2:
        return None
    return best_r
