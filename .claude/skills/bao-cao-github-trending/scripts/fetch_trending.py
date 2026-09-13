#!/usr/bin/env python3
"""Lấy GitHub Trending (Today) — chỉ thư viện chuẩn. In JSON stdout.

GitHub không có API trending chính thức. Thứ tự:
  1) HTML https://github.com/trending
  2) JSON dự phòng (unofficial), nếu HTML lỗi

  python fetch_trending.py --since daily --limit 15
  python fetch_trending.py --html-file fixture.html
  python fetch_trending.py --json-file fixture.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from html import unescape
from typing import Any

VN = timezone(timedelta(hours=7))
UA = "Mozilla/5.0 (compatible; JavisOS/1.0; +https://github.com/duongcanhquan/javisOS)"
TRENDING = "https://github.com/trending"
# Gương JSON công khai (không chính thức). Chỉ dùng khi HTML lỗi.
JSON_MIRRORS = (
    "https://api.gitterapp.com/repositories",
)

_ARTICLE = re.compile(r"<article\b[^>]*>(.*?)</article>", re.I | re.S)
_H2 = re.compile(r"<h2\b[^>]*>(.*?)</h2>", re.I | re.S)
_HREF = re.compile(r'href="(/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)"', re.I)
_SKIP_OWNER = frozenset({
    "topics", "settings", "orgs", "users", "sponsors", "login",
    "marketplace", "explore", "features", "enterprise", "pricing",
})
_DESC = re.compile(r"<p\b[^>]*>(.*?)</p>", re.I | re.S)
_LANG = re.compile(
    r'itemprop="programmingLanguage"[^>]*>(.*?)</span>', re.I | re.S
)
_TODAY = re.compile(
    r"([\d,.]+)\s+stars?\s+today", re.I
)
_STARGAZERS = re.compile(
    r'href="(/[^"]+/stargazers)"[^>]*>(.*?)</a>', re.I | re.S
)
_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


def _now_vn() -> datetime:
    return datetime.now(VN)


def _strip(s: str) -> str:
    s = unescape(s or "")
    s = _TAG.sub(" ", s)
    return _WS.sub(" ", s).strip()


def _int(raw: str) -> int:
    digits = re.sub(r"[^\d]", "", raw or "")
    if not digits:
        return 0
    try:
        return int(digits)
    except ValueError:
        return 0


def parse_trending_html(html: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for block in _ARTICLE.findall(html or ""):
        h2 = _H2.search(block)
        hrefs = _HREF.findall(h2.group(1) if h2 else block)
        rel = ""
        for h in hrefs:
            if h.count("/") != 2:
                continue
            if any(x in h for x in ("/stargazers", "/issues", "/forks", "/pulls")):
                continue
            owner_try = h.strip("/").split("/")[0].lower()
            if owner_try in _SKIP_OWNER:
                continue
            rel = h
            break
        if not rel:
            continue
        parts = rel.strip("/").split("/")
        if len(parts) != 2:
            continue
        owner, name = parts[0], parts[1]
        if owner.lower() in _SKIP_OWNER:
            continue
        full = f"{owner}/{name}"
        if full in seen:
            continue
        seen.add(full)
        desc_m = _DESC.search(block)
        lang_m = _LANG.search(block)
        today_m = _TODAY.search(_strip(block))
        stars = 0
        sg = _STARGAZERS.search(block)
        if sg:
            stars = _int(_strip(sg.group(2)))
        items.append({
            "full_name": full,
            "owner": owner,
            "name": name,
            "url": "https://github.com/" + full,
            "description": _strip(desc_m.group(1)) if desc_m else "",
            "language": _strip(lang_m.group(1)) if lang_m else "",
            "stars": stars,
            "stars_today": _int(today_m.group(1)) if today_m else 0,
        })
    return items


def parse_mirror_json(raw: str) -> list[dict[str, Any]]:
    data = json.loads(raw or "[]")
    if isinstance(data, dict):
        data = data.get("items") or data.get("repositories") or []
    out: list[dict[str, Any]] = []
    if not isinstance(data, list):
        return out
    for row in data:
        if not isinstance(row, dict):
            continue
        owner = str(row.get("author") or row.get("owner") or "").strip()
        name = str(row.get("name") or "").strip()
        if isinstance(row.get("full_name"), str) and "/" in row["full_name"]:
            owner, name = row["full_name"].split("/", 1)
        if not owner or not name:
            continue
        url = str(row.get("url") or f"https://github.com/{owner}/{name}")
        out.append({
            "full_name": f"{owner}/{name}",
            "owner": owner,
            "name": name,
            "url": url,
            "description": str(row.get("description") or ""),
            "language": str(row.get("language") or ""),
            "stars": _int(str(row.get("stars") or row.get("totalStars") or 0)),
            "stars_today": _int(str(
                row.get("currentPeriodStars") or row.get("stars_today") or 0
            )),
        })
    return out


def fetch_url(url: str, timeout: int = 20) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


def _danh_sach_tho(items: list[dict[str, Any]]) -> str:
    lines = []
    for it in items:
        desc = it.get("description") or "(không có mô tả)"
        lang = it.get("language") or "?"
        today = it.get("stars_today") or 0
        lines.append(
            f"{it['rank']}. [{it['full_name']}]({it['url']}) · {lang} · +{today}★ hôm nay — {desc}"
        )
    return "\n".join(lines)


def build_result(
    items: list[dict[str, Any]],
    *,
    source: str,
    url: str,
    errors: list[str],
    limit: int,
    since: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    n = now or _now_vn()
    ranked = []
    for i, it in enumerate(items[: max(1, limit)], start=1):
        row = dict(it)
        row["rank"] = i
        ranked.append(row)
    return {
        "ok": bool(ranked),
        "timezone": "Asia/Ho_Chi_Minh",
        "date": n.strftime("%Y-%m-%d"),
        "date_human": n.strftime("%d/%m/%Y"),
        "since": since,
        "source": source,
        "url": url,
        "limit": limit,
        "count": len(ranked),
        "items": ranked,
        "danh_sach_tho": _danh_sach_tho(ranked),
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    p = argparse.ArgumentParser(description="Fetch GitHub Trending (stdlib)")
    p.add_argument("--since", default="daily", choices=("daily", "weekly", "monthly"))
    p.add_argument("--limit", type=int, default=15)
    p.add_argument("--spoken-language", default="", help="vd: vi (để trống = Any)")
    p.add_argument("--html-file", default="", help="Parse file HTML (test, không mạng)")
    p.add_argument("--json-file", default="", help="Parse file JSON gương (test)")
    p.add_argument("--no-network", action="store_true", help="Cấm fetch mạng")
    args = p.parse_args(argv)

    errors: list[str] = []
    q = {"since": args.since}
    if args.spoken_language:
        q["spoken_language"] = args.spoken_language
    page_url = TRENDING + "?" + urllib.parse.urlencode(q)

    items: list[dict[str, Any]] = []
    source = ""

    if args.html_file:
        html = open(args.html_file, encoding="utf-8").read()
        items = parse_trending_html(html)
        source = "html-file"
    elif args.json_file:
        raw = open(args.json_file, encoding="utf-8").read()
        items = parse_mirror_json(raw)
        source = "json-file"
    elif args.no_network:
        errors.append("no-network: cần --html-file hoặc --json-file")
    else:
        try:
            html = fetch_url(page_url)
            items = parse_trending_html(html)
            source = "github-trending-html"
            if not items:
                errors.append("HTML không tách được article — thử gương JSON")
        except Exception as e:  # noqa: BLE001
            errors.append(f"HTML {type(e).__name__}: {e}")
        if not items:
            for mirror in JSON_MIRRORS:
                try:
                    raw = fetch_url(mirror + "?" + urllib.parse.urlencode({"since": args.since}))
                    items = parse_mirror_json(raw)
                    if items:
                        source = "json-mirror"
                        break
                except Exception as e:  # noqa: BLE001
                    errors.append(f"{mirror}: {type(e).__name__}: {e}")

    out = build_result(
        items, source=source or "none", url=page_url,
        errors=errors, limit=args.limit, since=args.since,
    )
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
