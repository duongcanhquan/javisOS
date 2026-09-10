#!/usr/bin/env python3
"""Pack research Markdown into HTML / PDF / simple PPTX under exports/research/<slug>/."""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape


def find_vault(start: Path) -> Path:
    cur = start.resolve()
    for p in [cur, *cur.parents]:
        if (p / "sources").is_dir() and (p / "skills").is_dir():
            return p
    return cur


def md_to_html_body(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    in_ul = False
    in_code = False
    para: list[str] = []

    def flush_para() -> None:
        nonlocal para
        if para:
            out.append("<p>" + " ".join(para) + "</p>")
            para = []

    def close_ul() -> None:
        nonlocal in_ul
        if in_ul:
            out.append("</ul>")
            in_ul = False

    for raw in lines:
        line = raw.rstrip()
        if line.startswith("```"):
            flush_para()
            close_ul()
            if in_code:
                out.append("</code></pre>")
                in_code = False
            else:
                out.append("<pre><code>")
                in_code = True
            continue
        if in_code:
            out.append(html.escape(line))
            continue
        if not line.strip():
            flush_para()
            close_ul()
            continue
        if line.startswith("# "):
            flush_para()
            close_ul()
            out.append(f"<h1>{inline_md(line[2:])}</h1>")
        elif line.startswith("## "):
            flush_para()
            close_ul()
            out.append(f"<h2>{inline_md(line[3:])}</h2>")
        elif line.startswith("### "):
            flush_para()
            close_ul()
            out.append(f"<h3>{inline_md(line[4:])}</h3>")
        elif re.match(r"^[-*] ", line):
            flush_para()
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{inline_md(line[2:])}</li>")
        elif re.match(r"^\d+\. ", line):
            flush_para()
            close_ul()
            out.append(f"<p>{inline_md(line)}</p>")
        elif re.match(r"^!\[", line):
            flush_para()
            close_ul()
            m = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", line.strip())
            if m:
                alt, src = m.group(1), m.group(2)
                out.append(
                    f'<figure><img src="{html.escape(src)}" alt="{html.escape(alt)}" />'
                    f"<figcaption>{html.escape(alt)}</figcaption></figure>"
                )
        else:
            close_ul()
            para.append(inline_md(line))
    flush_para()
    close_ul()
    if in_code:
        out.append("</code></pre>")
    return "\n".join(out)


def inline_md(s: str) -> str:
    s = html.escape(s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        r'<a href="\2">\1</a>',
        s,
    )
    return s


def collect_md(src_dir: Path) -> list[Path]:
    files = sorted(src_dir.glob("*.md"))
    return [p for p in files if p.is_file()]


def build_html(title: str, parts: list[tuple[str, str]], vault: Path) -> str:
    body_parts = []
    for name, text in parts:
        body_parts.append(f'<section class="doc"><header>{html.escape(name)}</header>')
        body_parts.append(md_to_html_body(text))
        body_parts.append("</section>")
    css = """
    :root { --ink:#1a1a1a; --muted:#555; --line:#ddd; --accent:#0b5fff; }
    body { font: 15px/1.55 "Segoe UI", system-ui, sans-serif; color: var(--ink);
           max-width: 820px; margin: 40px auto; padding: 0 24px; }
    h1 { font-size: 1.7rem; margin-top: 0; }
    h2 { font-size: 1.25rem; border-bottom: 1px solid var(--line); padding-bottom: .2em; }
    h3 { font-size: 1.05rem; }
    .cover { margin-bottom: 2.5rem; }
    .cover .meta { color: var(--muted); font-size: .9rem; }
    .doc { page-break-before: always; margin-top: 2rem; }
    .doc header { font-size: .75rem; letter-spacing: .04em; text-transform: uppercase;
                  color: var(--muted); margin-bottom: .75rem; }
    img { max-width: 100%; height: auto; border: 1px solid var(--line); }
    figure { margin: 1rem 0; }
    figcaption { font-size: .85rem; color: var(--muted); }
    ul { padding-left: 1.2rem; }
    code { background: #f4f4f4; padding: .1em .35em; border-radius: 3px; }
    pre { background: #f4f4f4; padding: 12px; overflow: auto; }
    a { color: var(--accent); }
    @media print { body { margin: 0; max-width: none; } .doc { page-break-before: always; } }
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""<!DOCTYPE html>
<html lang="vi"><head><meta charset="utf-8"/>
<title>{html.escape(title)}</title>
<style>{css}</style></head><body>
<div class="cover">
  <h1>{html.escape(title)}</h1>
  <p class="meta">Gói nghiên cứu thị trường · xuất {now}</p>
</div>
{"".join(body_parts)}
</body></html>"""


def chrome_bin() -> str | None:
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
    ]
    for c in candidates:
        if c and Path(c).exists():
            return c
    return None


def export_pdf(html_path: Path, pdf_path: Path) -> bool:
    bin_ = chrome_bin()
    if not bin_:
        return False
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        bin_,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        html_path.resolve().as_uri(),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)
        return pdf_path.is_file() and pdf_path.stat().st_size > 0
    except (subprocess.SubprocessError, OSError):
        return False


def extract_slides(parts: list[tuple[str, str]], title: str) -> list[tuple[str, list[str]]]:
    slides: list[tuple[str, list[str]]] = [(title, ["Gói nghiên cứu thị trường", "Javis OS export"])]
    for name, text in parts:
        slides.append((name.replace(".md", ""), ["Nguồn: " + name]))
        current = None
        bullets: list[str] = []
        for line in text.splitlines():
            if line.startswith("## "):
                if current:
                    slides.append((current, bullets[:8] or ["(xem báo cáo đầy đủ)"]))
                current = line[3:].strip()
                bullets = []
            elif line.startswith("### ") and current is None:
                current = line[4:].strip()
                bullets = []
            elif re.match(r"^[-*] ", line) and current:
                bullets.append(line[2:].strip()[:160])
                if len(bullets) >= 8:
                    slides.append((current, bullets))
                    current = current + " (tt)"
                    bullets = []
        if current:
            slides.append((current, bullets[:8] or ["(xem báo cáo đầy đủ)"]))
    return slides[:40]


def write_pptx(path: Path, slides: list[tuple[str, list[str]]]) -> None:
    """Minimal PPTX (Office Open XML) without python-pptx."""
    path.parent.mkdir(parents=True, exist_ok=True)
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
  <Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
  <Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
"""
    for i in range(1, len(slides) + 1):
        content_types += (
            f'  <Override PartName="/ppt/slides/slide{i}.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>\n'
        )
    content_types += "</Types>"

    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
</Relationships>"""

    pres_rels = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
                 '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">']
    for i in range(1, len(slides) + 1):
        pres_rels.append(
            f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i}.xml"/>'
        )
    n = len(slides)
    mid = n + 1
    pres_rels.append(
        f'<Relationship Id="rId{mid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>'
    )
    pres_rels.append(
        f'<Relationship Id="rId{mid+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>'
    )
    pres_rels.append("</Relationships>")

    sld_ids = []
    for i in range(1, n + 1):
        sld_ids.append(f'<p:sldId id="{255 + i}" r:id="rId{i}"/>')
    presentation = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId{mid}"/></p:sldMasterIdLst>
  <p:sldIdLst>{"".join(sld_ids)}</p:sldIdLst>
  <p:sldSz cx="12192000" cy="6858000"/>
  <p:notesSz cx="6858000" cy="9144000"/>
</p:presentation>"""

    theme = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Javis">
  <a:themeElements>
    <a:clrScheme name="Javis"><a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>
      <a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>
      <a:dk2><a:srgbClr val="1A1A1A"/></a:dk2><a:lt2><a:srgbClr val="F5F5F5"/></a:lt2>
      <a:accent1><a:srgbClr val="0B5FFF"/></a:accent1><a:accent2><a:srgbClr val="0B5FFF"/></a:accent2>
      <a:accent3><a:srgbClr val="0B5FFF"/></a:accent3><a:accent4><a:srgbClr val="0B5FFF"/></a:accent4>
      <a:accent5><a:srgbClr val="0B5FFF"/></a:accent5><a:accent6><a:srgbClr val="0B5FFF"/></a:accent6>
      <a:hlink><a:srgbClr val="0B5FFF"/></a:hlink><a:folHlink><a:srgbClr val="0B5FFF"/></a:folHlink>
    </a:clrScheme>
    <a:fontScheme name="Javis">
      <a:majorFont><a:latin typeface="Calibri"/><a:ea typeface=""/><a:cs typeface=""/></a:majorFont>
      <a:minorFont><a:latin typeface="Calibri"/><a:ea typeface=""/><a:cs typeface=""/></a:minorFont>
    </a:fontScheme>
    <a:fmtScheme name="Javis">
      <a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst>
      <a:lnStyleLst><a:ln w="12700"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>
        <a:ln w="12700"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>
        <a:ln w="12700"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst>
      <a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle>
        <a:effectStyle><a:effectLst/></a:effectStyle>
        <a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst>
      <a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst>
    </a:fmtScheme>
  </a:themeElements>
</a:theme>"""

    slide_layout = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1">
  <p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
    <p:grpSpPr/></p:spTree></p:cSld></p:sldLayout>"""

    slide_master = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:bg><p:bgPr><a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill></p:bgPr></p:bg>
    <p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
    <p:grpSpPr/></p:spTree></p:cSld>
  <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2"
    accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
  <p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>
</p:sldMaster>"""

    master_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>
</Relationships>"""

    layout_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>"""

    def slide_xml(stitle: str, bullets: list[str]) -> str:
        title_esc = escape(stitle[:120])
        paras = []
        for b in bullets[:8]:
            paras.append(
                f'<a:p><a:pPr marL="342900" indent="-342900"><a:buFont typeface="Arial"/>'
                f'<a:buChar char="•"/></a:pPr><a:r><a:rPr lang="vi-VN" sz="1800"/>'
                f"<a:t>{escape(b)}</a:t></a:r></a:p>"
            )
        if not paras:
            paras.append('<a:p><a:endParaRPr lang="vi-VN"/></a:p>')
        body = "".join(paras)
        return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:spTree>
    <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/>
    <p:sp>
      <p:nvSpPr><p:cNvPr id="2" name="Title"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="457200" y="274320"/><a:ext cx="11277600" cy="914400"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>
      <p:txBody><a:bodyPr/><a:lstStyle/>
        <a:p><a:r><a:rPr lang="vi-VN" sz="2800" b="1"/><a:t>{title_esc}</a:t></a:r></a:p>
      </p:txBody>
    </p:sp>
    <p:sp>
      <p:nvSpPr><p:cNvPr id="3" name="Body"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="457200" y="1371600"/><a:ext cx="11277600" cy="4572000"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>
      <p:txBody><a:bodyPr/><a:lstStyle/>{body}</p:txBody>
    </p:sp>
  </p:spTree></p:cSld>
</p:sld>"""

    slide_rel = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
</Relationships>"""

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("ppt/presentation.xml", presentation)
        z.writestr("ppt/_rels/presentation.xml.rels", "\n".join(pres_rels))
        z.writestr("ppt/theme/theme1.xml", theme)
        z.writestr("ppt/slideMasters/slideMaster1.xml", slide_master)
        z.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", master_rels)
        z.writestr("ppt/slideLayouts/slideLayout1.xml", slide_layout)
        z.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", layout_rels)
        for i, (st, bullets) in enumerate(slides, 1):
            z.writestr(f"ppt/slides/slide{i}.xml", slide_xml(st, bullets))
            z.writestr(f"ppt/slides/_rels/slide{i}.xml.rels", slide_rel)


def main() -> int:
    ap = argparse.ArgumentParser(description="Export research pack to HTML/PDF/PPTX")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--vault", default="")
    ap.add_argument("--title", default="")
    ap.add_argument("--formats", default="pdf,pptx,html", help="Comma: pdf,pptx,html")
    args = ap.parse_args()

    vault = Path(args.vault) if args.vault else find_vault(Path.cwd())
    src = vault / "sources" / "research" / args.slug
    out = vault / "exports" / "research" / args.slug
    out.mkdir(parents=True, exist_ok=True)

    if not src.is_dir():
        print(json.dumps({"ok": False, "error": f"missing {src}"}, ensure_ascii=False))
        return 1

    md_files = collect_md(src)
    if not md_files:
        print(json.dumps({"ok": False, "error": "no markdown in source dir"}, ensure_ascii=False))
        return 1

    parts = [(p.name, p.read_text(encoding="utf-8")) for p in md_files]
    title = args.title.strip() or f"Nghiên cứu thị trường - {args.slug}"
    formats = {f.strip().lower() for f in args.formats.split(",") if f.strip()}

    result: dict = {"ok": True, "slug": args.slug, "vault": str(vault), "out": str(out), "files": {}}

    html_path = out / "report.html"
    if "html" in formats or "pdf" in formats:
        html_path.write_text(build_html(title, parts, vault), encoding="utf-8")
        result["files"]["html"] = str(html_path)

    if "pdf" in formats:
        pdf_path = out / "report.pdf"
        if export_pdf(html_path, pdf_path):
            result["files"]["pdf"] = str(pdf_path)
        else:
            result["pdf_error"] = "Chrome/Chromium not available or print failed; use report.html"

    if "pptx" in formats:
        pptx_path = out / "deck.pptx"
        write_pptx(pptx_path, extract_slides(parts, title))
        result["files"]["pptx"] = str(pptx_path)

    (out / "manifest.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
