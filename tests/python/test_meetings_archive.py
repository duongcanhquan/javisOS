"""Lưu trữ + tìm kiếm cuộc họp."""
import importlib.util
import json
from pathlib import Path


def _mt():
    spec = importlib.util.spec_from_file_location(
        "meetings", Path(__file__).resolve().parents[2] / "server" / "meetings.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _sample_md(title: str, body_line: str) -> str:
    return (
        "---\n"
        "type: source\n"
        "source_kind: meeting\n"
        "status: unprocessed\n"
        "created: 2026-09-05 10:30\n"
        "meeting_id: abc123\n"
        f"title: {json.dumps(title, ensure_ascii=False)}\n"
        'attendees: ["An", "Bình"]\n'
        "tags: [meeting]\n"
        "---\n\n"
        f"# {title}\n\n"
        "## Transcript\n\n"
        f"**[10:31]** {body_line}\n"
    )


def test_archive_groups_and_search(tmp_path):
    mt = _mt()
    d = mt.meetings_dir(str(tmp_path))
    (d / "2026-09-05-hop-marketing-abc.md").write_text(
        _sample_md("Họp Marketing", "ngân sách quảng cáo Facebook"), encoding="utf-8")
    (d / "2026-09-04-hop-ky-thuat-xyz.md").write_text(
        _sample_md("Họp kỹ thuật", "deploy VPS docker"), encoding="utf-8")

    all_r = mt.archive(str(tmp_path))
    assert all_r["total"] == 2
    assert len(all_r["groups"]) == 2

    q = mt.archive(str(tmp_path), q="marketing")
    assert q["total"] == 1
    assert q["groups"][0]["items"][0]["title"] == "Họp Marketing"

    day = mt.archive(str(tmp_path), date="2026-09-04")
    assert day["total"] == 1
    assert "kỹ thuật" in day["groups"][0]["items"][0]["title"].lower()


def test_meeting_detail(tmp_path):
    mt = _mt()
    d = mt.meetings_dir(str(tmp_path))
    md = d / "2026-09-05-hop-marketing-abc.md"
    md.write_text(_sample_md("Họp Marketing", "dòng một"), encoding="utf-8")
    rel = str(md.relative_to(tmp_path)).replace("\\", "/")
    r = mt.meeting_detail(str(tmp_path), rel)
    assert r["ok"] is True
    assert r["title"] == "Họp Marketing"
    assert "dòng một" in r["transcript"]
