#!/usr/bin/env bash
# Dọn VPS Javis: bỏ cấu hình chết (Llama/Ollama local), prune Docker an toàn, kiểm tra hàm sống.
# Idempotent. Chạy trên host trong thư mục repo (sau deploy hoặc tay).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONTAINER="${JAVIS_CONTAINER:-javis}"
cd "$ROOT"

echo "============================================"
echo " Javis VPS cleanup"
echo "============================================"

RAM_MB=$(awk '/MemTotal/ {print int($2/1024)}' /proc/meminfo 2>/dev/null || echo 0)
FREE_GB=$(df -BG / 2>/dev/null | awk 'NR==2 {gsub(/G/,"",$4); print $4}' || echo "?")
echo "RAM: ${RAM_MB} MB · đĩa trống: ~${FREE_GB} GB"

# Không gọi apply-model-routing: mỗi deploy từng ghi đè ghim Telegram/Zalo về Antigravity.
# Không gỡ Ollama ở đây: vps-deploy.sh chỉ gỡ khi host còn binary/service.

# --- Docker prune AN TOÀN (không đụng volume brains/state) ---
echo
echo "==> Docker prune (images/containers/network dư, GIỮ volumes)"
docker container prune -f 2>/dev/null || true
docker image prune -af 2>/dev/null || true
docker network prune -f 2>/dev/null || true
docker builder prune -af 2>/dev/null || true
echo "đĩa sau prune: $(df -BG / 2>/dev/null | awk 'NR==2 {print $4}')"

# --- 4. Kiểm tra hàm sống trong container (tránh 500 xoá kết nối / 404 Llama) ---
if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  echo "WARN: container '$CONTAINER' không chạy - bỏ qua kiểm tra nội bộ"
else
  echo
  echo "==> Kiểm tra settings + API sống"
  docker exec -i -u javis "$CONTAINER" python - <<'PY'
import sys
sys.path.insert(0, "/app/server")
import config as cfg
import engine
import mcp_client
import mcp_hub
from capability_registry import CapabilityRegistry

s = cfg.read_settings()
m = s.get("model") or {}
main = m.get("main") or {}
aux = m.get("auxiliary") or {}
tg = m.get("telegram") or {}
print("VERSION file:", open("/app/VERSION").read().strip() if __import__("pathlib").Path("/app/VERSION").is_file() else "?")
print("main:", main)
print("auxiliary:", aux)
print("telegram/messaging pin:", tg)
print("ollama_local_endpoint:", (m.get("ollama_local_endpoint") or "").strip() or "(đã xóa - OK)")
print("lazy_tools:", (s.get("mcp") or {}).get("lazy_tools"))
print("has_groq_key:", bool((m.get("groq_api_key") or "").strip()))
print("has_gemini_key:", bool((m.get("gemini_api_key") or "").strip()))
print("has_deepseek_key:", bool((m.get("deepseek_api_key") or "").strip()))
print("has_openrouter_key:", bool((m.get("openrouter_key") or "").strip()))

loi = []
for slot, block in (("main", main), ("auxiliary", aux), ("telegram", tg)):
    if (block.get("provider") or "") == "groq" and "llama" in (block.get("model") or "").lower():
        loi.append(f"{slot} vẫn ghim Llama: {block.get('model')}")
if (m.get("ollama_local_endpoint") or "").strip():
    loi.append("còn ollama_local_endpoint")

# Hàm sống (xoá kết nối / remap Groq)
for ten, ok in (
    ("pool.close_now", callable(getattr(mcp_client.pool, "close_now", None))),
    ("pool.dang_ban_theo_key", callable(getattr(mcp_client.pool, "dang_ban_theo_key", None))),
    ("mcp_hub.forget_rate", callable(getattr(mcp_hub, "forget_rate", None))),
    ("mcp_hub.audit_scrub", callable(getattr(mcp_hub, "audit_scrub", None))),
    ("CapabilityRegistry.drop_connection", callable(getattr(CapabilityRegistry, "drop_connection", None))),
    ("engine.groq_resolve_model", callable(getattr(engine, "groq_resolve_model", None))),
):
    print(f"  {ten}: {'OK' if ok else 'MISSING'}")
    if not ok:
        loi.append(f"thiếu {ten}")

if hasattr(engine, "groq_resolve_model"):
    got = engine.groq_resolve_model("llama-3.3-70b-versatile")
    print("  remap llama-3.3 ->", got)
    if "llama" in got.lower():
        loi.append("remap Llama thất bại")

if loi:
    print("CLEANUP_FAIL:")
    for x in loi:
        print(" -", x)
    sys.exit(1)
print("CLEANUP_OK")
PY
fi

# --- 5. Health ---
echo
echo "==> /health"
ok=0
for i in 1 2 3 4 5 6; do
  if curl -fsS -m 5 http://127.0.0.1:7777/health; then
    echo
    ok=1
    break
  fi
  echo "waiting health... ($i)"
  sleep 2
done
[ "$ok" = 1 ] || echo "HEALTH_FAIL"

echo
echo "============================================"
echo " XONG cleanup"
echo "  Main/Aux   → Antigravity"
echo "  Nhắn tin   → Groq gpt-oss (nếu có key), không Llama"
echo "  Ollama local → đã gỡ"
echo "============================================"
