"""Cuộc họp: lưu transcript realtime + tổng hợp bằng Ollama local.

STT chạy trên trình duyệt (Moonshine WASM). Module này chỉ nhận chữ đã chốt,
ghi `sources/meetings/`, và khi dừng thì gọi Ollama để tóm tắt như trợ lý chuyên nghiệp.
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


async def analyze_with_ollama(
    meeting_id: str,
    *,
    stream_fn: Callable,
    model: str = "qwen3:4b",
    api_key: str = "local",
) -> dict:
    """Gọi Ollama local → ghi file summary chuyên nghiệp."""
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

    chunks = chunk_text(body, 12000)
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
                err = ev.get("content") or "Ollama lỗi"
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
                return {"ok": False, "error": ev.get("content") or "Ollama merge lỗi"}
        summary = "".join(buf).strip() or "\n\n".join(partials)

    if not summary:
        return {"ok": False, "error": "Ollama trả về rỗng."}

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
    d = meetings_dir(brain_root)
    files = sorted(d.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    out = []
    for p in files[: max(1, min(limit, 50))]:
        kind = "summary" if p.name.endswith("-summary.md") else "transcript"
        rel = str(p.relative_to(Path(brain_root))).replace("\\", "/")
        out.append({
            "name": p.name,
            "path": rel,
            "kind": kind,
            "mtime": p.stat().st_mtime,
            "size": p.stat().st_size,
        })
    return out
