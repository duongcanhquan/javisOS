"""Landing/HTML mở trên Javis phải còn nút Về Javis — không kẹt trang thuần.

    python tests/python/test_xem_html_trong_javis.py

Không mạng. Dùng JAVIS_STATE_DIR tạm.
"""
import os
import sys
import tempfile
from pathlib import Path

from _paths import ROOT, SERVER  # noqa: E402,F401

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

os.environ.setdefault("JAVIS_STATE_DIR", tempfile.mkdtemp(prefix="javis-htmlview-"))

import main  # noqa: E402

fails = []


def check(name: str, cond: bool) -> None:
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


_TMP = Path(tempfile.mkdtemp(prefix="javis-htmlview-brain-")).resolve()
BRAIN = _TMP / "brains" / "Bo Nao"
land = BRAIN / "exports" / "landing" / "demo"
land.mkdir(parents=True)
(land / "index.html").write_text(
    "<!doctype html><html><body><h1>Landing demo</h1></body></html>",
    encoding="utf-8",
)
(BRAIN / "ghi-chu.md").write_text("# note", encoding="utf-8")

main._brain_root = lambda brain: str(BRAIN)
main.BRAINS_DIR = str(_TMP / "brains")
os.environ["JAVIS_HOST"] = "0.0.0.0"
os.environ.pop("JAVIS_FILES_ROOT", None)
os.environ.pop("JAVIS_REQUIRE_LOGIN", None)

rel = "exports/landing/demo/index.html"

wrap = main.html_view_response("brain", rel)
body = wrap.body.decode("utf-8") if hasattr(wrap, "body") else ""
check("html-view trả HTMLResponse", getattr(wrap, "status_code", 200) == 200)
check("html-view có nút Về Javis về /", "← Về Javis" in body and 'href="/"' in body)
check("html-view nhúng iframe raw (plain=1), không dán nội dung landing vào khung",
      "iframe" in body and "plain=1" in body and "Landing demo" not in body)
check("html-view không sửa file xuất — chỉ bọc",
      "<h1>Landing demo</h1>" not in body)

bad = main.html_view_response("brain", "../etc/passwd")
check("html-view chặn traversal",
      getattr(bad, "status_code", 0) in (400, 404)
      or (hasattr(bad, "body") and b"error" in bad.body))

md = main.html_view_response("brain", "ghi-chu.md")
check("html-view từ chối file không phải HTML", getattr(md, "status_code", 0) == 400)

redir = main.raw_file_response("brain", rel, dest="document")
loc = ""
if hasattr(redir, "headers"):
    loc = redir.headers.get("location") or redir.headers.get("Location") or ""
check("raw HTML mở thành tab (dest=document) → html-view",
      getattr(redir, "status_code", 0) in (302, 307) and "html-view" in loc)

frame = main.raw_file_response("brain", rel, dest="iframe")
check("iframe vẫn nhận file thô (landing chạy trong trình sửa)",
      getattr(frame, "status_code", 200) == 200
      and "FileResponse" in type(frame).__name__)

plain = main.raw_file_response("brain", rel, dest="document", plain=True)
check("plain=1 giữ trang thuần, không vòng redirect",
      getattr(plain, "status_code", 200) == 200
      and "FileResponse" in type(plain).__name__)

note = main.raw_file_response("brain", "ghi-chu.md", dest="document")
check("raw .md không bị đẩy sang html-view",
      "html-view" not in str(getattr(note, "headers", {}))
      and "FileResponse" in type(note).__name__)

src = (ROOT / "server" / "main.py").read_text(encoding="utf-8")
check("có route /files/html-view", '@app.get("/files/html-view")' in src)
check("files_raw đọc Sec-Fetch-Dest, không gọi handler khác như hàm",
      "sec-fetch-dest" in src and "def html_view_response(" in src)
check("brain_file_compat không bắt buộc Request (test cũ gọi thẳng handler)",
      "request: Request = None" in src)

print()
if fails:
    print(f"FAIL - test_xem_html_trong_javis: {len(fails)} lỗi: " + ", ".join(fails))
    raise SystemExit(1)
print("OK - test_xem_html_trong_javis: tất cả pass")
