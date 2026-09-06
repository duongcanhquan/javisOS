#!/usr/bin/env python3
"""Lọc bài RSS theo danh mục trong cửa sổ [hôm qua 00:00, hôm nay 08:00] giờ VN.

Chỉ dùng thư viện chuẩn. In JSON stdout.
  python fetch_rss.py --config Javis/bao-chi-cau-hinh.md --category giao-duc
  python fetch_rss.py --config ... --list-categories
  python fetch_rss.py --feeds URL1,URL2 --topic "..." --limit 10
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
    n = now or _now_vn()
    end = n.replace(hour=8, minute=0, second=0, microsecond=0)
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
            dt = datetime.strptime(
                t[:26].replace("+00:00", "+0000"),
                fmt.replace("%z", "%z") if "%z" in fmt else fmt,
            )
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


def newspaper_name(url: str) -> str:
    """Tên báo đọc được từ URL feed hoặc link bài."""
    u = (url or "").lower()
    known = (
        ("vnexpress.net", "VnExpress"),
        ("tuoitre.vn", "Tuổi Trẻ"),
        ("thanhnien.vn", "Thanh Niên"),
        ("vietnamnet.vn", "VietnamNet"),
        ("dantri.com.vn", "Dân Trí"),
        ("zingnews.vn", "Zing News"),
        ("laodong.vn", "Lao Động"),
        ("nld.com.vn", "Người Lao Động"),
        ("cafef.vn", "CafeF"),
        ("vneconomy.vn", "VnEconomy"),
        ("baomoi.com", "Báo Mới"),
    )
    for host, name in known:
        if host in u:
            return name
    m = re.search(r"https?://(?:www\.)?([^/]+)", u)
    return m.group(1) if m else (url or "Không rõ")


def published_human(iso_or_ts: str | float | int | None) -> str:
    """Giờ xuất bản kiểu 05:36 06/09/2026 (VN)."""
    if iso_or_ts is None or iso_or_ts == "" or iso_or_ts == 0:
        return "không rõ giờ"
    try:
        if isinstance(iso_or_ts, (int, float)):
            dt = datetime.fromtimestamp(float(iso_or_ts), VN)
        else:
            raw = str(iso_or_ts).strip()
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=VN)
            dt = dt.astimezone(VN)
        return dt.strftime("%H:%M %d/%m/%Y")
    except Exception:
        return "không rõ giờ"


def parse_feed(xml_bytes: bytes, source_url: str) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_bytes)
    items: list[dict[str, Any]] = []
    paper = newspaper_name(source_url)

    def _item(title: str, link: str, desc: str, pub: datetime | None) -> dict[str, Any]:
        return {
            "title": title,
            "link": link,
            "summary": desc[:400],
            "published": pub.isoformat() if pub else "",
            "published_ts": pub.timestamp() if pub else 0,
            "published_human": published_human(pub.timestamp() if pub else 0),
            "source": source_url,
            "source_name": paper,
        }

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
            row = _item(title, link, desc, pub)
            # Ưu tiên tên báo từ domain link bài nếu rõ hơn
            row["source_name"] = newspaper_name(link) or paper
            items.append(row)
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
                row = _item(title, link, desc, pub)
                row["source_name"] = newspaper_name(link) or paper
                items.append(row)
    return items


def fetch_url(url: str, timeout: int = 20) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def match_topic(item: dict[str, Any], keywords: list[str]) -> bool:
    if not keywords:
        return True
    blob = f"{item.get('title', '')} {item.get('summary', '')}".lower()
    return any(k.lower() in blob for k in keywords if k.strip())


def _slugify(s: str) -> str:
    import unicodedata

    s = (s or "").strip().lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("đ", "d")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def load_config_md(path: Path) -> dict[str, Any]:
    """Đọc cấu hình: danh mục (## Danh mục: slug) hoặc format cũ (một khối RSS)."""
    text = path.read_text(encoding="utf-8")
    default_cat = ""
    categories: dict[str, dict[str, Any]] = {}
    # legacy flat
    legacy_feeds: list[str] = []
    legacy_topic = ""
    legacy_keywords: list[str] = []

    section = ""  # top-level ## 
    cat_slug = ""
    sub = ""  # ### trong danh mục

    for line in text.splitlines():
        s = line.strip()
        if s.startswith("## "):
            title = s[3:].strip()
            low = title.lower()
            m = re.match(r"danh\s*mục\s*:\s*(.+)$", title, re.I)
            if m:
                cat_slug = _slugify(m.group(1))
                categories.setdefault(cat_slug, {"slug": cat_slug, "label": "", "feeds": [], "keywords": []})
                section = "category"
                sub = ""
                continue
            cat_slug = ""
            sub = ""
            if "mặc định" in low or "mac dinh" in low:
                section = "default"
            elif low.startswith("nguồn") or low.startswith("rss") or "feed" in low:
                section = "legacy_feeds"
            elif low.startswith("chủ đề") or low.startswith("chu de"):
                section = "legacy_topic"
            elif low.startswith("từ khóa") or low.startswith("tu khoa"):
                section = "legacy_keywords"
            else:
                section = ""
            continue
        if s.startswith("### "):
            sub = s[4:].strip().lower()
            continue
        if not s or s.startswith("#"):
            continue

        if section == "default":
            if s.startswith("-"):
                s = s[1:].strip()
            if s and not default_cat:
                default_cat = _slugify(s)
            continue

        if section == "category" and cat_slug:
            cat = categories[cat_slug]
            if sub.startswith("nhãn") or sub.startswith("nhan") or sub.startswith("tên"):
                if s.startswith("-"):
                    s = s[1:].strip()
                if s and not cat["label"]:
                    cat["label"] = s
            elif sub.startswith("rss") or sub.startswith("nguồn") or "feed" in sub:
                m = re.search(r"https?://\S+", s)
                if m:
                    cat["feeds"].append(m.group(0).rstrip(").,]"))
            elif sub.startswith("từ khóa") or sub.startswith("tu khoa") or sub.startswith("keyword"):
                if s.startswith("-"):
                    s = s[1:].strip()
                cat["keywords"].extend([x.strip() for x in re.split(r"[,;/|]", s) if x.strip()])
            continue

        if section == "legacy_feeds":
            m = re.search(r"https?://\S+", s)
            if m:
                legacy_feeds.append(m.group(0).rstrip(").,]"))
        elif section == "legacy_topic":
            if s.startswith("-"):
                s = s[1:].strip()
            if s and not legacy_topic:
                legacy_topic = s
        elif section == "legacy_keywords":
            if s.startswith("-"):
                s = s[1:].strip()
            legacy_keywords.extend([x.strip() for x in re.split(r"[,;/|]", s) if x.strip()])

    # Migrate format cũ → một danh mục
    if not categories and legacy_feeds:
        slug = default_cat or "mac-dinh"
        categories[slug] = {
            "slug": slug,
            "label": legacy_topic or slug,
            "feeds": legacy_feeds,
            "keywords": legacy_keywords,
        }
        default_cat = default_cat or slug

    if not default_cat and categories:
        default_cat = next(iter(categories.keys()))

    return {
        "default_category": default_cat,
        "categories": categories,
        # tương thích cũ
        "feeds": (categories.get(default_cat) or {}).get("feeds") or legacy_feeds,
        "topic": (categories.get(default_cat) or {}).get("label") or legacy_topic,
        "keywords": (categories.get(default_cat) or {}).get("keywords") or legacy_keywords,
    }


def resolve_category(cfg: dict[str, Any], wanted: str) -> dict[str, Any]:
    cats: dict[str, dict[str, Any]] = cfg.get("categories") or {}
    slug = _slugify(wanted) if wanted else (cfg.get("default_category") or "")
    if slug and slug in cats:
        return cats[slug]
    # alias mềm
    aliases = {
        "giao-duc": ["giao-duc", "education", "edu", "gd"],
        "tai-chinh": ["tai-chinh", "finance", "kinh-doanh", "tc"],
        "bat-dong-san": ["bat-dong-san", "bds", "real-estate", "nha-dat"],
    }
    want = slug
    for canon, al in aliases.items():
        if want in al or want == canon:
            if canon in cats:
                return cats[canon]
    if cfg.get("default_category") in cats:
        return cats[cfg["default_category"]]
    if cats:
        return next(iter(cats.values()))
    return {"slug": slug or "unknown", "label": "", "feeds": [], "keywords": []}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", help="Đường dẫn Javis/bao-chi-cau-hinh.md")
    ap.add_argument("--category", "-c", default="", help="Slug danh mục: giao-duc, tai-chinh, bat-dong-san…")
    ap.add_argument("--list-categories", action="store_true", help="In danh mục trong config rồi thoát")
    ap.add_argument("--feeds", help="URL RSS cách nhau bởi dấu phẩy (bỏ qua category)")
    ap.add_argument("--topic", default="", help="Nhãn chủ đề (ghi đè nhãn danh mục)")
    ap.add_argument("--keywords", default="", help="Từ khóa lọc, cách nhau bởi dấu phẩy")
    ap.add_argument("--limit", type=int, default=10, help="Số bài mới nhất trả về")
    ap.add_argument("--no-filter-topic", action="store_true", help="Không lọc từ khóa, chỉ lọc thời gian")
    args = ap.parse_args()

    feeds: list[str] = []
    topic = (args.topic or "").strip()
    keywords = [x.strip() for x in (args.keywords or "").split(",") if x.strip()]
    category_slug = ""
    cfg: dict[str, Any] = {}

    if args.config:
        cfg = load_config_md(Path(args.config))
        if args.list_categories:
            out = {
                "ok": True,
                "default_category": cfg.get("default_category"),
                "categories": [
                    {
                        "slug": c["slug"],
                        "label": c.get("label") or c["slug"],
                        "feeds": len(c.get("feeds") or []),
                        "keywords": len(c.get("keywords") or []),
                    }
                    for c in (cfg.get("categories") or {}).values()
                ],
            }
            json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
            print()
            return 0
        cat = resolve_category(cfg, args.category)
        category_slug = cat.get("slug") or ""
        feeds = list(cat.get("feeds") or [])
        topic = topic or (cat.get("label") or category_slug)
        if not keywords:
            keywords = list(cat.get("keywords") or [])
    elif args.list_categories:
        print(json.dumps({"ok": False, "error": "Cần --config để liệt kê danh mục"}, ensure_ascii=False))
        return 2

    if args.feeds:
        feeds = [u.strip() for u in args.feeds.split(",") if u.strip()]
        category_slug = category_slug or "custom"

    if not feeds:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "Thiếu RSS (--category trong config hoặc --feeds)",
                    "category": category_slug or args.category,
                    "available": list((cfg.get("categories") or {}).keys()),
                },
                ensure_ascii=False,
            )
        )
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
    dated = [x for x in matched if not x.get("_no_date")]
    undated = [x for x in matched if x.get("_no_date")]
    top = (dated + undated)[: max(1, args.limit)]

    out = {
        "ok": True,
        "timezone": "Asia/Ho_Chi_Minh",
        "window_start": start.isoformat(),
        "window_end": end.isoformat(),
        "category": category_slug,
        "topic": topic,
        "keywords": keywords,
        "feeds": feeds,
        "fetched": len(all_items),
        "in_window": len(in_window),
        "matched": len(matched),
        "limit": args.limit,
        "articles": [
            {k: v for k, v in a.items() if not k.startswith("_") and k != "published_ts"}
            for a in top
        ],
        "errors": errors,
    }
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
