"""Kéo cuộc họp Fathom (MCP chính chủ) vào vault `sources/meetings/`.

Fathom KHÔNG ghi mic trong Javis. Bot Fathom ghi trên Zoom/Meet/Teams; module này
chỉ đọc list/summary/transcript rồi ghi file markdown giống cuộc họp native.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import meetings
import mcp_client
import mcp_store

CONNECTOR_ID = "fathom"
SYNC_CAP = 5


def _now_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def connection() -> Optional[dict]:
    for c in mcp_store.resolved(enabled_only=True):
        if c.get("connector_id") == CONNECTOR_ID:
            return c
    return None


def status() -> dict:
    conn = connection()
    if not conn:
        return {"ok": True, "connected": False, "label": ""}
    return {
        "ok": True,
        "connected": True,
        "label": conn.get("label") or "Fathom",
        "perm": conn.get("perm") or "readonly",
    }


def _tool_name(tools: list, *needles: str) -> str:
    names = []
    for t in tools or []:
        if isinstance(t, dict):
            names.append(str(t.get("name") or ""))
        else:
            names.append(str(t or ""))
    for needle in needles:
        want = needle.lower().replace("_", "")
        for n in names:
            if want in n.lower().replace("_", "").replace("-", ""):
                return n
    return ""


def _parse_payload(text: str) -> Any:
    raw = (text or "").strip()
    if raw.startswith("ERROR:"):
        raise ValueError(raw[6:].strip() or "Fathom trả lỗi")
    if not raw:
        return {}
    fenced = re.search(r"```(?:json)?\s*([\s\S]+?)```", raw)
    if fenced:
        raw = fenced.group(1).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    start_obj = raw.find("{")
    start_arr = raw.find("[")
    starts = [i for i in (start_obj, start_arr) if i >= 0]
    if starts:
        chunk = raw[min(starts):]
        try:
            return json.loads(chunk)
        except json.JSONDecodeError:
            pass
    return {"text": raw}


def _as_list(payload: Any) -> list[dict]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("items", "meetings", "data", "results", "recordings"):
        val = payload.get(key)
        if isinstance(val, list):
            return [x for x in val if isinstance(x, dict)]
    if payload.get("recording_id") or payload.get("id"):
        return [payload]
    return []


def _rec_id(item: dict) -> str:
    for k in ("recording_id", "recordingId", "id", "call_id", "callId"):
        v = item.get(k)
        if v is not None and str(v).strip():
            return str(v).strip()
    return ""


def _item_title(item: dict) -> str:
    for k in ("title", "name", "meeting_title", "topic"):
        v = item.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()[:160]
    return "Cuộc họp Fathom"


def _item_when(item: dict) -> tuple[str, str]:
    if item.get("date"):
        return str(item.get("date") or "")[:10], str(item.get("time") or "")
    for k in ("created_at", "createdAt", "recording_start_time", "scheduled_start_time",
              "started_at", "recorded_at", "start_time"):
        v = item.get(k)
        if not v:
            continue
        s = str(v).strip()
        try:
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            dt = datetime.fromisoformat(s)
            if dt.tzinfo:
                dt = dt.astimezone()
            return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M")
        except ValueError:
            m = re.match(r"(\d{4}-\d{2}-\d{2})", s)
            if m:
                return m.group(1), ""
    return datetime.now().strftime("%Y-%m-%d"), ""


def _people(item: dict) -> list[str]:
    if isinstance(item.get("people"), list) and item.get("people"):
        return [str(x).strip()[:60] for x in item["people"] if str(x).strip()][:20]
    names = []
    for k in ("calendar_invitees", "invitees", "attendees", "participants", "speakers"):
        val = item.get(k) or []
        if isinstance(val, str):
            names.extend(meetings._parse_attendees(val))
            continue
        if not isinstance(val, list):
            continue
        for p in val:
            if isinstance(p, str) and p.strip():
                names.append(p.strip()[:60])
            elif isinstance(p, dict):
                n = (p.get("name") or p.get("email") or "").strip()
                if n:
                    names.append(n[:60])
    rec = item.get("recorded_by") or item.get("recorder") or {}
    if isinstance(rec, dict):
        n = (rec.get("name") or rec.get("email") or "").strip()
        if n:
            names.insert(0, n[:60])
    elif isinstance(rec, str) and rec.strip():
        names.insert(0, rec.strip()[:60])
    out = []
    for n in names:
        if n not in out:
            out.append(n)
    return out[:20]


def _rel(brain_root: str, p: Path) -> str:
    try:
        return str(p.resolve().relative_to(Path(brain_root).resolve())).replace("\\", "/")
    except ValueError:
        return p.name


def imported_ids(brain_root: str) -> set[str]:
    ids: set[str] = set()
    d = meetings.meetings_dir(brain_root)
    for p in d.glob("*.md"):
        try:
            head = p.read_text(encoding="utf-8")[:2500]
        except OSError:
            continue
        m = re.search(r"fathom_recording_id:\s*[\"']?([^\s\"']+)", head)
        if m:
            ids.add(m.group(1).strip())
    return ids


async def _dial():
    conn = connection()
    if not conn:
        return None, {"ok": False, "connected": False,
                      "error": "Chưa kết nối Fathom. Mở Kết nối, tìm Fathom, bấm Kết nối."}
    spec = mcp_client._conn_spec(conn)
    spec["headers"].update(await mcp_client._oauth_headers(conn))
    try:
        tools = await mcp_client.pool.list_tools(spec)
    except Exception as e:
        return None, {"ok": False, "connected": True,
                      "error": "Không gọi được Fathom: " + type(e).__name__ + ": " + str(e)[:240]}
    return (conn, spec, tools), None


async def _call(spec: dict, tools: list, *needles: str, arguments: dict | None = None) -> str:
    name = _tool_name(tools, *needles)
    if not name:
        raise ValueError("Fathom MCP không có tool " + "/".join(needles))
    res = await mcp_client.pool.call_tool(spec, name, arguments or {})
    return str(res or "")


def _speaker_name(row: dict) -> str:
    who = row.get("speaker") or row.get("name")
    if isinstance(who, dict):
        return (who.get("display_name") or who.get("name") or "").strip()
    return str(who or "").strip()


def _text_from_payload(payload: Any) -> str:
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, list):
        return _text_from_payload({"transcript": payload})
    if not isinstance(payload, dict):
        return json.dumps(payload, ensure_ascii=False, indent=2) if payload else ""
    ds = payload.get("default_summary")
    if isinstance(ds, dict):
        md = ds.get("markdown_formatted") or ds.get("markdown") or ds.get("text")
        if isinstance(md, str) and md.strip():
            return md.strip()
    for k in ("transcript", "summary", "markdown_formatted", "text", "markdown", "content"):
        v = payload.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
        if isinstance(v, list):
            lines = []
            for row in v:
                if isinstance(row, str):
                    lines.append(row)
                elif isinstance(row, dict):
                    who = _speaker_name(row)
                    tx = (row.get("text") or row.get("content") or "").strip()
                    if tx and who:
                        lines.append(f"**{who}:** {tx}")
                    elif tx:
                        lines.append(tx)
            if lines:
                return "\n\n".join(lines)
    if payload.get("text"):
        return str(payload["text"])
    return json.dumps(payload, ensure_ascii=False, indent=2)


async def list_meetings(brain_root: str) -> dict:
    pack, err = await _dial()
    if err:
        return err
    _conn, spec, tools = pack
    last_err = None
    rows: list[dict] = []
    for args in (
        {"include_summary": True, "include_action_items": True},
        {"include_action_items": True},
        {},
    ):
        try:
            raw = await _call(
                spec, tools, "list_meetings", "listmeetings", arguments=args)
            payload = _parse_payload(raw)
            rows = _as_list(payload)
            last_err = None
            break
        except Exception as e:
            last_err = e
            rows = []
    if last_err and not rows:
        return {"ok": False, "connected": True, "error": str(last_err), "items": []}
    have = imported_ids(brain_root)
    items = []
    for row in rows:
        rid = _rec_id(row)
        if not rid:
            continue
        date_key, time_label = _item_when(row)
        summ = ""
        if isinstance(row.get("summary"), str):
            summ = row["summary"].strip()
        elif isinstance(row.get("default_summary"), dict):
            ds = row["default_summary"]
            summ = str(ds.get("markdown_formatted") or ds.get("markdown") or ds.get("text") or "")
        items.append({
            "recording_id": rid,
            "title": _item_title(row),
            "date": date_key,
            "time": time_label,
            "people": _people(row),
            "url": row.get("url") or row.get("share_url") or "",
            "action_items": row.get("action_items") or [],
            "excerpt": re.sub(r"\s+", " ", summ)[:220],
            "imported": rid in have,
        })
    return {"ok": True, "connected": True, "items": items, "total": len(items)}


def _write_vault(brain_root: str, *, recording_id: str, title: str,
                 date_key: str, time_label: str, people: list[str],
                 url: str, transcript: str, summary: str, actions: str) -> dict:
    mid = "fathom" + re.sub(r"[^a-zA-Z0-9]", "", recording_id)[:12]
    slug = meetings._slug(title)
    stamp = f"{date_key}-{time_label.replace(':', '') or '0000'}"
    base = meetings.meetings_dir(brain_root)
    md_path = base / f"{stamp}-{slug}-{mid}.md"
    if md_path.exists():
        md_path = base / f"{stamp}-{slug}-{mid}-b.md"
    people_line = ", ".join(people) if people else "(không ghi)"
    notes = ""
    if actions:
        notes = actions.strip() + "\n"
    if url:
        notes += ("" if not notes else "\n") + f"Link Fathom: {url}\n"
    live_block = f"## Ghi chú trong họp\n\n{notes}\n" if notes else "## Ghi chú trong họp\n\n"
    body_tx = (transcript or "").strip() or "(Fathom chưa có transcript.)"
    fm = (
        "---\n"
        "type: source\n"
        "source_kind: meeting\n"
        "status: processed\n"
        f"created: {_now_stamp()}\n"
        f"meeting_id: {mid}\n"
        f"fathom_recording_id: {json.dumps(str(recording_id), ensure_ascii=False)}\n"
        f"title: {json.dumps(title, ensure_ascii=False)}\n"
        f"attendees: {json.dumps(people, ensure_ascii=False)}\n"
        "tags: [meeting, fathom]\n"
        "---\n\n"
        f"# {title}\n\n"
        f"_Fathom · {date_key} {time_label}_\n\n"
        f"**Thành phần:** {people_line}\n\n"
        f"{live_block}"
        "## Transcript\n\n"
        f"{body_tx}\n"
    )
    md_path.write_text(fm, encoding="utf-8")
    rel_md = _rel(brain_root, md_path)
    rel_sum = ""
    if (summary or "").strip():
        sp = md_path.with_name(md_path.stem + "-summary.md")
        sp.write_text(
            "---\n"
            "type: source\n"
            "source_kind: meeting-summary\n"
            "status: processed\n"
            f"created: {_now_stamp()}\n"
            f"meeting_id: {mid}\n"
            f"source: {json.dumps(rel_md, ensure_ascii=False)}\n"
            "tags: [meeting, summary, fathom]\n"
            "---\n\n"
            f"# Tổng kết: {title}\n\n"
            f"{summary.strip()}\n",
            encoding="utf-8",
        )
        rel_sum = _rel(brain_root, sp)
    return {
        "ok": True,
        "recording_id": recording_id,
        "path": rel_md,
        "summary_path": rel_sum,
        "title": title,
    }


async def import_one(brain_root: str, recording_id: str, title: str = "",
                     meta: Optional[dict] = None) -> dict:
    rid = str(recording_id or "").strip()
    if not rid:
        return {"ok": False, "error": "Thiếu mã cuộc họp Fathom."}
    if rid in imported_ids(brain_root):
        return {"ok": True, "skipped": True, "recording_id": rid}
    pack, err = await _dial()
    if err:
        return err
    _conn, spec, tools = pack
    transcript = ""
    summary = ""
    actions = ""
    try:
        rec_arg = {"recording_id": int(rid) if rid.isdigit() else rid}
        raw_t = await _call(spec, tools, "get_meeting_transcript", "transcript",
                            arguments=rec_arg)
        transcript = _text_from_payload(_parse_payload(raw_t))
    except Exception as e:
        transcript = ""
        tx_err = str(e)
    else:
        tx_err = ""
    try:
        rec_arg = {"recording_id": int(rid) if rid.isdigit() else rid}
        raw_s = await _call(spec, tools, "get_meeting_summary", "summary",
                            arguments=rec_arg)
        summary = _text_from_payload(_parse_payload(raw_s))
    except Exception:
        summary = ""
    if not (transcript or summary):
        return {"ok": False, "error": "Fathom chưa có transcript/tóm tắt. "
                + (tx_err or "Thử lại sau khi cuộc họp xử lý xong.")}
    meta = meta or {}
    people = _people(meta)
    date_key, time_label = _item_when(meta) if meta else (
        datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M"))
    acts = meta.get("action_items") or meta.get("actionItems") or []
    if isinstance(acts, list) and acts:
        lines = []
        for a in acts:
            if isinstance(a, str):
                lines.append("- " + a)
            elif isinstance(a, dict):
                lines.append("- " + str(a.get("description") or a.get("text") or a.get("title") or a))
        actions = "Việc cần làm (Fathom):\n" + "\n".join(lines)
    return _write_vault(
        brain_root,
        recording_id=rid,
        title=(title or _item_title(meta) or "Cuộc họp Fathom"),
        date_key=date_key,
        time_label=time_label or "00:00",
        people=people,
        url=str(meta.get("url") or meta.get("share_url") or ""),
        transcript=transcript,
        summary=summary,
        actions=actions,
    )


async def sync_new(brain_root: str) -> dict:
    listed = await list_meetings(brain_root)
    if not listed.get("ok"):
        return listed
    todo = [x for x in (listed.get("items") or []) if not x.get("imported")]
    saved = []
    errors = []
    for item in todo[:SYNC_CAP]:
        r = await import_one(
            brain_root, item["recording_id"], title=item.get("title") or "",
            meta=item,
        )
        if r.get("ok") and not r.get("skipped"):
            saved.append(r)
        elif not r.get("ok"):
            errors.append((item.get("title") or item["recording_id"]) + ": " + (r.get("error") or "lỗi"))
    return {
        "ok": True,
        "connected": True,
        "imported": len(saved),
        "skipped": max(0, len(todo) - len(saved) - len(errors)),
        "remaining": max(0, len(todo) - SYNC_CAP),
        "items": saved,
        "errors": errors,
        "message": (
            f"Đã lưu {len(saved)} cuộc họp vào vault."
            + (f" Còn {len(todo) - SYNC_CAP} cuộc, bấm Đồng bộ lần nữa." if len(todo) > SYNC_CAP else "")
        ),
    }
