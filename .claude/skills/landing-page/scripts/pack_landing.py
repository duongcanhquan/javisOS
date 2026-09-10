#!/usr/bin/env python3
"""Zip a landing folder for handoff (HTML/MD/assets).

Usage:
  python3 pack_landing.py /path/to/exports/landing/<slug>

Writes landing-<slug>.zip next to the folder (inside the folder by default).
Excludes: .DS_Store, __pycache__, nested *.zip (avoid recursion).
"""
from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

SKIP_NAMES = {".DS_Store", "Thumbs.db"}
SKIP_SUFFIXES = {".pyc"}


def main() -> int:
    ap = argparse.ArgumentParser(description="Pack landing folder to zip")
    ap.add_argument("folder", type=Path, help="exports/landing/<slug> directory")
    ap.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output zip path (default: <folder>/landing-<slug>.zip)",
    )
    args = ap.parse_args()
    root = args.folder.expanduser().resolve()
    if not root.is_dir():
        print(f"ERROR: not a directory: {root}", file=sys.stderr)
        return 2
    slug = root.name
    out = args.output.expanduser().resolve() if args.output else root / f"landing-{slug}.zip"
    if out.exists():
        out.unlink()

    count = 0
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            if path.resolve() == out:
                continue
            if path.name in SKIP_NAMES or path.suffix in SKIP_SUFFIXES:
                continue
            if path.suffix.lower() == ".zip":
                continue
            arc = path.relative_to(root).as_posix()
            zf.write(path, arcname=f"{slug}/{arc}")
            count += 1

    print(f"OK {out} ({count} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
