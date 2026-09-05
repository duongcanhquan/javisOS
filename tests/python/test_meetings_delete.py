"""Xóa file cuộc họp — chỉ trong sources/meetings/."""
from pathlib import Path

from _paths import SERVER  # noqa: F401  - nạp server/ vào sys.path
import meetings as mt


def test_delete_meeting_transcript_and_sidecars(tmp_path):
    d = mt.meetings_dir(str(tmp_path))
    md = d / "2026-09-05-test-abc.md"
    jl = d / "2026-09-05-test-abc.jsonl"
    sm = d / "2026-09-05-test-abc-summary.md"
    md.write_text("# test\n", encoding="utf-8")
    jl.write_text("{}", encoding="utf-8")
    sm.write_text("# sum\n", encoding="utf-8")
    rel = str(md.relative_to(tmp_path)).replace("\\", "/")
    r = mt.delete_files(str(tmp_path), rel)
    assert r["ok"] is True
    assert not md.exists()
    assert not jl.exists()
    assert not sm.exists()


def test_delete_rejects_outside_meetings(tmp_path):
    bad = tmp_path / "notes.md"
    bad.write_text("x", encoding="utf-8")
    rel = str(bad.relative_to(tmp_path)).replace("\\", "/")
    r = mt.delete_files(str(tmp_path), rel)
    assert r["ok"] is False


if __name__ == "__main__":
    import tempfile
    t = Path(tempfile.mkdtemp())
    test_delete_meeting_transcript_and_sidecars(t)
    test_delete_rejects_outside_meetings(t)
    print("OK - test_meetings_delete")
