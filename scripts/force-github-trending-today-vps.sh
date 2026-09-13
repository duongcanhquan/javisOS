#!/usr/bin/env bash
# Ép báo cáo GitHub Trending chạy NGAY trên VPS (one-shot ~1 phút).
# Giữ nhắc cron 20h hàng ngày.
set -euo pipefail

CONTAINER="${JAVIS_CONTAINER:-javis}"
PORT="${JAVIS_PORT:-7777}"
LABEL="${GH_TRENDING_LABEL:-GitHub Trending 20h}"
BRAIN="${GH_TRENDING_BRAIN:-brain}"

echo "==> container: $CONTAINER"
if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  echo "ERROR: container '$CONTAINER' không chạy."
  exit 1
fi

docker exec -i -u javis \
  -e "JAVIS_PORT=$PORT" \
  -e "GH_LABEL=$LABEL" \
  -e "GH_BRAIN=$BRAIN" \
  "$CONTAINER" python - <<'PY'
import json, os, urllib.error, urllib.parse, urllib.request

port = os.environ.get("JAVIS_PORT", "7777")
base = f"http://127.0.0.1:{port}"
label = os.environ["GH_LABEL"]
brain = os.environ["GH_BRAIN"]


def call(method, path, data=None, form=False):
    url = base + path
    if data is None:
        req = urllib.request.Request(url, method=method)
    elif form:
        body = urllib.parse.urlencode({k: str(v) for k, v in data.items()}).encode()
        req = urllib.request.Request(
            url, data=body, method=method,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    else:
        raw = json.dumps(data, ensure_ascii=False).encode()
        req = urllib.request.Request(
            url, data=raw, method=method,
            headers={"Content-Type": "application/json"},
        )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            return json.loads(body)
        except Exception:
            return {"ok": False, "error": f"HTTP {e.code}: {body[:400]}"}


listed = call("GET", f"/reminders?brain={urllib.parse.quote(brain)}")
pending = listed.get("pending") or []
rem = next((r for r in pending if (r.get("label") or "") == label), None)
if not rem:
    raise SystemExit(
        f"ERROR: chưa có nhắc '{label}'. Chạy scripts/seed-github-trending-vps.sh trước."
    )

text = rem.get("text") or ""
one = call("POST", "/reminders", {
    "text": text,
    "label": f"{label} (chạy ngay)",
    "mode": "task",
    "brain": brain,
    "muc_quyen": rem.get("muc_quyen") or "suggest",
    "chat_id": rem.get("chat_id") or "all",
    "delay_min": 1,
    "created_by": "force-github-trending-today",
    "allow_no_channel": True,
})
print("oneshot:", json.dumps(one, ensure_ascii=False))
if not one.get("ok"):
    raise SystemExit(f"ERROR oneshot: {one}")
print(f"OK: bản hôm nay sẽ gửi trong ~1 phút (id={one.get('id')}, due={one.get('due_human')}).")
print("    Lịch 20h hàng ngày giữ nguyên.")
PY
