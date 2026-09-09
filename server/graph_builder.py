"""
Graph builder - quét các file markdown, parse [[wikilink]], dựng đồ thị kết nối.
Đây là lớp "Graphify" - visualize mạng lưới note như Obsidian graph view.
"""
import os
import re
import glob
from pathlib import Path
from typing import List, Dict

# Match [[Note]] và [[folder/Note|alias]]
WIKILINK_RE = re.compile(r"\[\[([^\]\|#]+)(?:[#\|][^\]]*)?\]\]")

# File không phải "tri thức" (bản dịch README skill, DESIGN-pl, ...): bỏ khỏi đồ thị dù
# orphans=1. Chỉ nối bằng [[wikilink]] - các file này gần như không bao giờ được link.
_NOISE_STEM_RE = re.compile(
    r"(?i)^(?:"
    r"readme(?:[-_.].*)?|"
    r"license(?:[-_.].*)?|"
    r"changelog(?:[-_.].*)?|"
    r"contributing(?:[-_.].*)?|"
    r"code[-_.]?of[-_.]?conduct|"
    r"design(?:-[a-z0-9]{2,12})?"
    r")$"
)
# stem kiểu note.ja-JP / guide.zh-CN (bản dịch theo locale)
_LOCALE_STEM_RE = re.compile(r"(?i)^.+\.[a-z]{2}(?:-[a-z]{2})?$")
_SKIP_PATH_PARTS = frozenset({
    "node_modules", ".git", ".obsidian", ".trash", "__pycache__", "vendor",
})

# Palette tinh vân tím (như V.A.U.L.T) - tím chủ đạo + vài tông phụ, lõi trắng nóng
FOLDER_COLORS = {
    "00": "#c77dff", "01": "#a96bff", "02": "#7c5cff", "03": "#d98cff",
    "04": "#8a9bff", "05": "#e07ad1", "06": "#b07aff", "07": "#9b8cff",
    "08": "#c9a3ff", "brain": "#c77dff", "wiki": "#7c5cff",
}

def _color_for(rel_path: str) -> str:
    top = rel_path.split("/")[0].lower()
    for key, color in FOLDER_COLORS.items():
        if top.startswith(key):
            return color
    return "#9d7aff"  # tím mặc định

def _top_folder(rel_path: str) -> str:
    parts = rel_path.split("/")
    return parts[0] if len(parts) > 1 else "root"


def is_graph_noise(stem: str, rel: str = "") -> bool:
    """True = không đưa lên đồ thị tri thức (README dịch, DESIGN-xx, thư mục vendor...)."""
    s = (stem or "").strip()
    if not s:
        return True
    if _NOISE_STEM_RE.match(s) or _LOCALE_STEM_RE.match(s):
        return True
    parts = (rel or "").replace("\\", "/").split("/")
    for p in parts[:-1]:
        pl = p.lower()
        if pl in _SKIP_PATH_PARTS or (p.startswith(".") and p not in (".", "..")):
            return True
    return False


def build_graph(roots: List[str], max_files: int = 2000, include_orphans: bool = False) -> Dict:
    """
    Quét nhiều thư mục root, dựng graph.
    roots: list các đường dẫn thư mục chứa .md
    Trả về: {nodes: [...], edges: [...], stats: {...}}
    """
    nodes = {}          # stem (lowercase) -> node dict
    stem_to_id = {}     # stem lowercase -> node id
    edges = []
    file_count = 0
    skipped_noise = 0

    # Pass 1: thu thập tất cả file -> tạo node
    all_files = []
    for root in roots:
        if not root or not os.path.isdir(root):
            continue
        root_name = Path(root).name
        for fpath in glob.glob(f"{root}/**/*.md", recursive=True):
            if file_count >= max_files:
                break
            try:
                rel = Path(fpath).relative_to(root).as_posix()
            except ValueError:
                rel = Path(fpath).name
            stem = Path(fpath).stem
            if is_graph_noise(stem, rel):
                skipped_noise += 1
                continue
            key = stem.lower()
            node_id = key
            if node_id in stem_to_id:
                continue  # trùng tên -> bỏ qua bản sau
            stem_to_id[key] = node_id
            # Mốc "note ra đời" cho timelapse: birthtime (macOS) > ctime (Windows = creation) >
            # mtime; lấy min với mtime vì file copy/sync có thể mang mtime gốc cũ hơn ctime.
            try:
                st = os.stat(fpath)
                born = min(getattr(st, "st_birthtime", st.st_ctime), st.st_mtime)
            except OSError:
                born = 0
            nodes[node_id] = {
                "id": node_id,
                "label": stem,
                "folder": _top_folder(rel),
                "color": _color_for(rel),
                "path": f"{root_name}/{rel}",
                "fullpath": fpath,
                "links": 0,
                "t": born,
            }
            all_files.append((node_id, fpath))
            file_count += 1

    # Pass 2: parse wikilink -> tạo edge
    for node_id, fpath in all_files:
        try:
            content = Path(fpath).read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for match in WIKILINK_RE.finditer(content):
            target_raw = match.group(1).strip()
            target_stem = target_raw.split("/")[-1].strip().lower()
            if target_stem in stem_to_id and target_stem != node_id:
                edges.append({"source": node_id, "target": stem_to_id[target_stem]})
                nodes[node_id]["links"] += 1
                nodes[stem_to_id[target_stem]]["links"] += 1

    # Loại edge trùng
    seen = set()
    unique_edges = []
    for e in edges:
        k = tuple(sorted([e["source"], e["target"]]))
        if k not in seen:
            seen.add(k)
            unique_edges.append(e)

    orphan_count = len([n for n in nodes.values() if n["links"] == 0])

    # Giữ node: mặc định bỏ note cô đơn (0 kết nối); include_orphans=True thì giữ note cô đơn
    # (vẫn đã lọc noise ở Pass 1). Không còn fallback "nếu trống thì hiện hết" - đó chính là
    # nguyên nhân màn hình đầy chấm rời khi vault toàn README/locale không wikilink.
    if include_orphans:
        keep = set(nodes.keys())
    else:
        keep = {nid for nid, n in nodes.items() if n["links"] > 0}

    node_list = [n for nid, n in nodes.items() if nid in keep]
    edge_list = [e for e in unique_edges if e["source"] in keep and e["target"] in keep]

    # Đếm concept theo nhóm (folder cha trực tiếp của file) - cho nhãn HUD
    from collections import Counter
    cat_counter = Counter()
    for n in node_list:
        segs = n["path"].split("/")
        cat = segs[-2] if len(segs) >= 2 else "root"
        cat = re.sub(r"^\d+\s*[-_.]\s*", "", cat).strip()  # bỏ tiền tố "07 - "
        if cat:
            cat_counter[cat] += 1
    categories = [{"name": c, "count": cnt} for c, cnt in cat_counter.most_common(8)]

    return {
        "nodes": node_list,
        "edges": edge_list,
        "categories": categories,
        "stats": {
            "total_notes": len(node_list),
            "total_links": len(edge_list),
            "orphans": orphan_count,
            "hidden": len(nodes) - len(node_list),
            "skipped_noise": skipped_noise,
        }
    }
