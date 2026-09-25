"""Tests for manager_template_sync (path mode, no docker)."""
from __future__ import annotations

import json
from pathlib import Path

from _paths import ROOT, SERVER  # noqa: E402,F401
import manager_template_sync as m


def _brain(tmp: Path, name: str = "src") -> Path:
    root = tmp / name
    (root / "agents").mkdir(parents=True)
    (root / "workflows").mkdir(parents=True)
    (root / "skills" / "demo-skill").mkdir(parents=True)
    (root / "agents" / "alpha.md").write_text("# alpha\nv1\n", encoding="utf-8")
    (root / "workflows" / "flow-a.md").write_text("# flow\nv1\n", encoding="utf-8")
    (root / "skills" / "demo-skill" / "SKILL.md").write_text(
        "---\nname: demo\n---\nbody v1\n", encoding="utf-8"
    )
    return root


def test_install_missing(tmp_path: Path):
    src = _brain(tmp_path, "src")
    dst = tmp_path / "dst"
    dst.mkdir()
    stats = m.sync_brain(src, dst)
    assert stats["installed"] >= 3
    assert (dst / "agents" / "alpha.md").is_file()
    assert (dst / "skills" / "demo-skill" / "SKILL.md").is_file()
    man = json.loads((dst / ".javis" / "manager-manifest.json").read_text(encoding="utf-8"))
    assert "agents/alpha" in man["files"]


def test_skip_user_modified(tmp_path: Path):
    src = _brain(tmp_path, "src")
    dst = _brain(tmp_path, "dst")
    m.sync_brain(src, dst)
    (dst / "agents" / "alpha.md").write_text("# alpha\ntenant edit\n", encoding="utf-8")
    (src / "agents" / "alpha.md").write_text("# alpha\nv2 manager\n", encoding="utf-8")
    stats = m.sync_brain(src, dst)
    assert stats["skipped_user"] >= 1
    assert "tenant edit" in (dst / "agents" / "alpha.md").read_text(encoding="utf-8")


def test_update_unmodified(tmp_path: Path):
    src = _brain(tmp_path, "src")
    dst = _brain(tmp_path, "dst")
    m.sync_brain(src, dst)
    (src / "agents" / "alpha.md").write_text("# alpha\nv2\n", encoding="utf-8")
    stats = m.sync_brain(src, dst)
    assert stats["updated"] >= 1
    assert "v2" in (dst / "agents" / "alpha.md").read_text(encoding="utf-8")


def test_skip_disabled_skill(tmp_path: Path):
    import shutil

    src = _brain(tmp_path, "src")
    dst = _brain(tmp_path, "dst")
    m.sync_brain(src, dst)
    disabled_parent = dst / "skills" / ".disabled"
    disabled_parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(dst / "skills" / "demo-skill"), str(disabled_parent / "demo-skill"))
    (src / "skills" / "demo-skill" / "SKILL.md").write_text(
        "---\nname: demo\n---\nbody v2\n", encoding="utf-8"
    )
    stats = m.sync_brain(src, dst)
    assert stats["skipped_disabled"] >= 1
    assert not (dst / "skills" / "demo-skill" / "SKILL.md").exists()


def test_promote_force(tmp_path: Path):
    src = _brain(tmp_path, "src")
    dst = _brain(tmp_path, "dst")
    (dst / "agents" / "alpha.md").write_text("old\n", encoding="utf-8")
    stats = m.promote(src, dst)
    assert stats["updated"] + stats["installed"] >= 1
    assert "v1" in (dst / "agents" / "alpha.md").read_text(encoding="utf-8")


def test_is_manager_role(monkeypatch):
    monkeypatch.delenv("JAVIS_ROLE", raising=False)
    monkeypatch.delenv("JAVIS_TEMPLATE_SOURCE", raising=False)
    assert m.is_manager_role() is False
    monkeypatch.setenv("JAVIS_ROLE", "manager")
    assert m.is_manager_role() is True


def test_filter_sync_targets_includes_stopped_names():
    names = [
        "javis-manager", "javis-proxy", "javis-park", "javis-quan",
        "javis-lananh", "javis-thuy", "javis-long",
    ]
    got = m.filter_sync_targets(names, manager="javis-manager")
    assert got == ["javis-lananh", "javis-long", "javis-quan", "javis-thuy"]


_got = m.filter_sync_targets(
    ["javis-manager", "javis-proxy", "javis-park", "javis-quan", "javis-thuy"],
    manager="javis-manager",
)
assert _got == ["javis-quan", "javis-thuy"], _got
print("ok - filter_sync_targets")


def test_summarize_sync_report_counts_dict_tenants():
    report = {
        "ok": True,
        "tenants": {
            "javis-thuy": {"installed": 3, "updated": 0, "errors": []},
            "javis-hang": {"installed": 0, "updated": 1, "errors": ["boom"]},
        },
    }
    s = m.summarize_sync_report(report)
    assert s["tenant_count"] == 2
    assert s["installed"] == 3
    assert s["updated"] == 1
    assert any("javis-hang" in e for e in s["errors"])
    assert "javis-thuy" in s["tenant_names"]


def test_schedule_catalog_push_skipped_when_not_manager(monkeypatch):
    monkeypatch.setenv("JAVIS_ROLE", "tenant")
    monkeypatch.delenv("JAVIS_TEMPLATE_SOURCE", raising=False)
    assert m.schedule_catalog_push(reason="test") is False


_sum = m.summarize_sync_report({
    "tenants": {"javis-thuy": {"installed": 3, "updated": 0, "errors": []}},
})
assert _sum["tenant_count"] == 1 and _sum["installed"] == 3, _sum
print("ok - summarize_sync_report")
