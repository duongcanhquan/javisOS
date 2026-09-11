"""Ghi chú tay + tổng kết lại cuộc họp đã lưu (không cần phiên RAM).

    python tests/python/test_meetings_notes_tong_ket.py
"""
import asyncio
import tempfile
from pathlib import Path

from _paths import SERVER  # noqa: F401
import meetings as mt


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        raise SystemExit(1)


async def _stream_ok(*_a, **_k):
    yield {"type": "final", "content": "## Tổng hợp\nĐã chốt ngân sách."}


def test_live_notes_va_tong_ket_tu_file():
    mt._ACTIVE.clear()
    root = Path(tempfile.mkdtemp(prefix="javis-mt-"))
    started = mt.start(str(root), title="Họp ngân sách", notes="Agenda: Q3", attendees="An")
    check("start ok", started.get("ok") is True)
    mid = started["id"]
    rline = mt.append_line(mid, "Chúng ta tăng ngân sách Facebook.")
    check("ghi transcript", rline.get("ok") is True)

    notes = mt.set_live_notes(mid, "Cần chốt hạn Friday. An phụ trách ads.")
    check("lưu ghi chú trong họp", notes.get("ok") is True)
    raw = Path(mt._ACTIVE[mid]["md_path"]).read_text(encoding="utf-8")
    check("file có mục Ghi chú trong họp", "## Ghi chú trong họp" in raw)
    check("ghi chú không nuốt transcript", "tăng ngân sách Facebook" in raw)

    rel = started["path"]
    mt.stop(mid)
    mt._ACTIVE.clear()  # giống restart / tổng kết lỗi rồi thoát trang

    hyd = mt.hydrate_from_path(str(root), rel)
    check("nạp lại từ file sau khi mất phiên RAM", hyd.get("ok") is True)
    check("hydrate đúng id", hyd.get("id") == mid)

    mt._ACTIVE.clear()
    out = asyncio.run(mt.analyze_transcript(
        mid, stream_fn=_stream_ok, model="fake", brain_root=str(root), rel_path=rel))
    check("tổng kết được khi không còn phiên RAM", out.get("ok") is True)
    check("ghi file summary", bool(out.get("summary_path")))
    sp = root / out["summary_path"]
    check("summary nằm cạnh transcript", sp.is_file())
    check("summary có nội dung model", "Đã chốt ngân sách" in sp.read_text(encoding="utf-8"))

    det = mt.meeting_detail(str(root), rel)
    check("xem lại thấy tổng kết", det.get("has_summary") is True and "Đã chốt" in (det.get("summary") or ""))
    check("xem lại thấy ghi chú tay", "hạn Friday" in (det.get("notes_full") or ""))


if __name__ == "__main__":
    test_live_notes_va_tong_ket_tu_file()
    print("OK - test_meetings_notes_tong_ket")
