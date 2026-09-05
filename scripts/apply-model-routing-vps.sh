#!/usr/bin/env bash
# Áp phân tầng model trên VPS (cloud-first, không Ollama local):
#   Main     = Antigravity CLI (dashboard / MCP nặng / lệnh máy)
#   Việc nền = Antigravity CLI (nhắc hẹn, loop, Kanban, tự học, tổng kết sáng)
#   Nhắn tin = theo Main (Antigravity) — không ghim Groq/API flash
#              (Groq free TPM thấp, STT phụ thuộc key, hay 429 / “thiếu key”)
#   Họp      = Antigravity (trang Cuộc họp → Tổng kết)
#
# Tuỳ chọn env:
#   JAVIS_MSG_PROVIDER / JAVIS_MSG_MODEL  - chỉ khi CỐ Ý ghim API flash (không khuyến nghị)
#   JAVIS_NEW_ADMIN_PASSWORD              - reset mật khẩu dashboard
# Idempotent. Chạy trong thư mục repo trên VPS (cần docker container javis đang chạy).
set -euo pipefail

CONTAINER="${JAVIS_CONTAINER:-javis}"
MAIN_PROVIDER="${JAVIS_MAIN_PROVIDER:-antigravity-cli}"
MAIN_MODEL="${JAVIS_MAIN_MODEL:-}"
AUX_PROVIDER="${JAVIS_AUX_PROVIDER:-antigravity-cli}"
AUX_MODEL="${JAVIS_AUX_MODEL:-}"
MSG_PROVIDER="${JAVIS_MSG_PROVIDER:-}"
MSG_MODEL="${JAVIS_MSG_MODEL:-}"

echo "==> container: $CONTAINER"
if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  echo "ERROR: container '$CONTAINER' không chạy."
  exit 1
fi

echo "==> áp Main=$MAIN_PROVIDER | Việc nền=$AUX_PROVIDER | Nhắn tin=${MSG_PROVIDER:-auto}"
docker exec -i -u javis \
  -e "JAVIS_MAIN_PROVIDER=$MAIN_PROVIDER" \
  -e "JAVIS_MAIN_MODEL=$MAIN_MODEL" \
  -e "JAVIS_AUX_PROVIDER=$AUX_PROVIDER" \
  -e "JAVIS_AUX_MODEL=$AUX_MODEL" \
  -e "JAVIS_MSG_PROVIDER=$MSG_PROVIDER" \
  -e "JAVIS_MSG_MODEL=$MSG_MODEL" \
  -e "JAVIS_NEW_ADMIN_PASSWORD=${JAVIS_NEW_ADMIN_PASSWORD:-}" \
  "$CONTAINER" python - <<'PY'
import os
import sys

sys.path.insert(0, "/app/server")
import config as cfg  # noqa: E402

s = cfg.read_settings()
m = s.setdefault("model", {})

main_p = (os.environ.get("JAVIS_MAIN_PROVIDER") or "antigravity-cli").strip()
main_mod = (os.environ.get("JAVIS_MAIN_MODEL") or "").strip()
aux_p = (os.environ.get("JAVIS_AUX_PROVIDER") or "antigravity-cli").strip()
aux_mod = (os.environ.get("JAVIS_AUX_MODEL") or "").strip()
msg_p = (os.environ.get("JAVIS_MSG_PROVIDER") or "").strip()
msg_mod = (os.environ.get("JAVIS_MSG_MODEL") or "").strip()
new_pw = os.environ.get("JAVIS_NEW_ADMIN_PASSWORD") or ""

# --- Main ---
old_main = dict(m.get("main") or {})
if not main_mod and old_main.get("provider") == main_p and (old_main.get("model") or "").strip():
    main_mod = (old_main.get("model") or "").strip()
if main_p == "antigravity-cli" and not main_mod:
    main_mod = "gemini-3.8-flash-high"
m["main"] = {"provider": main_p, "model": main_mod}
m["engine"] = main_p if main_p != "anthropic-cli" else "cli"
print("main:", old_main, "->", m["main"])

# --- Việc nền = cloud (mặc định cùng Antigravity + model Main) ---
old_aux = dict(m.get("auxiliary") or {})
if old_aux.get("provider") == "ollama-local":
    print("WARN: auxiliary cũ = ollama-local → chuyển sang", aux_p)
if not aux_mod:
    if aux_p == main_p and main_mod:
        aux_mod = main_mod
    elif old_aux.get("provider") == aux_p and (old_aux.get("model") or "").strip():
        aux_mod = (old_aux.get("model") or "").strip()
    elif aux_p == "antigravity-cli":
        aux_mod = main_mod or "gemini-3.8-flash-high"
m["auxiliary"] = {"provider": aux_p, "model": aux_mod}
print("auxiliary:", old_aux, "->", m["auxiliary"])

# --- Nhắn tin (Telegram + Zalo): mặc định THEO MAIN (Antigravity) ---
# Không còn tự ghim Groq/Gemini API: gói free TPM thấp + STT bắt key → hay lỗi.
# Chỉ ghim API flash khi env JAVIS_MSG_PROVIDER đặt rõ ràng.
_KEY = {
    "groq": "groq_api_key",
    "gemini": "gemini_api_key",
    "deepseek": "deepseek_api_key",
    "openrouter": "openrouter_key",
}
_MAC_DINH_MSG = {
    "groq": "openai/gpt-oss-20b",
    "gemini": "gemini-2.5-flash",
    "deepseek": "deepseek-v4-flash",
    "openrouter": "google/gemini-2.0-flash-001",
    "antigravity-cli": "",
}


def _co_key(prov: str) -> bool:
    k = _KEY.get(prov)
    return bool(k and str(m.get(k) or "").strip())


old_tg = dict(m.get("telegram") or {})
if msg_p:
    if msg_p not in _MAC_DINH_MSG and msg_p != "antigravity-cli":
        print("WARN: JAVIS_MSG_PROVIDER lạ", msg_p, "- bỏ qua ghim nhắn tin")
        msg_p = ""
    elif msg_p in _KEY and not _co_key(msg_p):
        print("WARN: JAVIS_MSG_PROVIDER=", msg_p, "nhưng chưa có API key - bỏ qua")
        msg_p = ""
if msg_p and msg_p != "antigravity-cli":
    if not msg_mod:
        msg_mod = _MAC_DINH_MSG.get(msg_p) or ""
    m["telegram"] = {"provider": msg_p, "model": msg_mod}
    print("messaging (Telegram+Zalo):", old_tg, "->", m["telegram"], "(ép env)")
else:
    # Gỡ ghim API flash (Groq/…) → kênh nhắn tin đi theo Main = Antigravity.
    m["telegram"] = {"provider": "", "model": ""}
    print("messaging: gỡ ghim API flash", old_tg or "(trống)", "-> theo Main/Antigravity")

# --- Scrub Llama chết trên Groq (nếu vẫn còn trong Main/Aux/catalog) ---
for slot in ("main", "auxiliary"):
    block = dict(m.get(slot) or {})
    if (block.get("provider") or "") == "groq" and "llama" in (block.get("model") or "").lower():
        block["model"] = _MAC_DINH_MSG["groq"]
        m[slot] = block
        print(f"scrub {slot}: bỏ Llama →", block["model"])
cat = m.setdefault("catalog", {})
old_g = list(cat.get("groq") or [])
neu_g = [x for x in old_g if "llama" not in str(x).lower()]
if not neu_g:
    neu_g = ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.6-27b"]
if neu_g != old_g:
    cat["groq"] = neu_g
    print("catalog.groq:", old_g, "->", neu_g)

# --- Xóa Ollama local (VPS không dùng) ---
cleared = []
for k in (
    "ollama_local_endpoint",
    "ollama_local_key",
    "ollama_local_num_ctx",
    "ollama_local_keep_alive",
    "ollama_local_max_tool_rounds",
    "ollama_local_specs",
    "ollama_local_http_timeout",
):
    if m.pop(k, None) is not None:
        cleared.append(k)
if cleared:
    print("cleared ollama_local:", ", ".join(cleared))

# --- MCP lazy: để auto (Antigravity CLI không cần ép True như khi ghim Groq) ---
mcp = s.setdefault("mcp", {})
if mcp.get("lazy_tools") is True:
    print("mcp.lazy_tools: True -> auto (bỏ ép tốc độ API flash)")
    mcp["lazy_tools"] = "auto"

# --- Reset mật khẩu (tuỳ chọn) ---
if new_pw.strip():
    if len(new_pw.strip()) < 8:
        print("ERROR: mật khẩu mới phải >= 8 ký tự")
        sys.exit(1)
    auth = dict(s.get("auth") or {})
    user = (auth.get("username") or "admin").strip() or "admin"
    h, salt = cfg.hash_password(new_pw.strip())
    auth["username"] = user
    auth["password_hash"] = h
    auth["salt"] = salt
    s["auth"] = auth
    cfg.write_settings(s)
    try:
        cfg.clear_sessions()
    except Exception as e:
        print("WARN: clear_sessions:", e)
    print("auth: đã reset mật khẩu cho user", user)
else:
    cfg.write_settings(s)
    print("auth: không đổi (không truyền JAVIS_NEW_ADMIN_PASSWORD)")

print("OK - đã ghi settings (Main/Aux/nhắn tin = Antigravity)")
PY

echo "==> xong. Main + Việc nền + Telegram/Zalo = Antigravity (không ghim Groq)."
