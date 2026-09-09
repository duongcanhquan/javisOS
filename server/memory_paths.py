"""Đường dẫn bộ nhớ dài hạn trong brain: chuẩn `memory/` (chữ thường).

Trên Linux (case-sensitive), AI làm theo tài liệu cũ `Memory/` dễ tạo THÊM một thư mục
song song với `memory/` đã có. App chỉ đọc `memory/` → ký ức ghi vào `Memory/` thành
"mồ côi". Module này:

- chỉ ra thư mục chuẩn
- gộp/đổi tên `Memory/` → `memory/` khi phát hiện lệch chữ hoa
- no-op trên macOS/Windows case-insensitive (iterdir chỉ thấy một tên)
"""
from __future__ import annotations

import shutil
from pathlib import Path

CANONICAL = "memory"
LEGACY = "Memory"


def dir_names(root: Path) -> set[str]:
    try:
        return {p.name for p in Path(root).iterdir() if p.is_dir()}
    except OSError:
        return set()


def both_casing_dirs(root: Path) -> bool:
    """True chỉ khi Linux (hoặc FS phân biệt hoa/thường) có CẢ `memory/` lẫn `Memory/`."""
    names = dir_names(root)
    return CANONICAL in names and LEGACY in names


def _merge_index(canonical_idx: Path, legacy_idx: Path) -> bool:
    """Gộp dòng từ MEMORY.md legacy vào canonical; không xoá dòng đã có. True nếu có ghi."""
    if not legacy_idx.is_file():
        return False
    try:
        leg = legacy_idx.read_text(encoding="utf-8")
    except OSError:
        return False
    if not canonical_idx.exists():
        try:
            canonical_idx.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(legacy_idx), str(canonical_idx))
            return True
        except OSError:
            return False
    try:
        can = canonical_idx.read_text(encoding="utf-8")
    except OSError:
        return False
    can_lines = set(can.splitlines())
    extra = [ln for ln in leg.splitlines() if ln.strip() and ln not in can_lines]
    if not extra:
        try:
            legacy_idx.unlink()
        except OSError:
            pass
        return False
    text = can.rstrip() + "\n" + "\n".join(extra) + "\n"
    try:
        canonical_idx.write_text(text, encoding="utf-8")
        legacy_idx.unlink()
    except OSError:
        return False
    return True


def _merge_legacy_into_canonical(root: Path) -> list[str]:
    """Copy/move file từ Memory/ sang memory/ (không ghi đè file đã có), rồi dọn Memory/."""
    root = Path(root)
    canonical = root / CANONICAL
    legacy = root / LEGACY
    actions: list[str] = []
    if not legacy.is_dir():
        return actions
    canonical.mkdir(parents=True, exist_ok=True)

    # MEMORY.md: gộp dòng thay vì bỏ qua khi đích đã có
    if (legacy / "MEMORY.md").is_file():
        if _merge_index(canonical / "MEMORY.md", legacy / "MEMORY.md"):
            actions.append("gộp Memory/MEMORY.md → memory/MEMORY.md")

    for src in sorted(legacy.rglob("*")):
        if not src.is_file():
            continue
        rel = src.relative_to(legacy)
        if str(rel) == "MEMORY.md":
            continue
        dst = canonical / rel
        if dst.exists():
            # Giữ bản canonical; đổi tên legacy thành .from-Memory để không mất dữ liệu
            alt = dst.with_name(dst.name + ".from-Memory")
            n = 1
            while alt.exists():
                alt = dst.with_name(f"{dst.name}.from-Memory{n}")
                n += 1
            try:
                alt.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(alt))
                actions.append(f"Memory/{rel} → memory/{alt.relative_to(canonical)} (trùng tên)")
            except OSError as e:
                actions.append(f"bỏ Memory/{rel}: {e}")
            continue
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            actions.append(f"Memory/{rel} → memory/{rel}")
        except OSError as e:
            actions.append(f"bỏ Memory/{rel}: {e}")

    # Xoá thư mục legacy còn trống (đi từ dưới lên)
    try:
        for d in sorted((p for p in legacy.rglob("*") if p.is_dir()),
                        key=lambda p: len(p.parts), reverse=True):
            try:
                d.rmdir()
            except OSError:
                pass
        legacy.rmdir()
        actions.append("xoá Memory/ (đã gộp)")
    except OSError:
        # Còn file sót → để nguyên, lần sau reconcile tiếp
        if any(legacy.rglob("*")):
            actions.append("Memory/ còn sót (sẽ gộp lần sau)")
        else:
            try:
                legacy.rmdir()
                actions.append("xoá Memory/ (đã gộp)")
            except OSError:
                pass
    return actions


def reconcile_memory_dir(root: Path) -> list[str]:
    """Đảm bảo dùng memory/. Gộp hoặc đổi tên Memory/ khi cần. Trả về danh sách việc đã làm."""
    root = Path(root)
    if not root.is_dir():
        return []
    if both_casing_dirs(root):
        return _merge_legacy_into_canonical(root)
    names = dir_names(root)
    if LEGACY in names and CANONICAL not in names:
        src, dst = root / LEGACY, root / CANONICAL
        try:
            src.rename(dst)
            return [f"{LEGACY}/ → {CANONICAL}/ (đổi tên)"]
        except OSError as e:
            return [f"đổi tên Memory/ lỗi: {e}"]
    return []


def memory_dir(root: Path) -> Path:
    """Trả về thư mục memory chuẩn (sau khi reconcile). Caller tạo facts/conversations nếu cần."""
    root = Path(root)
    try:
        reconcile_memory_dir(root)
    except Exception:
        pass
    can = root / CANONICAL
    if can.is_dir():
        return can
    leg = root / LEGACY
    if leg.is_dir():
        return leg
    return can
