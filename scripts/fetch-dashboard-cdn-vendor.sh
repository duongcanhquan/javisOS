#!/usr/bin/env bash
# Tải vendor dashboard từ CDN về máy chủ (mermaid, turndown, font) — trang không phụ thuộc mạng ngoài.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENDOR="$ROOT/dashboard/vendor"
CONTAINER="${JAVIS_CONTAINER:-javis}"
PERSIST="${JAVIS_DASHBOARD_VENDOR_DIR:-/root/javis-data/dashboard-vendor}"
mkdir -p "$VENDOR/fonts" "$VENDOR/mermaid" "$VENDOR/turndown"

echo "==> mermaid@10"
curl -L --fail --retry 3 -o "$VENDOR/mermaid/mermaid.min.js" \
  "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"

echo "==> turndown"
curl -L --fail --retry 3 -o "$VENDOR/turndown/turndown.js" \
  "https://unpkg.com/turndown@7.2.0/dist/turndown.js"
curl -L --fail --retry 3 -o "$VENDOR/turndown/turndown-plugin-gfm.js" \
  "https://unpkg.com/turndown-plugin-gfm@1.0.2/dist/turndown-plugin-gfm.js"

echo "==> Montserrat (google fonts css + woff2 chính)"
# CSS đã rewrite url → /static/vendor/fonts/
curl -L --fail --retry 3 -A "Mozilla/5.0" \
  -o "$VENDOR/fonts/montserrat.css" \
  "https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap"
# Tải các file woff2 được nhắc trong CSS
grep -oE 'https://fonts.gstatic.com/[^)]+' "$VENDOR/fonts/montserrat.css" | sort -u | while read -r url; do
  name=$(basename "$url" | cut -d'?' -f1)
  echo "  font $name"
  curl -L --fail --retry 3 -o "$VENDOR/fonts/$name" "$url" || true
done
# Rewrite CSS trỏ về cùng origin
sed -i.bak -E 's|https://fonts\.gstatic\.com/s/montserrat/[^/]+/|/static/vendor/fonts/|g' "$VENDOR/fonts/montserrat.css" \
  && rm -f "$VENDOR/fonts/montserrat.css.bak"
# gstatic paths are like .../v30/xxx.woff2 — basename is enough if we saved as basename
python3 - <<'PY' || true
from pathlib import Path
import re
p = Path("dashboard/vendor/fonts/montserrat.css")
if not p.is_file():
    raise SystemExit(0)
css = p.read_text(encoding="utf-8")
def repl(m):
    url = m.group(0)
    name = url.split("/")[-1].split("?")[0]
    return f"/static/vendor/fonts/{name}"
css2 = re.sub(r"https://fonts\.gstatic\.com/[^)\"']+", repl, css)
p.write_text(css2, encoding="utf-8")
print("rewrote montserrat.css urls")
PY

ls -lh "$VENDOR/mermaid" "$VENDOR/turndown" "$VENDOR/fonts" | head -40

# Persist ngoài container (sống qua recreate)
mkdir -p "$PERSIST"
rsync -a --delete "$VENDOR/mermaid/" "$PERSIST/mermaid/" 2>/dev/null \
  || { mkdir -p "$PERSIST/mermaid" && cp -a "$VENDOR/mermaid/." "$PERSIST/mermaid/"; }
rsync -a --delete "$VENDOR/turndown/" "$PERSIST/turndown/" 2>/dev/null \
  || { mkdir -p "$PERSIST/turndown" && cp -a "$VENDOR/turndown/." "$PERSIST/turndown/"; }
rsync -a --delete "$VENDOR/fonts/" "$PERSIST/fonts/" 2>/dev/null \
  || { mkdir -p "$PERSIST/fonts" && cp -a "$VENDOR/fonts/." "$PERSIST/fonts/"; }
echo "==> persist → $PERSIST"

if docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  echo "==> docker cp vào $CONTAINER"
  docker exec -u root "$CONTAINER" mkdir -p /app/dashboard/vendor
  docker cp "$PERSIST/mermaid" "$CONTAINER:/app/dashboard/vendor/"
  docker cp "$PERSIST/turndown" "$CONTAINER:/app/dashboard/vendor/"
  docker cp "$PERSIST/fonts" "$CONTAINER:/app/dashboard/vendor/"
  docker exec -u root "$CONTAINER" chmod -R a+rX /app/dashboard/vendor/mermaid /app/dashboard/vendor/turndown /app/dashboard/vendor/fonts
fi
echo "OK vendor CDN đã local"
