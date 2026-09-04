"""Kho nhận file từ kênh chat (Zalo / Telegram) - 3 tầng lưu trữ.

Tầng 1 inbox/<kênh>/     : vừa nhận, cache, media_gc có thể dọn
Tầng 2 received/         : kho làm việc trên brain (KHÔNG bị media_gc quét)
Tầng 3 sources/ + Drive  : lâu dài - Sources do engine/skill; Drive khi user bảo + đã đấu MCP

Sổ theo dõi: <brain>/Javis/received-index.json (tối đa 200 mục mới nhất).
"""
from __future__ import annotations

import json
import re
import shutil
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

_VN = timezone(timedelta(hours=7))
_INDEX_NAME = "received-index.json"
_MAX_INDEX = 200

# Caption / tin sau có ý "làm việc với file" → lên tầng 2 (hoặc để engine làm tầng 3).
_WORK_RE = re.compile(
    r"(phân\s*tích|đọc(\s+giúp|\s+file|\s+hộ)?|tóm\s*tắt|giữ(\s+lại)?|"
    r"lưu(\s*trữ|\s+lại|\s+vào)?|đưa\s*(lên\s*)?(drive|gg\s*drive|google\s*drive)|"
    r"triển\s*khai|xem\s+giúp|ocr|trích|"
    r"analyze|summarize|keep|save|upload|ingest|"
    r"ghi\s+vào\s+(source|sources|brain|wiki)|lưu\s+vào\s+(source|sources|drive))",
    re.I,
)

# Tin follow-up muốn đụng file vừa nhận (không kèm path).
_FOLLOW_RE = re.compile(
    r"(file|ảnh|tài\s*liệu|cái|bản)\s+(vừa|mới)\s+(gửi|nhận|gửi\s+lên)|"
    r"(phân\s*tích|đọc|tóm\s*tắt|giữ|lưu|đưa\s*.*drive|triển\s*khai).{0,40}"
    r"(file|ảnh|tài\s*liệu)?\s*(vừa|mới)?|"
    r"(file|ảnh)\s+(đó|này|kia)",
    re.I,
)

_PATH_IN_TEXT = re.compile(
    r"(đã tải về|tải về):\s*([^\]\n]+)|"
    r"(/[^\s\]\n]+/(?:inbox|received)/[^\s\]\n]+)",
    re.I,
)

_MARK_FILE = re.compile(
    r"\[Người dùng gửi .+?(?:đã tải về|gateway đã tải về):\s*(.+?)\]",
    re.I,
)


def _now_iso() -> str:
    return datetime.now(_VN).strftime("%Y-%m-%dT%H:%M:%S%z")


def _today() -> str:
    return datetime.now(_VN).strftime("%Y-%m-%d")


def index_path(brain_root) -> Path:
    d = Path(brain_root) / "Javis"
    d.mkdir(parents=True, exist_ok=True)
    return d / _INDEX_NAME


def received_dir(brain_root) -> Path:
    d = Path(brain_root) / "received"
    d.mkdir(parents=True, exist_ok=True)
    return d


def load_index(brain_root) -> List[dict]:
    p = index_path(brain_root)
    try:
        if p.is_file():
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []


def save_index(brain_root, items: List[dict]) -> None:
    p = index_path(brain_root)
    p.parent.mkdir(parents=True, exist_ok=True)
    trim = items[-_MAX_INDEX:]
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(trim, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(p)


def brain_from_inbox(inbox_dir) -> str:
    """inbox/telegram|zalo → brain root."""
    p = Path(inbox_dir).resolve()
    if p.name in ("telegram", "zalo") and p.parent.name == "inbox":
        return str(p.parent.parent)
    if p.name == "inbox":
        return str(p.parent)
    return str(p.parent)


def ten_an_toan(name: str) -> str:
    t = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", (name or "").strip()) or "file"
    return t[:120]


def ten_kho(channel: str, name: str, when: Optional[str] = None) -> str:
    """YYYY-MM-DD_kenh_ten-goc.ext"""
    day = (when or _today())[:10]
    ch = re.sub(r"[^a-z0-9]+", "", (channel or "chat").lower()) or "chat"
    base = ten_an_toan(name)
    return f"{day}_{ch}_{base}"


def co_y_lam_viec(text: str) -> bool:
    return bool(_WORK_RE.search(text or ""))


def co_theo_doi_file(text: str) -> bool:
    return bool(_FOLLOW_RE.search(text or ""))


def chi_nhan_thoi(caption: str, text: str) -> bool:
    """True = chỉ soft-ack, không gọi model.

    Không áp cho lệnh slash (/notes…) hay tin thoại (đã thành chữ lệnh).
    """
    cap = (caption or "").strip()
    t = (text or "").strip()
    if not t:
        return False
    if t.startswith("/") or cap.startswith("/"):
        return False
    if "Tin thoại" in t or "đã nghe thành chữ" in t:
        return False
    if co_y_lam_viec(cap) or co_y_lam_viec(t):
        return False
    # Phải là tin đính kèm (có marker tải về)
    if "đã tải về:" not in t and "gateway đã tải về:" not in t:
        return False
    return True


def trich_path(text: str) -> Optional[str]:
    if not text:
        return None
    m = _MARK_FILE.search(text)
    if m:
        return m.group(1).strip()
    m2 = _PATH_IN_TEXT.search(text)
    if m2:
        return (m2.group(2) or m2.group(0) or "").strip()
    return None


def ghi_nhan(brain_root, *, channel: str, path: str, name: str = "",
             kind: str = "file", caption: str = "", chat_id: str = "") -> dict:
    """Ghi sổ tầng 1 (file đã nằm inbox). Trả entry."""
    p = Path(path)
    entry = {
        "id": f"{int(time.time())}-{p.stem[:24]}",
        "ts": _now_iso(),
        "channel": channel,
        "chat_id": str(chat_id or ""),
        "kind": kind,
        "name": name or p.name,
        "path": str(p),
        "tier": "inbox",
        "caption": (caption or "")[:500],
    }
    items = load_index(brain_root)
    items.append(entry)
    save_index(brain_root, items)
    return entry


def promote(brain_root, path: str, channel: str = "", name: str = "") -> Optional[dict]:
    """Chuyển file từ inbox → received/ (tầng 2). Cập nhật sổ. Trả entry mới hoặc None."""
    src = Path(path)
    if not src.is_file():
        return None
    dest_name = ten_kho(channel or "chat", name or src.name)
    dest = received_dir(brain_root) / dest_name
    i = 1
    while dest.exists():
        dest = received_dir(brain_root) / f"{Path(dest_name).stem}_{i}{Path(dest_name).suffix}"
        i += 1
    try:
        shutil.move(str(src), str(dest))
    except Exception:
        try:
            shutil.copy2(str(src), str(dest))
        except Exception:
            return None
    items = load_index(brain_root)
    updated = None
    for e in reversed(items):
        if e.get("path") == str(src) or Path(e.get("path") or "").name == src.name:
            e["path"] = str(dest)
            e["tier"] = "received"
            e["promoted_ts"] = _now_iso()
            e["name"] = dest.name
            updated = e
            break
    if not updated:
        updated = {
            "id": f"{int(time.time())}-{dest.stem[:24]}",
            "ts": _now_iso(),
            "channel": channel,
            "kind": "file",
            "name": dest.name,
            "path": str(dest),
            "tier": "received",
            "caption": "",
        }
        items.append(updated)
    save_index(brain_root, items)
    return updated


def moi_nhat(brain_root, channel: str = "") -> Optional[dict]:
    items = load_index(brain_root)
    for e in reversed(items):
        if channel and e.get("channel") != channel:
            continue
        if e.get("path") and Path(e["path"]).is_file():
            return e
    return None


def cau_ack(entry: dict) -> str:
    # Plain text: Zalo không parse markdown; Telegram cũng đọc ổn không cần đậm.
    ten = entry.get("name") or "file"
    kenh = entry.get("channel") or "chat"
    return (
        f"Đã nhận {ten} ({kenh}).\n"
        f"Đang ở tầng trung chuyển (inbox) - dùng một lần / chờ lệnh.\n\n"
        f"Nhắn mình khi cần: phân tích, đọc, giữ vào kho làm việc, "
        f"hoặc đưa lên Drive / lưu Sources."
    )


def thay_path_trong_text(text: str, old: str, new: str) -> str:
    if not text or not old or not new:
        return text
    return text.replace(old, new)


def gan_vao_yeu_cau(text: str, entry: dict) -> str:
    """Gắn path file gần nhất vào tin follow-up để engine đọc được."""
    path = entry.get("path") or ""
    if not path:
        return text
    return (
        f"{text}\n\n"
        f"[File vừa nhận qua {entry.get('channel', 'chat')}, "
        f"đang ở tầng {entry.get('tier', '?')}: {path}]"
    )


def xu_ly_tin_dinh_kem(brain_root, text: str, caption: str, channel: str) -> Dict[str, Any]:
    """Sau khi ingest: quyết định soft-ack hoặc promote rồi để engine chạy.

    Trả {mode: 'ack'|'engine', text, reply?, entry?}
    """
    path = trich_path(text)
    entry = None
    if path and Path(path).is_file():
        # Có thể đã ghi_nhan ở bước ingest; tìm hoặc tạo mỏng
        for e in reversed(load_index(brain_root)):
            if e.get("path") == path:
                entry = e
                break
    if chi_nhan_thoi(caption, text):
        return {
            "mode": "ack",
            "text": text,
            "reply": cau_ack(entry or {
                "name": Path(path).name if path else "file",
                "channel": channel,
            }),
            "entry": entry,
        }
    # Có ý làm việc + còn ở inbox → lên tầng 2 trước khi engine đọc
    if path and co_y_lam_viec(caption or text):
        if "inbox" in path.replace("\\", "/"):
            promoted = promote(brain_root, path, channel=channel,
                               name=Path(path).name)
            if promoted:
                text = thay_path_trong_text(text, path, promoted["path"])
                entry = promoted
                text = (
                    f"{text}\n"
                    f"[Đã chuyển vào kho làm việc (tầng received): {promoted['path']}. "
                    f"Nếu user muốn lưu lâu dài lên Drive hoặc Sources thì làm theo yêu cầu.]"
                )
    return {"mode": "engine", "text": text, "entry": entry}


def xu_ly_tin_chu(brain_root, text: str, channel: str = "") -> str:
    """Tin chữ follow-up: nếu nhắc file vừa gửi mà chưa có path → gắn path mới nhất."""
    t = (text or "").strip()
    if not t or t.startswith("/"):
        return t
    if trich_path(t):
        return t
    if not (co_y_lam_viec(t) or co_theo_doi_file(t)):
        return t
    entry = moi_nhat(brain_root, channel=channel)
    if not entry:
        return t
    # Còn ở inbox mà user bảo giữ/phân tích → promote
    path = entry.get("path") or ""
    if entry.get("tier") == "inbox" and path and "inbox" in path.replace("\\", "/"):
        if co_y_lam_viec(t):
            promoted = promote(brain_root, path, channel=entry.get("channel") or channel,
                               name=entry.get("name") or "")
            if promoted:
                entry = promoted
    return gan_vao_yeu_cau(t, entry)
