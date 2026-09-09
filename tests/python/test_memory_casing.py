"""Chuẩn memory/ (chữ thường); gộp Memory/ khi Linux tạo cả hai.

Chạy: python tests/python/test_memory_casing.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))

import memory_paths as mp  # noqa: E402

fails = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


def _case_sensitive_tmpdir():
    """True nếu FS cho phép tồn tại đồng thời memory/ và Memory/."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "memory").mkdir()
        try:
            (root / "Memory").mkdir()
        except FileExistsError:
            return False
        return mp.both_casing_dirs(root)


# ---- 1. Đổi tên khi chỉ có Memory/ ----
with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    leg = root / "Memory"
    (leg / "facts").mkdir(parents=True)
    (leg / "MEMORY.md").write_text("# idx\n- [a](facts/a.md)\n", encoding="utf-8")
    (leg / "facts" / "a.md").write_text("hello\n", encoding="utf-8")
    actions = mp.reconcile_memory_dir(root)
    check("chỉ Memory/ → đổi tên thành memory/", (root / "memory").is_dir())
    check("sau đổi tên không còn tên Memory riêng (hoặc cùng inode trên FS không phân biệt)",
          not mp.both_casing_dirs(root))
    check("file facts còn sau đổi tên", (root / "memory" / "facts" / "a.md").is_file())
    check("có action đổi tên hoặc đã chuẩn", bool(actions) or (root / "memory" / "MEMORY.md").is_file())


# ---- 2. Gộp khi cả hai tồn tại (chỉ trên FS case-sensitive) ----
if _case_sensitive_tmpdir():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        can = root / "memory"
        leg = root / "Memory"
        (can / "facts").mkdir(parents=True)
        (leg / "facts").mkdir(parents=True)
        (can / "MEMORY.md").write_text("# idx\n- [old](facts/old.md)\n", encoding="utf-8")
        (leg / "MEMORY.md").write_text("# idx\n- [old](facts/old.md)\n- [new](facts/new.md)\n", encoding="utf-8")
        (can / "facts" / "old.md").write_text("canonical\n", encoding="utf-8")
        (leg / "facts" / "new.md").write_text("from legacy\n", encoding="utf-8")
        (leg / "facts" / "old.md").write_text("legacy duplicate\n", encoding="utf-8")
        actions = mp.reconcile_memory_dir(root)
        check("CANARY: sau gộp không còn cả hai casing", not mp.both_casing_dirs(root))
        check("file mới từ Memory/ vào memory/", (can / "facts" / "new.md").read_text(encoding="utf-8") == "from legacy\n")
        check("file trùng: giữ bản memory/ (không đè)",
              (can / "facts" / "old.md").read_text(encoding="utf-8") == "canonical\n")
        idx = (can / "MEMORY.md").read_text(encoding="utf-8")
        check("MEMORY.md gộp dòng mới từ legacy", "facts/new.md" in idx)
        check("có action gộp", any("→" in a or "gộp" in a for a in actions))
else:
    print("skip  gộp dual-dir (FS không phân biệt hoa/thường - giống macOS mặc định)")
    check("bỏ qua dual-dir trên FS này là đúng", True)
    # Vẫn tập _merge_index (dùng chung cho dual-dir trên Linux/CI)
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        can_idx = root / "MEMORY.md"
        leg_idx = root / "legacy.md"
        can_idx.write_text("- [a](facts/a.md)\n", encoding="utf-8")
        leg_idx.write_text("- [a](facts/a.md)\n- [b](facts/b.md)\n", encoding="utf-8")
        check("merge index thêm dòng mới", mp._merge_index(can_idx, leg_idx) is True)
        check("merge index giữ dòng cũ + thêm b",
              "facts/a.md" in can_idx.read_text(encoding="utf-8")
              and "facts/b.md" in can_idx.read_text(encoding="utf-8"))


# ---- 3. memory_dir luôn trỏ canonical sau reconcile ----
with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    (root / "Memory" / "conversations").mkdir(parents=True)
    d = mp.memory_dir(root)
    check("memory_dir sau reconcile là .../memory", d.name == "memory")
    check("conversations còn dưới memory/", (d / "conversations").is_dir())


# ---- 4. Canary tài liệu / prompt không còn dạy brain/Memory/ ----
claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
check("CLAUDE.md dùng brain/memory/", "brain/memory/" in claude)
check("CLAUDE.md KHÔNG còn brain/Memory/ (path)", "brain/Memory/" not in claude)
check("CLAUDE.md cảnh báo không dùng Memory viết hoa", "never `Memory/`" in claude or "never Memory/" in claude.lower() or "capital M" in claude)

seed = (ROOT / "server" / "main.py").read_text(encoding="utf-8")
check("SCHEMA_SEED ghi memory/ chữ thường", '`- `memory/` - bộ nhớ' in seed or "`memory/` - bộ nhớ" in seed)
check("main dùng memory_paths", "memory_paths" in seed)
check("_fit_memory_index trỏ memory/facts/", "memory/facts/" in seed)
check("_fit_memory_index KHÔNG còn Memory/facts/ trong chuỗi user-facing",
      'ở Memory/facts/' not in seed and "Memory/MEMORY.md" not in seed.split("def brain_migrate")[0])

learn = (ROOT / "server" / "learn.py").read_text(encoding="utf-8")
check("curator không hardcode Memory/conversations path",
      ' / "Memory" / "conversations"' not in learn)
check("curator dùng brain_memory_dir(...)/conversations",
      'brain_memory_dir(brain)) / "conversations"' in learn)


print("")
if fails:
    print(f"THAT BAI {len(fails)}: " + ", ".join(fails))
    sys.exit(1)
print("OK - test_memory_casing: tat ca pass")
