"""Cuộc họp: lưu transcript realtime + tổng hợp bằng model cloud (Antigravity mặc định).

STT chạy trên trình duyệt (Moonshine WASM). Module này chỉ nhận chữ đã chốt,
ghi `sources/meetings/`, và khi dừng thì gọi model cloud để tóm tắt.
"""
from __future__ import annotations

import json
import re
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

# Trạng thái phiên đang ghi (RAM). Restart container mất phiên đang mở — chấp nhận được
# vì transcript đã append xuống đĩa từng dòng.
_ACTIVE: dict[str, dict] = {}

_ANALYZE_SYSTEM = (
    "Bạn là trợ lý thư ký cuộc họp chuyên nghiệp. Chỉ dùng transcript được cung cấp. "
    "Không bịa số liệu, tên người, ý kiến hay quyết định không có trong transcript. "
    "Viết tiếng Việt, rõ ràng, logic, trung lập.\n\n"
    "Trả lời đúng các mục markdown sau:\n"
    "## Diễn biến cuộc họp\n"
    "(Cuộc họp diễn ra thế nào: mục đích, không khí, các chủ đề chính theo thứ tự)\n"
    "## Ý kiến các bên\n"
    "(Gom theo người nói nếu transcript có nhãn; nêu quan điểm chính, không bịa)\n"
    "## Đề xuất đã nêu\n"
    "(Các phương án / đề xuất được đưa ra)\n"
    "## Quyết định\n"
    "(Những gì đã chốt; nếu chưa chốt thì ghi rõ 'chưa quyết định')\n"
    "## Việc cần làm\n"
    "- [ ] Việc — người phụ trách (nếu có) — hạn (nếu có)\n"
    "## Cần lưu ý\n"
    "(Rủi ro, điểm nghẽn, thông tin còn thiếu, follow-up)\n"
    "## Tổng hợp\n"
    "(1 đoạn ngắn như thư ký chuyên nghiệp: kết luận logic của cả cuộc họp)\n"
)


def _skill_system_prompt(brain_root: str = "") -> str:
    """Ưu tiên body skill `phan-tich-cuoc-hop` nếu có trong brain hoặc .claude/skills."""
    candidates = []
    if brain_root:
        root = Path(brain_root)
        candidates.extend([
            root / "skills" / "phan-tich-cuoc-hop" / "SKILL.md",
            root / ".claude" / "skills" / "phan-tich-cuoc-hop" / "SKILL.md",
        ])
    try:
        here = Path(__file__).resolve().parent.parent
        candidates.append(here / ".claude" / "skills" / "phan-tich-cuoc-hop" / "SKILL.md")
    except Exception:
        pass
    for p in candidates:
        try:
            if p.is_file():
                raw = p.read_text(encoding="utf-8")
                if raw.startswith("---"):
                    parts = raw.split("---", 2)
                    body = parts[2] if len(parts) >= 3 else raw
                else:
                    body = raw
                body = body.strip()
                if len(body) > 80:
                    return (
                        "Tuân thủ skill phân tích cuộc họp sau. "
                        "Chỉ dùng transcript được cung cấp, không bịa.\n\n" + body
                    )
        except OSError:
            continue
    return _ANALYZE_SYSTEM


def _slug(s: str, n: int = 40) -> str:
    s = re.sub(r"[^\w\s-]", "", (s or "").strip().lower(), flags=re.UNICODE)
    s = re.sub(r"[\s_]+", "-", s).strip("-")
    return (s or "cuoc-hop")[:n]


def _now_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _file_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d-%H%M")


def meetings_dir(brain_root: str) -> Path:
    """`sources/meetings/` dưới brain (tạo nếu chưa có)."""
    root = Path(brain_root)
    sources = None
    try:
        for p in root.iterdir():
            if p.is_dir() and re.match(r"^(\d+\s*[-_.]\s*)?sources$", p.name, re.I):
                sources = p
                break
    except OSError:
        pass
    if sources is None:
        sources = root / "sources"
        sources.mkdir(parents=True, exist_ok=True)
    d = sources / "meetings"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _parse_attendees(raw: str) -> list[str]:
    names = []
    for part in re.split(r"[,;\n]+", raw or ""):
        n = part.strip()
        if n and n not in names:
            names.append(n[:60])
    return names[:20]


def start(brain_root: str, title: str = "", language: str = "vi",
          notes: str = "", attendees: str = "") -> dict:
    """Tạo phiên mới + file transcript trống. Trả {ok, id, path, ...}."""
    mid = uuid.uuid4().hex[:12]
    stamp = _file_stamp()
    title = (title or "").strip() or f"Cuộc họp {stamp}"
    notes = (notes or "").strip()
    people = _parse_attendees(attendees)
    slug = _slug(title)
    base = meetings_dir(brain_root)
    md_path = base / f"{stamp}-{slug}-{mid}.md"
    jsonl_path = base / f"{stamp}-{slug}-{mid}.jsonl"
    created = _now_stamp()
    people_line = ", ".join(people) if people else "(chưa ghi)"
    notes_block = f"## Ghi chú trước họp\n\n{notes}\n\n" if notes else ""
    fm = (
        "---\n"
        "type: source\n"
        "source_kind: meeting\n"
        "status: unprocessed\n"
        f"created: {created}\n"
        f"meeting_id: {mid}\n"
        f"language: {language or 'vi'}\n"
        f"title: {json.dumps(title, ensure_ascii=False)}\n"
        f"attendees: {json.dumps(people, ensure_ascii=False)}\n"
        "tags: [meeting]\n"
        "---\n\n"
        f"# {title}\n\n"
        f"_Bắt đầu: {created}_\n\n"
        f"**Thành phần:** {people_line}\n\n"
        f"{notes_block}"
        "## Transcript\n\n"
    )
    md_path.write_text(fm, encoding="utf-8")
    jsonl_path.write_text("", encoding="utf-8")
    rel_md = str(md_path.relative_to(Path(brain_root))).replace("\\", "/")
    rel_jsonl = str(jsonl_path.relative_to(Path(brain_root))).replace("\\", "/")
    _ACTIVE[mid] = {
        "id": mid,
        "brain_root": str(brain_root),
        "title": title,
        "language": language or "vi",
        "notes": notes,
        "attendees": people,
        "md_path": str(md_path),
        "jsonl_path": str(jsonl_path),
        "rel_md": rel_md,
        "rel_jsonl": rel_jsonl,
        "started_at": time.time(),
        "line_count": 0,
        "stopped": False,
    }
    return {
        "ok": True,
        "id": mid,
        "title": title,
        "path": rel_md,
        "jsonl": rel_jsonl,
        "language": language or "vi",
        "attendees": people,
        "notes": notes,
    }


def get_active(meeting_id: str) -> Optional[dict]:
    return _ACTIVE.get(meeting_id)


def append_line(meeting_id: str, text: str, t0: float = 0, t1: float = 0,
                partial: bool = False, speaker: str = "",
                speaker_index: int = -1) -> dict:
    """Ghi một dòng transcript đã chốt. partial=True → bỏ qua (chỉ hiện UI)."""
    if partial:
        return {"ok": True, "skipped": "partial"}
    sess = _ACTIVE.get(meeting_id)
    if not sess:
        return {"ok": False, "error": "Không tìm thấy phiên họp (đã dừng hoặc hết hạn)."}
    if sess.get("stopped"):
        return {"ok": False, "error": "Phiên đã dừng."}
    line = (text or "").strip()
    if not line:
        return {"ok": True, "skipped": "empty"}
    sp = (speaker or "").strip()
    if not sp and speaker_index is not None and int(speaker_index) >= 0:
        people = sess.get("attendees") or []
        idx = int(speaker_index)
        sp = people[idx] if idx < len(people) else f"Người {idx + 1}"
    ts = _now_stamp()
    try:
        with open(sess["md_path"], "a", encoding="utf-8") as f:
            if sp:
                f.write(f"**[{ts}] {sp}:** {line}\n\n")
            else:
                f.write(f"**[{ts}]** {line}\n\n")
    except OSError as e:
        return {"ok": False, "error": f"Ghi md lỗi: {e}"}
    rec = {
        "ts": time.time(),
        "wall": ts,
        "text": line,
        "t0": float(t0 or 0),
        "t1": float(t1 or 0),
        "speaker": sp,
        "speaker_index": int(speaker_index) if speaker_index is not None else -1,
    }
    try:
        with open(sess["jsonl_path"], "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError as e:
        return {"ok": False, "error": f"Ghi jsonl lỗi: {e}"}
    sess["line_count"] = int(sess.get("line_count") or 0) + 1
    return {"ok": True, "line_count": sess["line_count"], "wall": ts, "speaker": sp}


def stop(meeting_id: str) -> dict:
    sess = _ACTIVE.get(meeting_id)
    if not sess:
        return {"ok": False, "error": "Không tìm thấy phiên họp."}
    if not sess.get("stopped"):
        ended = _now_stamp()
        try:
            with open(sess["md_path"], "a", encoding="utf-8") as f:
                f.write(f"\n_Kết thúc: {ended} · {sess.get('line_count', 0)} đoạn_\n")
        except OSError:
            pass
        sess["stopped"] = True
        sess["ended_at"] = time.time()
    return {
        "ok": True,
        "id": meeting_id,
        "path": sess.get("rel_md"),
        "jsonl": sess.get("rel_jsonl"),
        "line_count": sess.get("line_count", 0),
        "title": sess.get("title"),
    }


def read_transcript(meeting_id: str = "", md_path: str = "") -> str:
    path = ""
    if meeting_id and meeting_id in _ACTIVE:
        path = _ACTIVE[meeting_id].get("md_path") or ""
    if not path and md_path:
        path = md_path
    if not path:
        return ""
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError:
        return ""


def replace_transcript_from_stt(meeting_id: str, text: str, source: str = "groq") -> dict:
    sess = _ACTIVE.get(meeting_id)
    if not sess:
        return {"ok": False, "error": "Không tìm thấy phiên họp."}
    title = sess.get("title") or "Cuộc họp"
    created = _now_stamp()
    people = sess.get("attendees") or []
    notes = sess.get("notes") or ""
    people_line = ", ".join(people) if people else "(chưa ghi)"
    notes_block = f"## Ghi chú trước họp\n\n{notes}\n\n" if notes else ""
    body = (
        "---\n"
        "type: source\n"
        "source_kind: meeting\n"
        "status: unprocessed\n"
        f"created: {created}\n"
        f"meeting_id: {meeting_id}\n"
        f"language: {sess.get('language') or 'vi'}\n"
        f"title: {json.dumps(title, ensure_ascii=False)}\n"
        f"attendees: {json.dumps(people, ensure_ascii=False)}\n"
        f"stt_fallback: {source}\n"
        "tags: [meeting]\n"
        "---\n\n"
        f"# {title}\n\n"
        f"_Transcript từ file ghi âm ({source}) · {created}_\n\n"
        f"**Thành phần:** {people_line}\n\n"
        f"{notes_block}"
        "## Transcript\n\n"
        f"{(text or '').strip()}\n"
    )
    try:
        Path(sess["md_path"]).write_text(body, encoding="utf-8")
        rec = {"ts": time.time(), "wall": created, "text": (text or "").strip(),
               "source": source, "bulk": True}
        Path(sess["jsonl_path"]).write_text(
            json.dumps(rec, ensure_ascii=False) + "\n", encoding="utf-8")
        sess["line_count"] = 1 if (text or "").strip() else 0
    except OSError as e:
        return {"ok": False, "error": str(e)}
    return {"ok": True, "path": sess.get("rel_md"), "chars": len(text or "")}


def chunk_text(text: str, max_chars: int = 12000) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]
    chunks, i = [], 0
    while i < len(text):
        chunks.append(text[i:i + max_chars])
        i += max_chars
    return chunks


async def analyze_transcript(
    meeting_id: str,
    *,
    stream_fn: Callable,
    model: str = "",
    api_key: str = "",
) -> dict:
    """Gọi model cloud (stream_fn) → ghi file summary chuyên nghiệp."""
    sess = _ACTIVE.get(meeting_id)
    if not sess:
        return {"ok": False, "error": "Không tìm thấy phiên họp."}
    if not sess.get("stopped"):
        stop(meeting_id)

    raw = read_transcript(meeting_id=meeting_id)
    if len(raw.strip()) < 40:
        return {"ok": False, "error": "Transcript quá ngắn để phân tích."}

    body = raw
    if "## Transcript" in raw:
        body = raw.split("## Transcript", 1)[1]

    meta = (
        f"Tiêu đề: {sess.get('title')}\n"
        f"Thành phần: {', '.join(sess.get('attendees') or []) or '(không ghi)'}\n"
    )
    if sess.get("notes"):
        meta += f"Ghi chú trước họp: {sess.get('notes')}\n"

    chunks = chunk_text(body, 6000)
    system = _skill_system_prompt(sess.get("brain_root") or "")
    partials: list[str] = []
    for i, ch in enumerate(chunks):
        prompt = (
            meta
            + f"\nTranscript cuộc họp"
            + (f" (phần {i + 1}/{len(chunks)})" if len(chunks) > 1 else "")
            + ":\n\n"
            + ch
            + "\n\nHãy tổng kết như trợ lý thư ký chuyên nghiệp theo đúng các mục đã nêu."
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]
        buf = []
        err = ""
        async for ev in stream_fn(api_key, model, messages, "off"):
            t = ev.get("type")
            if t == "text":
                buf.append(ev.get("content") or "")
            elif t == "final":
                buf.append(ev.get("content") or "")
            elif t == "error":
                err = ev.get("content") or "Model lỗi"
                break
        if err:
            return {"ok": False, "error": err}
        partials.append("".join(buf).strip())

    if len(partials) == 1:
        summary = partials[0]
    else:
        merge_msgs = [
            {"role": "system", "content": system},
            {"role": "user", "content": (
                "Gộp các bản phân tích từng phần thành MỘT báo cáo thống nhất, "
                "bỏ trùng lặp, giữ đủ các mục:\n\n" + "\n\n---\n\n".join(partials)
            )},
        ]
        buf = []
        async for ev in stream_fn(api_key, model, merge_msgs, "off"):
            if ev.get("type") in ("text", "final"):
                buf.append(ev.get("content") or "")
            elif ev.get("type") == "error":
                return {"ok": False, "error": ev.get("content") or "Gộp tổng kết lỗi"}
        summary = "".join(buf).strip() or "\n\n".join(partials)

    if not summary:
        return {"ok": False, "error": "Model trả về rỗng. Thử lại hoặc đổi model ở trang Models."}

    md_path = Path(sess["md_path"])
    summary_path = md_path.with_name(md_path.stem + "-summary.md")
    created = _now_stamp()
    out = (
        "---\n"
        "type: source\n"
        "source_kind: meeting-summary\n"
        "status: unprocessed\n"
        f"created: {created}\n"
        f"meeting_id: {meeting_id}\n"
        f"source: {json.dumps(sess.get('rel_md') or '', ensure_ascii=False)}\n"
        f"model: {json.dumps(model, ensure_ascii=False)}\n"
        "tags: [meeting, summary]\n"
        "---\n\n"
        f"# Tổng kết: {sess.get('title')}\n\n"
        f"{summary.rstrip()}\n"
    )
    try:
        summary_path.write_text(out, encoding="utf-8")
        try:
            old = md_path.read_text(encoding="utf-8")
            if "status: unprocessed" in old:
                md_path.write_text(
                    old.replace("status: unprocessed", "status: processed", 1),
                    encoding="utf-8")
        except OSError:
            pass
    except OSError as e:
        return {"ok": False, "error": f"Ghi summary lỗi: {e}"}

    rel = str(summary_path.relative_to(Path(sess["brain_root"]))).replace("\\", "/")
    sess["summary_path"] = str(summary_path)
    sess["rel_summary"] = rel
    return {
        "ok": True,
        "id": meeting_id,
        "summary_path": rel,
        "transcript_path": sess.get("rel_md"),
        "summary": summary,
        "model": model,
    }


# Backward-compatible alias (tests / plugin cũ).
analyze_with_ollama = analyze_transcript


def delete_files(brain_root: str, rel_path: str) -> dict:
    """Xóa file cuộc họp (transcript/summary) trong sources/meetings/."""
    root = Path(brain_root).resolve()
    rel = (rel_path or "").strip().replace("\\", "/").lstrip("/")
    if not rel or ".." in rel.split("/"):
        return {"ok": False, "error": "Đường dẫn không hợp lệ"}
    p = (root / rel).resolve()
    try:
        p.relative_to(root)
    except ValueError:
        return {"ok": False, "error": "Đường dẫn ngoài brain"}
    if not p.is_file() or p.suffix.lower() != ".md":
        return {"ok": False, "error": "Chỉ xóa file .md cuộc họp"}
    parts = [x.lower() for x in p.parts]
    if "meetings" not in parts:
        return {"ok": False, "error": "Chỉ xóa file trong thư mục meetings"}
    deleted: list[str] = []
    try:
        p.unlink()
        deleted.append(rel)
    except OSError as e:
        return {"ok": False, "error": f"Xóa lỗi: {e}"}
    stem = p.stem
    if stem.endswith("-summary"):
        return {"ok": True, "deleted": deleted}
    jl = p.parent / f"{stem}.jsonl"
    if jl.is_file():
        try:
            jl.unlink()
            deleted.append(str(jl.relative_to(root)).replace("\\", "/"))
        except OSError:
            pass
    summ = p.parent / f"{stem}-summary.md"
    if summ.is_file():
        try:
            summ.unlink()
            deleted.append(str(summ.relative_to(root)).replace("\\", "/"))
        except OSError:
            pass
    return {"ok": True, "deleted": deleted}


def list_recent(brain_root: str, limit: int = 20) -> list[dict]:
    arch = archive(brain_root, limit=limit)
    flat = []
    for g in arch.get("groups") or []:
        for it in g.get("items") or []:
            flat.append({
                "name": Path(it["path"]).name,
                "path": it["path"],
                "kind": "transcript",
                "mtime": it.get("mtime") or 0,
                "size": it.get("size") or 0,
                "title": it.get("title") or "",
            })
    return flat


def _parse_simple_frontmatter(raw: str) -> tuple[dict, str]:
    meta: dict = {}
    body = raw
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            body = parts[2]
            for line in parts[1].splitlines():
                if ":" not in line:
                    continue
                k, v = line.split(":", 1)
                k, v = k.strip(), v.strip()
                if not k:
                    continue
                if v.startswith("[") or v.startswith('"'):
                    try:
                        meta[k] = json.loads(v)
                    except json.JSONDecodeError:
                        meta[k] = v.strip('"')
                else:
                    meta[k] = v
    return meta, body


def _date_time_from_file(name: str, meta: dict) -> tuple[str, str]:
    """Trả (YYYY-MM-DD, HH:MM) từ frontmatter hoặc tên file."""
    created = str(meta.get("created") or "")
    m = re.match(r"(\d{4}-\d{2}-\d{2})\s+(\d{1,2}:\d{2})", created)
    if m:
        return m.group(1), m.group(2)
    m = re.match(r"(\d{4}-\d{2}-\d{2})-(\d{4})", name)
    if m:
        t = m.group(2)
        return m.group(1), f"{t[:2]}:{t[2:]}"
    m = re.match(r"(\d{4}-\d{2}-\d{2})", name)
    if m:
        return m.group(1), ""
    return "", ""


def _extract_meeting_sections(body: str) -> tuple[str, str, str]:
    """notes, transcript, heading title line."""
    heading = ""
    for line in body.splitlines():
        if line.startswith("# "):
            heading = line[2:].strip()
            break
    notes = ""
    if "## Ghi chú trước họp" in body:
        chunk = body.split("## Ghi chú trước họp", 1)[1]
        if "## Transcript" in chunk:
            notes = chunk.split("## Transcript", 1)[0].strip()
        else:
            notes = chunk.strip()
    transcript = ""
    if "## Transcript" in body:
        transcript = body.split("## Transcript", 1)[1]
        transcript = re.sub(r"\n_Kết thúc:.*$", "", transcript, flags=re.S).strip()
    return notes, transcript, heading


def _count_transcript_lines(transcript: str) -> int:
    if not transcript:
        return 0
    n = len(re.findall(r"^\*\*\[", transcript, flags=re.M))
    if n:
        return n
    return len([ln for ln in transcript.splitlines() if ln.strip()])


def _read_text_limited(path: Path, max_bytes: int = 512_000) -> str:
    try:
        data = path.read_bytes()
        if len(data) > max_bytes:
            data = data[:max_bytes]
        return data.decode("utf-8", errors="replace")
    except OSError:
        return ""


def _meeting_item_from_path(brain_root: str, p: Path) -> Optional[dict]:
    if p.name.endswith("-summary.md"):
        return None
    raw = _read_text_limited(p)
    if not raw:
        return None
    meta, body = _parse_simple_frontmatter(raw)
    notes, transcript, heading = _extract_meeting_sections(body)
    title = meta.get("title") or heading or p.stem
    if isinstance(title, str):
        title = title.strip()
    else:
        title = str(title)
    attendees = meta.get("attendees") or []
    if isinstance(attendees, str):
        attendees = _parse_attendees(attendees)
    elif not isinstance(attendees, list):
        attendees = []
    date_key, time_label = _date_time_from_file(p.name, meta)
    if not date_key:
        date_key = datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d")
    rel = str(p.relative_to(Path(brain_root))).replace("\\", "/")
    stem = p.stem
    summ_path = p.parent / f"{stem}-summary.md"
    summ_rel = ""
    summ_excerpt = ""
    has_summary = summ_path.is_file()
    if has_summary:
        summ_rel = str(summ_path.relative_to(Path(brain_root))).replace("\\", "/")
        summ_body = _read_text_limited(summ_path, 120_000)
        _, summ_text, _ = _extract_meeting_sections(summ_body)
        summ_excerpt = re.sub(r"\s+", " ", summ_text)[:280]
    excerpt_src = transcript or notes or summ_excerpt
    excerpt = re.sub(r"\s+", " ", excerpt_src)[:280]
    line_count = _count_transcript_lines(transcript)
    st = meta.get("status") or "unprocessed"
    return {
        "id": str(meta.get("meeting_id") or stem),
        "title": title or p.stem,
        "path": rel,
        "summary_path": summ_rel or None,
        "has_summary": has_summary,
        "attendees": attendees[:20],
        "notes": (notes or "")[:500],
        "created": str(meta.get("created") or ""),
        "date": date_key,
        "time": time_label,
        "line_count": line_count,
        "excerpt": excerpt,
        "status": st,
        "mtime": p.stat().st_mtime,
        "size": p.stat().st_size,
    }


def _in_date_range(date_key: str, date: str = "", date_from: str = "",
                   date_to: str = "") -> bool:
    if date and date_key != date:
        return False
    if date_from and date_key < date_from:
        return False
    if date_to and date_key > date_to:
        return False
    return True


def archive(brain_root: str, q: str = "", date: str = "", date_from: str = "",
            date_to: str = "", limit: int = 80) -> dict:
    """Danh sách cuộc họp nhóm theo ngày, có tìm kiếm."""
    d = meetings_dir(brain_root)
    query = (q or "").strip().lower()
    limit = max(1, min(int(limit or 80), 200))
    items: list[dict] = []
    for p in sorted(d.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True):
        it = _meeting_item_from_path(brain_root, p)
        if not it:
            continue
        if not _in_date_range(it["date"], date, date_from, date_to):
            continue
        if query:
            hay = " ".join([
                it.get("title") or "",
                " ".join(it.get("attendees") or []),
                it.get("notes") or "",
                it.get("excerpt") or "",
                it.get("path") or "",
                it.get("date") or "",
            ]).lower()
            if it.get("summary_path"):
                sp = Path(brain_root) / it["summary_path"]
                if sp.is_file():
                    hay += " " + _read_text_limited(sp, 200_000).lower()
            if it.get("path"):
                tp = Path(brain_root) / it["path"]
                if tp.is_file():
                    hay += " " + _read_text_limited(tp, 300_000).lower()
            if query not in hay:
                continue
        items.append(it)
        if len(items) >= limit:
            break
    groups_map: dict[str, list] = {}
    for it in items:
        groups_map.setdefault(it["date"], []).append(it)
    groups = []
    for dk in sorted(groups_map.keys(), reverse=True):
        groups.append({"date": dk, "items": groups_map[dk]})
    return {"ok": True, "total": len(items), "groups": groups}


def meeting_detail(brain_root: str, rel_path: str) -> dict:
    root = Path(brain_root).resolve()
    rel = (rel_path or "").strip().replace("\\", "/").lstrip("/")
    if not rel or ".." in rel.split("/"):
        return {"ok": False, "error": "Đường dẫn không hợp lệ"}
    p = (root / rel).resolve()
    try:
        p.relative_to(root)
    except ValueError:
        return {"ok": False, "error": "Đường dẫn ngoài brain"}
    if not p.is_file() or p.suffix.lower() != ".md":
        return {"ok": False, "error": "Không tìm thấy file"}
    if "meetings" not in [x.lower() for x in p.parts]:
        return {"ok": False, "error": "Không phải file cuộc họp"}
    if p.name.endswith("-summary.md"):
        return {"ok": False, "error": "Chọn file transcript, không phải summary"}
    it = _meeting_item_from_path(brain_root, p)
    if not it:
        return {"ok": False, "error": "Đọc file lỗi"}
    raw = _read_text_limited(p, 800_000)
    meta, body = _parse_simple_frontmatter(raw)
    notes, transcript, _ = _extract_meeting_sections(body)
    summary = ""
    if it.get("summary_path"):
        sp = root / it["summary_path"]
        if sp.is_file():
            _, summary, _ = _extract_meeting_sections(_read_text_limited(sp, 800_000))
    return {
        "ok": True,
        **it,
        "notes_full": notes,
        "transcript": transcript,
        "summary": summary,
        "project_id": str(meta.get("project_id") or ""),
        "wiki_links": meta.get("wiki_links") if isinstance(meta.get("wiki_links"), list) else [],
        "knowledge_topic": str(meta.get("knowledge_topic") or ""),
    }


def _resolve_wiki_dir(brain_root: str) -> Path:
    root = Path(brain_root)
    try:
        for child in sorted(root.iterdir()):
            if child.is_dir() and re.match(r"^(\d+\s*[-_.]\s*)?wiki$", child.name.strip(), re.I):
                return child
    except OSError:
        pass
    d = root / "wiki"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _rewrite_frontmatter(raw: str, updates: dict) -> str:
    """Cập nhật/thêm khóa frontmatter YAML đơn giản; giữ body nguyên."""
    meta, body = _parse_simple_frontmatter(raw)
    meta.update({k: v for k, v in updates.items() if v is not None})
    lines = ["---"]
    order = [
        "type", "source_kind", "status", "created", "processed_at", "meeting_id",
        "language", "title", "attendees", "tags", "project_id", "project_name",
        "knowledge_topic", "wiki_links", "source", "model",
    ]
    seen = set()
    for k in order:
        if k not in meta:
            continue
        seen.add(k)
        v = meta[k]
        if isinstance(v, (list, dict)):
            lines.append(f"{k}: {json.dumps(v, ensure_ascii=False)}")
        elif isinstance(v, str) and (v.startswith("[") or ":" in v or v.startswith("{")):
            lines.append(f"{k}: {json.dumps(v, ensure_ascii=False)}")
        else:
            lines.append(f"{k}: {v}")
    for k, v in meta.items():
        if k in seen:
            continue
        if isinstance(v, (list, dict)):
            lines.append(f"{k}: {json.dumps(v, ensure_ascii=False)}")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    body_out = body if body.startswith("\n") else "\n" + body
    return "\n".join(lines) + body_out


def _safe_meeting_md(brain_root: str, rel_path: str) -> Path:
    root = Path(brain_root).resolve()
    rel = (rel_path or "").strip().replace("\\", "/").lstrip("/")
    if not rel or ".." in rel.split("/"):
        raise ValueError("Đường dẫn không hợp lệ")
    p = (root / rel).resolve()
    p.relative_to(root)
    if not p.is_file() or p.suffix.lower() != ".md":
        raise ValueError("Không tìm thấy file cuộc họp")
    if "meetings" not in [x.lower() for x in p.parts]:
        raise ValueError("Không phải file cuộc họp")
    return p


def to_knowledge(
    brain_root: str,
    rel_path: str = "",
    *,
    project_id: str = "",
    project_name: str = "",
    topic: str = "",
    pin: bool = True,
    add_project_file_fn=None,
    pin_project_file_fn=None,
) -> dict:
    """Đưa cuộc họp vào Wiki (+ gắn project nếu chọn).

    - Ưu tiên nội dung summary nếu có; không thì dùng transcript/notes.
    - Tạo trang `wiki/meetings/<slug>.md`, cập nhật index/log.
    - Đánh dấu source + summary: status processed, wiki_links, project_id.
    - Nếu có project_id + callback: gắn file summary (hoặc transcript) vào project.
    """
    try:
        p = _safe_meeting_md(brain_root, rel_path)
    except ValueError as e:
        return {"ok": False, "error": str(e)}
    if p.name.endswith("-summary.md"):
        # Cho phép chọn summary: quy về transcript cùng stem.
        stem = p.stem[: -len("-summary")]
        cand = p.parent / f"{stem}.md"
        if cand.is_file():
            p = cand
        else:
            return {"ok": False, "error": "Chọn file transcript cuộc họp"}

    it = _meeting_item_from_path(brain_root, p)
    if not it:
        return {"ok": False, "error": "Đọc cuộc họp lỗi"}

    root = Path(brain_root).resolve()
    summ_rel = it.get("summary_path") or ""
    summ_path = (root / summ_rel) if summ_rel else None
    body_src = ""
    source_for_wiki = it["path"]
    if summ_path and summ_path.is_file():
        _, body_src, _ = _extract_meeting_sections(_read_text_limited(summ_path, 800_000))
        source_for_wiki = summ_rel
    if not (body_src or "").strip():
        raw_t = _read_text_limited(p, 800_000)
        notes, transcript, _ = _extract_meeting_sections(raw_t)
        body_src = (transcript or notes or "").strip()
        source_for_wiki = it["path"]
    if len((body_src or "").strip()) < 40:
        return {"ok": False, "error": "Nội dung quá ngắn. Hãy ghi họp hoặc bấm Tổng kết trước."}

    title = (it.get("title") or p.stem).strip()
    topic_name = (topic or "").strip() or title
    wiki_title = topic_name if topic_name.lower() != title.lower() else f"Họp: {title}"
    date_key = it.get("date") or datetime.now().strftime("%Y-%m-%d")
    slug = _slug(wiki_title, 48)
    wiki_dir = _resolve_wiki_dir(brain_root)
    meetings_wiki = wiki_dir / "meetings"
    meetings_wiki.mkdir(parents=True, exist_ok=True)
    wiki_file = meetings_wiki / f"{date_key}-{slug}.md"
    # Trùng slug: thêm meeting_id ngắn
    if wiki_file.exists():
        mid = (it.get("id") or "x")[:8]
        wiki_file = meetings_wiki / f"{date_key}-{slug}-{mid}.md"

    wiki_rel = str(wiki_file.relative_to(root)).replace("\\", "/")
    src_rel = it["path"]
    attendees = it.get("attendees") or []
    people_line = ", ".join(attendees) if attendees else "(không ghi)"
    proj_line = ""
    if project_id:
        pn = (project_name or "").strip() or project_id
        proj_line = f"\n**Dự án:** {pn}\n"

    wiki_body = (
        "---\n"
        "type: wiki\n"
        f"created: {_now_stamp()}\n"
        f"source: {json.dumps(src_rel, ensure_ascii=False)}\n"
        f"meeting_id: {json.dumps(it.get('id') or '', ensure_ascii=False)}\n"
        f"aliases: {json.dumps([title, topic_name, f'cuộc họp {title}'], ensure_ascii=False)}\n"
        "tags: [meeting, knowledge]\n"
        + (f"project_id: {json.dumps(project_id, ensure_ascii=False)}\n" if project_id else "")
        + "---\n\n"
        f"# {wiki_title}\n\n"
        f"Kiến thức chưng từ cuộc họp **{title}** ({date_key}). "
        f"Dùng khi cần quyết định, việc làm hoặc ngữ cảnh dự án liên quan buổi họp này.\n"
        f"{proj_line}\n"
        f"**Thành phần:** {people_line}\n\n"
        f"**Nguồn:** [[{Path(src_rel).stem}]] · `{src_rel}`"
        + (f" · summary `{summ_rel}`" if summ_rel else "")
        + "\n\n"
        "## Nội dung đã chưng\n\n"
        f"{body_src.strip()}\n\n"
        "## Liên hệ\n\n"
        f"- Nguồn gốc: `{src_rel}`\n"
        + (f"- Dự án gắn: `{project_name or project_id}`\n" if project_id else "")
    )
    try:
        wiki_file.write_text(wiki_body, encoding="utf-8")
    except OSError as e:
        return {"ok": False, "error": f"Ghi wiki lỗi: {e}"}

    # index + log
    idx = wiki_dir / "index.md"
    try:
        line = f"- [[{wiki_file.stem}]] — {wiki_title} (họp {date_key})\n"
        if idx.is_file():
            cur = idx.read_text(encoding="utf-8")
            if wiki_file.stem not in cur:
                if not cur.endswith("\n"):
                    cur += "\n"
                if "## Cuộc họp" not in cur:
                    cur += "\n## Cuộc họp\n\n"
                cur += line
                idx.write_text(cur, encoding="utf-8")
        else:
            idx.write_text(
                "# Wiki index\n\n## Cuộc họp\n\n" + line, encoding="utf-8")
    except OSError:
        pass
    try:
        logf = wiki_dir / "log.md"
        entry = (
            f"\n## [{datetime.now().strftime('%Y-%m-%d')}] ingest | họp → wiki\n\n"
            f"- Nguồn: `{src_rel}`\n"
            f"- Trang: [[{wiki_file.stem}]]\n"
            + (f"- Dự án: {project_name or project_id}\n" if project_id else "")
        )
        if logf.is_file():
            logf.write_text(logf.read_text(encoding="utf-8") + entry, encoding="utf-8")
        else:
            logf.write_text("# Wiki log\n" + entry, encoding="utf-8")
    except OSError:
        pass

    processed_at = _now_stamp()
    fm_updates = {
        "status": "processed",
        "processed_at": processed_at,
        "wiki_links": [wiki_rel],
        "knowledge_topic": topic_name,
    }
    if project_id:
        fm_updates["project_id"] = project_id
        if project_name:
            fm_updates["project_name"] = project_name

    for target in [p] + ([summ_path] if summ_path and summ_path.is_file() else []):
        try:
            old = target.read_text(encoding="utf-8")
            target.write_text(_rewrite_frontmatter(old, fm_updates), encoding="utf-8")
        except OSError:
            pass

    project_file_id = None
    attach_path = summ_rel or src_rel
    if project_id and callable(add_project_file_fn):
        try:
            project_file_id = add_project_file_fn(
                project_id, attach_path, f"Họp: {title}")
            if pin and project_file_id and callable(pin_project_file_fn):
                try:
                    pin_project_file_fn(project_id, project_file_id)
                except Exception:
                    pass
        except Exception as e:
            return {
                "ok": True,
                "wiki_path": wiki_rel,
                "source_path": src_rel,
                "summary_path": summ_rel or None,
                "project_id": project_id,
                "project_warn": str(e),
                "title": wiki_title,
            }

    return {
        "ok": True,
        "wiki_path": wiki_rel,
        "source_path": src_rel,
        "summary_path": summ_rel or None,
        "project_id": project_id or "",
        "project_file_id": project_file_id,
        "title": wiki_title,
        "pinned": bool(pin and project_file_id),
    }


