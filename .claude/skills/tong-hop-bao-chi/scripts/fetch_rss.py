#!/usr/bin/env python3
"""Lọc bài RSS trong cửa sổ [hôm qua 00:00, hôm nay 08:00] giờ VN (UTC+7).

Chỉ dùng thư viện chuẩn. In JSON stdout để skill/agent đọc.
Cách gọi:
  python fetch_rss.py --config /path/to/bao-chi-cau-hinh.md
  python fetch_rss.py --feeds URL1,URL2 --topic "giáo dục đại học" --limit 10
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path
from typing import Any

VN = timezone(timedelta(hours=7))
UA = "Mozilla/5.0 (compatible; JavisOS/1.0; +https://github.com/duongcanhquan/javisOS)"


def _now_vn() -> datetime:
    return datetime.now(VN)


def _window(now: datetime | None = None) -> tuple[datetime, datetime]:
    """Hôm qua 00:00 → hôm nay 08:00 (VN)."""
    n = now or _now_vn()
    end = n.replace(hour=8, minute=0, second=0, microsecond=0)
    if n < end:
        # Trước 8h: cửa sổ kết thúc = 8h hôm nay; bắt đầu = 0h hôm qua.
        start = (end - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        # Sau 8h: vẫn lấy cửa sổ vừa qua (0h hôm qua → 8h hôm nay) trừ khi --today-open.
        start = (end - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return start, end


def _strip_html(s: str) -> str:
    s = unescape(s or "")
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _parse_date(raw: str) -> datetime | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        dt = parsedate_to_datetime(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=VN)
        return dt.astimezone(VN)
    except Exception:
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S"):
        try:
            t = raw.replace("Z", "+0000") if fmt.endswith("%z") else raw
            dt = datetime.strptime(t[:26].replace("+00:00", "+0000"), fmt.replace("%z", "%z") if "%z" in fmt else fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=VN)
            return dt.astimezone(VN)
        except Exception:
            continue
    return None


def _local(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag


def _text(el: ET.Element | None) -> str:
    if el is None:
        return ""
    return (el.text or "").strip()


def _child(parent: ET.Element, *names: str) -> ET.Element | None:
    want = {n.lower() for n in names}
    for c in list(parent):
        if _local(c.tag).lower() in want:
            return c
    return None


def parse_feed(xml_bytes: bytes, source_url: str) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_bytes)
    items: list[dict[str, Any]] = []
    # RSS 2.0
    for item in root.iter():
        if _local(item.tag).lower() != "item":
            continue
        title = _strip_html(_text(_child(item, "title")))
        link = _text(_child(item, "link"))
        if not link:
            guid = _child(item, "guid")
            if guid is not None and (guid.get("isPermaLink") or "true").lower() != "false":
                link = _text(guid)
        desc = _strip_html(_text(_child(item, "description")) or _text(_child(item, "summary")))
        pub = _parse_date(_text(_child(item, "pubDate", "published", "date", "updated")))
        if title and link:
            items.append({
                "title": title,
                "link": link,
                "summary": desc[:400],
                "published": pub.isoformat() if pub else "",
                "published_ts": pub.timestamp() if pub else 0,
                "source": source_url,
            })
    # Atom
    if not items:
        for entry in root.iter():
            if _local(entry.tag).lower() != "entry":
                continue
            title = _strip_html(_text(_child(entry, "title")))
            link = ""
            for c in list(entry):
                if _local(c.tag).lower() == "link":
                    href = c.get("href") or _text(c)
                    if href:
                        link = href
                        if (c.get("rel") or "alternate") == "alternate":
                            break
            desc = _strip_html(_text(_child(entry, "summary")) or _text(_child(entry, "content")))
            pub = _parse_date(_text(_child(entry, "published", "updated")))
            if title and link:
                items.append({
                    "title": title,
                    "link": link,
                    "summary": desc[:400],
                    "published": pub.isoformat() if pub else "",
                    "published_ts": pub.timestamp() if pub else 0,
                    "source": source_url,
                })
    return items


def fetch_url(url: str, timeout: int = 20) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/rss+xml, application/xml, text/xml, */*"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def match_topic(item: dict[str, Any], keywords: list[str]) -> bool:
    if not keywords:
        return True
    blob = f"{item.get('title','')} {item.get('summary','')}".lower()
    return any(k.lower() in blob for k in keywords if k.strip())


def load_config_md(path: Path) -> dict[str, Any]:
    """Đọc cấu hình đơn giản từ markdown: ## Nguồn RSS / ## Chủ đề mặc định / ## Từ khóa."""
    text = path.read_text(encoding="utf-8")
    feeds: list[str] = []
    topic = ""
    keywords: list[str] = []
    section = ""
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("## "):
            section = s[3:].strip().lower()
            continue
        if not s or s.startswith("#"):
            continue
        if section.startswith("nguồn") or section.startswith("rss") or "feed" in section:
            m = re.search(r"https?://\S+", s)
            if m:
                feeds.append(m.group(0).rstrip(").,]"))
        elif section.startswith("chủ đề"):
            if s.startswith("-"):
                s = s[1:].strip()
            if not topic:
                topic = s
        elif section.startswith("từ khóa") or section.startswith("tu khoa"):
            if s.startswith("-"):
                s = s[1:].strip()
            keywords.extend([x.strip() for x in re.split(r"[,;/|]", s) if x.strip()])
    return {"feeds": feeds, "topic": topic, "keywords": keywords}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", help="Đường dẫn Javis/bao-chi-cau-hinh.md")
    ap.add_argument("--feeds", help="URL RSS cách nhau bởi dấu phẩy")
    ap.add_argument("--topic", default="", help="Chủ đề quan tâm (nhãn)")
    ap.add_argument("--keywords", default="", help="Từ khóa lọc, cách nhau bởi dấu phẩy")
    ap.add_argument("--limit", type=int, default=10, help="Số bài mới nhất trả về")
    ap.add_argument("--no-filter-topic", action="store_true", help="Không lọc từ khóa, chỉ lọc thời gian")
    args = ap.parse_args()

    feeds: list[str] = []
    topic = (args.topic or "").strip()
    keywords = [x.strip() for x in (args.keywords or "").split(",") if x.strip()]

    if args.config:
        cfg = load_config_md(Path(args.config))
        feeds = cfg.get("feeds") or []
        topic = topic or (cfg.get("topic") or "")
        if not keywords:
            keywords = cfg.get("keywords") or []
    if args.feeds:
        feeds = [u.strip() for u in args.feeds.split(",") if u.strip()]

    if not feeds:
        print(json.dumps({"ok": False, "error": "Thiếu danh sách RSS (--feeds hoặc --config)"}, ensure_ascii=False))
        return 2

    start, end = _window()
    errors: list[str] = []
    all_items: list[dict[str, Any]] = []

    for url in feeds:
        try:
            raw = fetch_url(url)
            all_items.extend(parse_feed(raw, url))
        except Exception as e:  # noqa: BLE001
            errors.append(f"{url}: {type(e).__name__}: {e}")

    in_window: list[dict[str, Any]] = []
    for it in all_items:
        ts = it.get("published_ts") or 0
        if not ts:
            # Không có ngày: vẫn giữ tạm, xếp cuối; skill sẽ ghi chú.
            it["_no_date"] = True
            in_window.append(it)
            continue
        pub = datetime.fromtimestamp(ts, VN)
        if start <= pub <= end:
            in_window.append(it)

    if not args.no_filter_topic and keywords:
        matched = [it for it in in_window if match_topic(it, keywords)]
    else:
        matched = list(in_window)

    matched.sort(key=lambda x: x.get("published_ts") or 0, reverse=True)
    # Ưu tiên bài có ngày; bỏ bớt no_date nếu đã đủ limit
    dated = [x for x in matched if not x.get("_no_date")]
    undated = [x for x in matched if x.get("_no_date")]
    top = (dated + undated)[: max(1, args.limit)]

    out = {
        "ok": True,
        "timezone": "Asia/Ho_Chi_Minh",
        "window_start": start.isoformat(),
        "window_end": end.isoformat(),
        "topic": topic,
        "keywords": keywords,
        "feeds": feeds,
        "fetched": len(all_items),
        "in_window": len(in_window),
        "matched": len(matched),
        "limit": args.limit,
        "articles": [{k: v for k, v in a.items() if not k.startswith("_") and k != "published_ts"} for a in top],
        "errors": errors,
    }
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
