"""Kéo cuộc họp Fathom vào vault: parse MCP, ghi file, bỏ qua trùng. Không gọi mạng.

    python tests/run.py fathom_meetings
"""
import asyncio
import json
import tempfile
from pathlib import Path

from _paths import ROOT, SERVER  # noqa: F401
import fathom_meetings as fm


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        raise SystemExit(1)


def test_parse_va_people():
    payload = fm._parse_payload('```json\n{"items":[{"recording_id": 99, "title": "QBR"}]}\n```')
    rows = fm._as_list(payload)
    check("parse JSON trong fence", rows and fm._rec_id(rows[0]) == "99")
    check("tiêu đề", fm._item_title(rows[0]) == "QBR")

    when = fm._item_when({"created_at": "2026-03-01T16:01:12Z"})
    check("lấy ngày từ created_at", when[0] == "2026-03-01")

    people = fm._people({
        "calendar_invitees": [{"name": "An"}, {"email": "binh@x.com"}],
        "recorded_by": {"name": "Chi"},
    })
    check("người từ calendar_invitees + recorded_by",
          people[:1] == ["Chi"] and "An" in people)

    tx = fm._text_from_payload({
        "transcript": [
            {"speaker": {"display_name": "An"}, "text": "Chốt ngân sách."},
        ]
    })
    check("transcript speaker lồng dict", "An" in tx and "ngân sách" in tx)

    summ = fm._text_from_payload({
        "default_summary": {"markdown_formatted": "## Tóm tắt\nĐã chốt."}
    })
    check("summary markdown_formatted", "Đã chốt" in summ)


def test_ghi_vault_va_bo_trung():
    root = Path(tempfile.mkdtemp(prefix="javis-fathom-"))
    w = fm._write_vault(
        str(root),
        recording_id="123456789",
        title="Họp Fathom thử",
        date_key="2026-09-15",
        time_label="10:30",
        people=["An", "Bình"],
        url="https://fathom.video/share/x",
        transcript="**An:** Xin chào.",
        summary="## Tóm tắt\nĐã gặp.",
        actions="Việc cần làm (Fathom):\n- Gửi báo cáo",
    )
    check("ghi vault ok", w.get("ok") is True)
    md = root / w["path"]
    check("file transcript tồn tại", md.is_file())
    raw = md.read_text(encoding="utf-8")
    check("frontmatter fathom_recording_id", "fathom_recording_id:" in raw and "123456789" in raw)
    check("tag fathom", "fathom" in raw)
    check("có transcript", "Xin chào" in raw)
    check("có link Fathom", "fathom.video" in raw)
    check("có việc cần làm", "Gửi báo cáo" in raw)
    sp = root / w["summary_path"]
    check("file summary tồn tại", sp.is_file())
    check("summary nội dung", "Đã gặp" in sp.read_text(encoding="utf-8"))

    have = fm.imported_ids(str(root))
    check("imported_ids thấy recording", "123456789" in have)

    skip = asyncio.run(fm.import_one(str(root), "123456789", title="Họp Fathom thử"))
    check("trùng thì skipped, không gọi MCP", skip.get("skipped") is True and skip.get("ok") is True)


def test_catalog_va_route():
    cat = json.loads((ROOT / "system" / "mcp-catalog.json").read_text(encoding="utf-8"))
    item = next((c for c in cat["connectors"] if c.get("id") == "fathom"), None)
    check("catalog có connector fathom", bool(item))
    check("Fathom OAuth HTTP MCP",
          item["auth"]["type"] == "oauth" and item["url"] == "https://api.fathom.ai/mcp")
    check("default chỉ đọc", item.get("default_perm") == "readonly")
    main_src = (SERVER / "main.py").read_text(encoding="utf-8")
    check("route status/list/import/sync",
          "/meetings/fathom/status" in main_src and
          "/meetings/fathom/list" in main_src and
          "/meetings/fathom/import" in main_src and
          "/meetings/fathom/sync" in main_src)


if __name__ == "__main__":
    test_parse_va_people()
    test_ghi_vault_va_bo_trung()
    test_catalog_va_route()
    print("OK - test_fathom_meetings")
