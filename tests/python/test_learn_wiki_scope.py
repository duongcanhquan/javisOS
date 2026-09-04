"""Tự học: scope guard phải cho phép Wiki đánh số; verify skill không xoá khi parse lỗi.

Ca thật: brain dùng `03 - Wiki` (Obsidian/PARA). Engine học ghi note vào đúng thư mục đó
qua resolve_subfolder, rồi scope guard cứng chỉ cho `Wiki/` → coi path ngoài phạm vi →
hard_reset → nhật ký đầy `Bị chặn: bỏ N path ngoài scope`. User thấy "thất bại ghi" lặp lại.
"""
from _paths import ROOT, SERVER  # noqa: E402,F401
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import git_brain
import learn


def _engine(tmp: Path, resolve_wiki=None):
    deps = MagicMock()
    deps.state_dir = tmp
    deps.brain_root = lambda b: str(tmp)
    deps.brain_memory_dir = lambda b: tmp / "memory"
    deps.resolve_subfolder = resolve_wiki or (
        lambda root, regex, default: str(tmp / "Wiki"))
    deps.atomic_write_text = lambda path, text: (
        Path(path).parent.mkdir(parents=True, exist_ok=True),
        Path(path).write_text(text, encoding="utf-8"),
    )
    deps.build_system_prompt = lambda b: ""
    deps.aux_model = lambda: None
    deps.sessions_store = MagicMock()
    deps.readonly_tools = ["Read", "Glob", "Grep", "LS"]
    return learn.LearnFeature(deps)


def test_paths_within_cho_wiki_danh_so():
    """Prefix `03 - Wiki` phải được coi hợp lệ khi đưa vào allowed."""
    bad = git_brain.paths_within(
        ["03 - Wiki/POS.md", "03 - Wiki/index.md", "memory/facts/a.md"],
        ["memory", "Memory", "Wiki", "wiki", "03 - Wiki", "skills", "Javis"],
    )
    assert bad == []


def test_paths_within_chan_ngoai_scope():
    bad = git_brain.paths_within(
        ["secrets/key.md", "Wiki/ok.md"],
        learn.ALLOWED_WRITE_PREFIXES,
    )
    assert bad == ["secrets/key.md"]


def test_write_allow_prefixes_them_wiki_danh_so():
    tmp = Path(tempfile.mkdtemp(prefix="javis-learn-scope-"))
    (tmp / "03 - Wiki").mkdir()
    (tmp / "memory").mkdir()
    eng = _engine(tmp, lambda root, regex, default: str(tmp / "03 - Wiki"))
    prefixes = eng._write_allow_prefixes("brain", tmp)
    assert "03 - Wiki" in prefixes


def test_promote_giu_wiki_trong_thu_muc_danh_so():
    """Promote thật: note vào `03 - Wiki` phải còn trên đĩa, không bị hard_reset."""
    tmp = Path(tempfile.mkdtemp(prefix="javis-learn-promote-"))
    wiki = tmp / "03 - Wiki"
    wiki.mkdir()
    mem = tmp / "memory"
    (mem / "facts").mkdir(parents=True)
    (mem / "MEMORY.md").write_text("# Memory\n", encoding="utf-8")

    eng = _engine(tmp, lambda root, regex, default: str(wiki))

    class _Lock:
        def acquire(self): return True
        def release(self): pass

    real_lock = git_brain.BrainLock
    real_commit = git_brain.commit_paths
    real_reset = git_brain.hard_reset_paths
    real_is_git = git_brain.is_git_checkout
    git_brain.BrainLock = lambda *a, **k: _Lock()
    git_brain.commit_paths = lambda *a, **k: "abc1234"
    git_brain.is_git_checkout = lambda *a, **k: True
    resets = []
    git_brain.hard_reset_paths = lambda root, paths: resets.extend(paths)
    try:
        rep = eng._promote_sync(
            "brain",
            {
                "facts": [],
                "wiki": [{
                    "title": "POS",
                    "body": "Phần mềm bán hàng. [[conversations/2026-09-04]]",
                    "provenance": "user",
                    "density": 3,
                }],
                "skills": [],
            },
            {"_state": {}},
            {"memory": True, "wiki": True, "skill": False},
            allow_write=True,
        )
    finally:
        git_brain.BrainLock = real_lock
        git_brain.commit_paths = real_commit
        git_brain.hard_reset_paths = real_reset
        git_brain.is_git_checkout = real_is_git

    assert (wiki / "POS.md").is_file(), "note wiki phải còn sau promote"
    assert "POS" in rep["wiki"]
    assert resets == [], f"không được hard_reset wiki đánh số, got {resets}"
    assert not any("ngoài scope" in b for b in rep.get("blocked") or [])


def test_extract_json_fence_va_fallback():
    nested = '''```json
{"facts": [{"slug": "a", "body": "x"}], "notes": "ok"}
```'''
    d = learn._extract_json(nested)
    assert d and d["notes"] == "ok" and d["facts"][0]["slug"] == "a"

    plain = 'noise {"facts": [], "notes": "y"} trailing'
    d2 = learn._extract_json(plain)
    assert d2 and d2["notes"] == "y"


def test_verify_skills_giu_nguyen_khi_parse_loi():
    """Trước đây `or {}` + `if keep else []` xoá sạch skill khi fork verify trả rác."""
    tmp = Path(tempfile.mkdtemp(prefix="javis-learn-verify-"))
    eng = _engine(tmp)
    skills = [{"slug": "viet-email", "name": "Viết email", "description": "Soạn email"}]

    async def fake_spawn(*a, **k):
        return "xin lỗi, không có JSON"

    eng._spawn_readonly = fake_spawn
    out = asyncio.run(eng._verify_skills("brain", skills, {}))
    assert out == skills
