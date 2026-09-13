"""Skill + script GitHub Trending: parse HTML không mạng, khuôn skill/seed.

    python tests/run.py bao_cao_github_trending
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from _paths import ROOT  # noqa: E402

SKILL = ROOT / ".claude" / "skills" / "bao-cao-github-trending"
SCRIPT = SKILL / "scripts" / "fetch_trending.py"
SEED = ROOT / "scripts" / "seed-github-trending-vps.sh"
FORCE = ROOT / "scripts" / "force-github-trending-today-vps.sh"
FIXTURE = ROOT / "tests" / "fixtures" / "github-trending-sample.html"
DEPLOY = ROOT / "scripts" / "vps-deploy.sh"

fails = []


def check(name, cond, extra=None):
    print(("ok   " if cond else "FAIL ") + name + ("" if cond or extra is None else f"  [{extra}]"))
    if not cond:
        fails.append(name)


def main() -> int:
    check("có skill SKILL.md", (SKILL / "SKILL.md").is_file())
    check("có fetch_trending.py", SCRIPT.is_file())
    check("có javis-fit.md", (SKILL / "references" / "javis-fit.md").is_file())
    check("có fixture HTML", FIXTURE.is_file())

    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    check("frontmatter name", "name: bao-cao-github-trending" in text)
    check("có description_en", "description_en:" in text)
    check("group Năng suất", "group: Năng suất" in text)
    check("không tự cài", "Không cài" in text or "không tự cài" in text.lower())
    check("cấm pentest/leak/tải khóa", "pentest" in text.lower() and "leak" in text.lower())
    check("tin nhắn không bảng", "KHÔNG bảng" in text or "không bảng" in text)
    check("lưu exports/github-trending", "exports/github-trending" in text)
    check("cron 20h trong skill", "0 20 * * *" in text)

    fit = (SKILL / "references" / "javis-fit.md").read_text(encoding="utf-8")
    check("javis-fit có Không / Chỉ xem / Có thể bổ sung",
          "Không" in fit and "Chỉ xem" in fit and "Có thể bổ sung" in fit)
    check("javis-fit cấm pentest", "pentest" in fit.lower())

    # Parse fixture — không mạng
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--html-file", str(FIXTURE), "--limit", "15"],
        capture_output=True, text=True, encoding="utf-8",
    )
    check("script thoát 0 với fixture", proc.returncode == 0, proc.stderr[-400:] if proc.stderr else "")
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        check("stdout là JSON", False, str(e))
        data = {}
    items = data.get("items") or []
    names = [x.get("full_name") for x in items]
    check("tách đủ repo fixture (bỏ /sponsors/)", names == [
        "JustVugg/colibri", "ever-co/ever-gauzy",
        "tech-leads-club/agent-skills", "vxcontrol/pentagi",
    ], names)
    check("không lấy sponsors/ever-co", "sponsors/ever-co" not in names)
    colibri = items[0] if items else {}
    check("colibri: language C + 652 sao hôm nay",
          colibri.get("language") == "C" and colibri.get("stars_today") == 652, colibri)
    check("colibri: mô tả không rỗng", "MoE" in (colibri.get("description") or ""))
    check("có danh_sach_tho có URL",
          "https://github.com/JustVugg/colibri" in (data.get("danh_sach_tho") or ""))
    check("source=html-file", data.get("source") == "html-file")
    src = SCRIPT.read_text(encoding="utf-8")
    check("stdout UTF-8 (Windows không vỡ emoji mô tả)", "reconfigure" in src and "utf-8" in src)
    check("ok true", data.get("ok") is True)

    # Cấm mạng khi không có file
    no_net = subprocess.run(
        [sys.executable, str(SCRIPT), "--no-network"],
        capture_output=True, text=True, encoding="utf-8",
    )
    check("--no-network không giả repo", no_net.returncode != 0)
    try:
        empty = json.loads(no_net.stdout or "{}")
    except json.JSONDecodeError:
        empty = {}
    check("--no-network items rỗng", not empty.get("items"))

    # Gương JSON
    mirror = json.dumps([{
        "author": "foo", "name": "bar", "description": "demo",
        "language": "Rust", "stars": 10, "currentPeriodStars": 3,
    }])
    tmp = ROOT / "tests" / "fixtures" / "_tmp_trending_mirror.json"
    tmp.write_text(mirror, encoding="utf-8")
    try:
        mj = subprocess.run(
            [sys.executable, str(SCRIPT), "--json-file", str(tmp), "--limit", "5"],
            capture_output=True, text=True, encoding="utf-8",
        )
        md = json.loads(mj.stdout)
        check("parse gương JSON", md.get("items") and md["items"][0]["full_name"] == "foo/bar")
    finally:
        if tmp.exists():
            tmp.unlink()

    seed = SEED.read_text(encoding="utf-8")
    check("seed cron 0 20 * * *", "0 20 * * *" in seed)
    check("seed muc_quyen suggest", "suggest" in seed)
    check("seed chat_id all", "CHAT_ID" in seed and "all" in seed)
    check("seed gọi skill bao-cao-github-trending", "bao-cao-github-trending" in seed)
    check("seed idempotent theo label", "GitHub Trending 20h" in seed)
    check("force script tồn tại", FORCE.is_file())
    check("force nhắc seed trước", "seed-github-trending-vps.sh" in FORCE.read_text(encoding="utf-8"))

    deploy = DEPLOY.read_text(encoding="utf-8")
    check("vps-deploy extras gọi seed github trending",
          "seed-github-trending-vps.sh" in deploy)

    wf = ROOT / ".github" / "workflows" / "seed-github-trending-vps.yml"
    check("có workflow seed tay", wf.is_file())
    wft = wf.read_text(encoding="utf-8")
    check("workflow chỉ dispatch (không push)", "workflow_dispatch" in wft and "push:" not in wft)
    check("workflow group vps-ssh", "vps-ssh" in wft)

    if fails:
        print(f"\nTHAT BAI {len(fails)}: {', '.join(fails)}")
        return 1
    print("\nOK - test_bao_cao_github_trending")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
