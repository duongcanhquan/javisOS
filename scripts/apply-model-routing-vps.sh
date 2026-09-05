#!/usr/bin/env bash
# Áp phân tầng model trên VPS (cloud-first, không Ollama local):
#   Main     = Antigravity CLI (chat / MCP / lệnh máy / tra web)
#   Việc nền = Antigravity CLI (nhắc hẹn, loop, Kanban, tự học, tổng kết sáng)
#   Họp      = Antigravity (trang Cuộc họp → Tổng kết)
#   STT họp  = Moonshine (browser) hoặc Groq Whisper (upload file âm)
#
# Tuỳ chọn: JAVIS_NEW_ADMIN_PASSWORD=... để reset mật khẩu đăng nhập dashboard.
# Idempotent. Chạy trong thư mục repo trên VPS (cần docker container javis đang chạy).
set -euo pipefail

CONTAINER="${JAVIS_CONTAINER:-javis}"
MAIN_PROVIDER="${JAVIS_MAIN_PROVIDER:-antigravity-cli}"
MAIN_MODEL="${JAVIS_MAIN_MODEL:-}"
AUX_PROVIDER="${JAVIS_AUX_PROVIDER:-antigravity-cli}"
AUX_MODEL="${JAVIS_AUX_MODEL:-}"

echo "==> container: $CONTAINER"
if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  echo "ERROR: container '$CONTAINER' không chạy."
  exit 1
fi

echo "==> áp Main=$MAIN_PROVIDER | Việc nền=$AUX_PROVIDER (cloud, không Ollama local)"
docker exec -i -u javis \
  -e "JAVIS_MAIN_PROVIDER=$MAIN_PROVIDER" \
  -e "JAVIS_MAIN_MODEL=$MAIN_MODEL" \
  -e "JAVIS_AUX_PROVIDER=$AUX_PROVIDER" \
  -e "JAVIS_AUX_MODEL=$AUX_MODEL" \
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

# --- Tốc độ chat Telegram/Zalo: ép lazy MCP (ít schema tool = TTFT nhanh hơn) ---
mcp = s.setdefault("mcp", {})
if mcp.get("lazy_tools") != True:
    print("mcp.lazy_tools:", mcp.get("lazy_tools"), "-> True (ép bật cho chat nhanh)")
    mcp["lazy_tools"] = True
if int(mcp.get("lazy_threshold") or 40) > 25:
    print("mcp.lazy_threshold:", mcp.get("lazy_threshold"), "-> 25")
    mcp["lazy_threshold"] = 25

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

print("OK - đã ghi settings (cloud-first)")
PY

echo "==> xong. Kiểm tra: Models → Main + Model việc nền = Antigravity."
