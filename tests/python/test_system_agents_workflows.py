"""Test: agent/workflow HỆ THỐNG sync vào brain như skill/loop. Chạy:

    python tests/python/test_system_agents_workflows.py
"""
from _paths import ROOT, SERVER  # noqa: E402,F401
import json
import os
import tempfile
from pathlib import Path

os.environ.setdefault("JAVIS_STATE_DIR", tempfile.mkdtemp(prefix="javis-aw-"))

import system_sync  # noqa: E402

_fails = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        _fails.append(name)


def main():
    tmp = Path(tempfile.mkdtemp(prefix="javis-aw-run-"))
    try:
        agents = tmp / "sysagents"
        workflows = tmp / "sysworkflows"
        agents.mkdir()
        workflows.mkdir()
        (agents / "demo-agent.md").write_text(
            "---\ntype: agent\nname: Demo\nslug: demo-agent\nrole: test\ngroup: AI\n---\nThan agent v1\n",
            encoding="utf-8",
        )
        (workflows / "demo-wf.md").write_text(
            "---\ntype: workflow\nname: Demo WF\nslug: demo-wf\ngroup: AI\n---\nThan wf v1\n",
            encoding="utf-8",
        )

        system_sync.SYSTEM_SKILLS_DIR = tmp / "noskills"
        system_sync.SYSTEM_LOOPS_DIR = tmp / "noloops"
        system_sync.SYSTEM_AGENTS_DIR = agents
        system_sync.SYSTEM_WORKFLOWS_DIR = workflows
        system_sync._SKILL_SLUGS_CACHE = None
        system_sync._SYNCED_ROOTS.clear()

        items = system_sync._system_items()
        keys = {it[0] for it in items}
        check("1. liet ke agents + workflows",
              keys == {"agents/demo-agent", "workflows/demo-wf"})
        check("1b. kind dung",
              {it[1] for it in items} == {"agent", "workflow"})

        brain = tmp / "brain"
        brain.mkdir()
        res = system_sync.sync_brain(brain)
        check("2. cai agent", (brain / "agents" / "demo-agent.md").is_file())
        check("2b. cai workflow", (brain / "workflows" / "demo-wf.md").is_file())
        check("2c. installed 2",
              set(res["installed"]) == {"agents/demo-agent", "workflows/demo-wf"})

        man = json.loads((brain / ".javis" / "system-manifest.json").read_text(encoding="utf-8"))
        check("3. manifest agents/", "agents/demo-agent" in man["files"])
        check("3b. manifest workflows/", "workflows/demo-wf" in man["files"])

        res2 = system_sync.sync_brain(brain)
        check("4. idempotent", not res2["installed"] and not res2["updated"])

        (agents / "demo-agent.md").write_text(
            "---\ntype: agent\nname: Demo\nslug: demo-agent\nrole: test\ngroup: AI\n---\nThan agent v2\n",
            encoding="utf-8",
        )
        res3 = system_sync.sync_brain(brain)
        check("5. cap nhat agent chua sua",
              "agents/demo-agent" in res3["updated"]
              and "v2" in (brain / "agents" / "demo-agent.md").read_text(encoding="utf-8"))

        (brain / "agents" / "demo-agent.md").write_text(
            "---\ntype: agent\nname: Demo\nslug: demo-agent\nrole: test\ngroup: AI\n---\nCUA USER\n",
            encoding="utf-8",
        )
        (agents / "demo-agent.md").write_text(
            "---\ntype: agent\nname: Demo\nslug: demo-agent\nrole: test\ngroup: AI\n---\nThan agent v3\n",
            encoding="utf-8",
        )
        res4 = system_sync.sync_brain(brain)
        check("6. user sua -> giu nguyen",
              "CUA USER" in (brain / "agents" / "demo-agent.md").read_text(encoding="utf-8")
              and "agents/demo-agent" in res4["kept_user"])

        # Repo thật phải ship caps (không để thư mục trống trong image)
        real_agents = ROOT / "system" / "agents"
        real_wfs = ROOT / "system" / "workflows"
        n_a = len(list(real_agents.glob("*.md"))) if real_agents.is_dir() else 0
        n_w = len(list(real_wfs.glob("*.md"))) if real_wfs.is_dir() else 0
        check("7. repo co >= 30 agent he thong", n_a >= 30)
        check("7b. repo co >= 10 workflow he thong", n_w >= 10)
        check("7c. khong ship agent HTDT noi bo",
              not (real_agents / "thuc-tap-doanh-nghiep.md").exists()
              and not (real_agents / "du-an-uav.md").exists())

        # EXCLUDE trong code: dù lỡ có file trong SYSTEM_AGENTS_DIR vẫn bị bỏ
        bad = tmp / "sysagents-bad"
        bad.mkdir()
        (bad / "thuc-tap-doanh-nghiep.md").write_text("---\nslug: thuc-tap-doanh-nghiep\n---\nx\n",
                                                       encoding="utf-8")
        (bad / "ok-agent.md").write_text("---\nslug: ok-agent\n---\nok\n", encoding="utf-8")
        system_sync.SYSTEM_AGENTS_DIR = bad
        system_sync.SYSTEM_WORKFLOWS_DIR = tmp / "empty-wf"
        keys_ex = {it[0] for it in system_sync._system_items()}
        check("8. EXCLUDE_SYSTEM_AGENTS chan ship",
              "agents/thuc-tap-doanh-nghiep" not in keys_ex
              and "agents/ok-agent" in keys_ex)

        # Migrate Javis/agents → gộp khi agents/ đã có
        brain_leg = tmp / "brain-legacy"
        (brain_leg / "Javis" / "agents").mkdir(parents=True)
        (brain_leg / "agents").mkdir(parents=True)
        (brain_leg / "Javis" / "agents" / "user-only.md").write_text(
            "---\nslug: user-only\n---\nuser\n", encoding="utf-8")
        (brain_leg / "agents" / "already.md").write_text(
            "---\nslug: already\n---\nalready\n", encoding="utf-8")
        system_sync.migrate_brain(brain_leg)
        check("9. migrate gop Javis/agents khi agents/ da co",
              (brain_leg / "agents" / "user-only.md").is_file()
              and (brain_leg / "agents" / "already.md").is_file())

        # File sẵn có trùng hash → managed, không kept_user
        system_sync.SYSTEM_AGENTS_DIR = agents
        system_sync.SYSTEM_WORKFLOWS_DIR = workflows
        brain3 = tmp / "brain3"
        brain3.mkdir()
        (brain3 / "agents").mkdir()
        (brain3 / "agents" / "demo-agent.md").write_text(
            (agents / "demo-agent.md").read_text(encoding="utf-8"), encoding="utf-8")
        # reset demo-agent to v1 for match - may have been v3; rewrite v1
        (agents / "demo-agent.md").write_text(
            "---\ntype: agent\nname: Demo\nslug: demo-agent\nrole: test\ngroup: AI\n---\nThan agent v1\n",
            encoding="utf-8",
        )
        (brain3 / "agents" / "demo-agent.md").write_text(
            (agents / "demo-agent.md").read_text(encoding="utf-8"), encoding="utf-8")
        system_sync._SYNCED_ROOTS.clear()
        res5 = system_sync.sync_brain(brain3)
        check("10. file san co trung hash -> managed (khong kept_user)",
              "agents/demo-agent" not in res5.get("kept_user", [])
              and "agents/demo-agent" not in res5.get("installed", []))
    finally:
        pass
    if _fails:
        print(f"\n{len(_fails)} FAIL: " + "; ".join(_fails))
        raise SystemExit(1)
    print("\nALL OK")


if __name__ == "__main__":
    main()
