"""Mã bash `[[ ... ]]` KHÔNG phải wikilink, và một đầu dây hỏng không được giết đồ thị.

    python tests/run.py wikilink_bo_khoi_ma
"""
from _paths import ROOT, SERVER  # noqa: E402,F401
import os
import re

from graph_builder import bo_khoi_ma, doc_wikilink  # noqa: E402

_fails = []


def check(name, cond, extra=None):
    print(("ok   " if cond else "FAIL ") + name + ("" if cond or extra is None else f"  [{extra}]"))
    if not cond:
        _fails.append(name)


# ---- 1. Đọc đúng wikilink thật, bỏ sạch mã ----
VAN_BAN = (
    "Xem [[ghi chu that]] và [[thu muc/note khac|bí danh]] và [[co neo#muc]].\n"
    "\n"
    "```bash\n"
    'if [[ ! "$command_file" =~ \\.md$ ]]; then echo loi; fi\n'
    '[[ -d "$dir" ]] && echo co\n'
    "```\n"
    "\n"
    "Trong dòng: `[[ -z \"$x\" ]]` cũng không tính.\n"
    "\n"
    "~~~sh\n"
    '[[ -f "$p" ]] || exit 1\n'
    "~~~\n"
    "\n"
    "Còn [[cai nay]] thì tính.\n"
)
ra = list(doc_wikilink(VAN_BAN))
check("giữ đủ wikilink THẬT (4 cái, kể cả có bí danh và neo)",
      ra == ["ghi chu that", "note khac", "co neo", "cai nay"], ra)
check("CANARY: không còn đọc nhầm phép thử bash trong khối ```",
      not any("command_file" in x or "$dir" in x for x in ra))
check("bỏ cả khối ~~~ chứ không chỉ ```", not any('-f "$p"' in x for x in ra))
check("bỏ cả mã trong dòng (dấu huyền)", not any("-z" in x for x in ra))

check("dòng gây lỗi thật không còn sinh ra đầu dây nào",
      list(doc_wikilink('```\n[[ ! "$command_file" =~ \\.md$ ]]\n```')) == [])

# ---- 2. Không làm hỏng ca thường ----
check("file không có mã: đọc y như cũ",
      list(doc_wikilink("a [[mot]] b [[hai]]")) == ["mot", "hai"])
check("file rỗng / None không nổ",
      list(doc_wikilink("")) == [] and list(doc_wikilink(None)) == [])
check("bo_khoi_ma giữ nguyên văn bản không có mã",
      bo_khoi_ma("chi la chu thuong") == "chi la chu thuong")
check("wikilink NGOÀI khối mã vẫn giữ dù file có khối mã",
      "van giu" in list(doc_wikilink("```\ncode\n```\n[[van giu]]")))

# ---- 3. Cả hai đường dò đều dùng CHUNG một bộ ----
gb = open(os.path.join(ROOT, "server", "graph_builder.py"), encoding="utf-8").read()
gr = open(os.path.join(ROOT, "server", "routes", "graph.py"), encoding="utf-8").read()
check("build_graph dùng doc_wikilink", "for target_stem in doc_wikilink(content):" in gb)
check("đường live (_node_payload) cũng dùng doc_wikilink", "for t in doc_wikilink(content):" in gr)
check("CANARY: routes/graph.py không tự quét regex thô nữa", "WIKILINK_RE" not in gr)
check("CANARY: graph_builder chỉ quét regex thô ĐÚNG MỘT LẦN (trong doc_wikilink)",
      len(re.findall(r"WIKILINK_RE\.finditer", gb)) == 1, len(re.findall(r"WIKILINK_RE\.finditer", gb)))
check("và lần đó nằm SAU khi đã bỏ khối mã",
      re.search(r"WIKILINK_RE\.finditer\(bo_khoi_ma\(text\)\)", gb) is not None)

# ---- 4. Trình duyệt không nối tới node không tồn tại ----
js = open(os.path.join(ROOT, "dashboard", "graph.js"), encoding="utf-8").read()
check("addOrUpdate dựng tập node có thật trước khi nối",
      "const coNode = new Set(d.nodes.map(x => x.id));" in js)
check("đầu dây trỏ vào hư không thì BỎ QUA, không đẩy vào đồ thị",
      re.search(r"if \(!coNode\.has\(tid\)\) return;", js) is not None)

print(("\n%d FAIL" % len(_fails)) if _fails else "\nTat ca OK")
raise SystemExit(1 if _fails else 0)
