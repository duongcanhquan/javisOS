#!/usr/bin/env bash
# Áp phân tầng model trên VPS:
#   Main     = Antigravity CLI (chat / làm việc / lệnh máy)
#   Việc nền = Ollama Cloud   (nhắc hẹn, loop, Kanban, tự học, tổng kết sáng)
#   Họp      = Ollama (module họp đã ưu tiên Ollama)
#
# Tuỳ chọn: JAVIS_NEW_ADMIN_PASSWORD=... để reset mật khẩu đăng nhập dashboard.
# Idempotent. Chạy trong thư mục repo trên VPS (cần docker container javis đang chạy).
set -euo pipefail

CONTAINER="${JAVIS_CONTAINER:-javis}"
MAIN_PROVIDER="${JAVIS_MAIN_PROVIDER:-antigravity-cli}"
MAIN_MODEL="${JAVIS_MAIN_MODEL:-}"
AUX_PROVIDER="${JAVIS_AUX_PROVIDER:-ollama}"
# Model cloud phổ biến; để trống thì script giữ model aux cũ nếu đã là ollama, không thì đặt mặc định này.
AUX_MODEL="${JAVIS_AUX_MODEL:-gpt-oss:120b-cloud}"

echo "==> container: $CONTAINER"
if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  echo "ERROR: container '$CONTAINER' không chạy."
  exit 1
fi

echo "==> áp Main=$MAIN_PROVIDER model='${MAIN_MODEL:-<mặc định CLI>}' | Việc nền=$AUX_PROVIDER model=$AUX_MODEL"
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
aux_p = (os.environ.get("JAVIS_AUX_PROVIDER") or "ollama").strip()
aux_mod = (os.environ.get("JAVIS_AUX_MODEL") or "gpt-oss:120b-cloud").strip()
new_pw = os.environ.get("JAVIS_NEW_ADMIN_PASSWORD") or ""

# --- Main ---
old_main = dict(m.get("main") or {})
# Để trống MAIN_MODEL = giữ model đang dùng nếu cùng provider Antigravity (tránh xoá lựa chọn sẵn).
if not main_mod and old_main.get("provider") == main_p and (old_main.get("model") or "").strip():
    main_mod = (old_main.get("model") or "").strip()
m["main"] = {"provider": main_p, "model": main_mod}
m["engine"] = main_p if main_p != "anthropic-cli" else "cli"
print("main:", old_main, "->", m["main"])

# --- Việc nền ---
old_aux = dict(m.get("auxiliary") or {})
m["auxiliary"] = {"provider": aux_p, "model": aux_mod}
print("auxiliary:", old_aux, "->", m["auxiliary"])

# Cảnh báo nếu chưa có key Ollama Cloud
key = (m.get("ollama_key") or "").strip()
if aux_p == "ollama" and not key:
    print("WARN: chưa có ollama_key trong settings - việc nền sẽ fallback.")
    print("      Vào Models → Ollama Cloud → dán API key từ ollama.com rồi chạy lại script này.")
else:
    print("ollama_key:", "có" if key else "không")

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

print("OK - đã ghi settings")
PY

echo "==> xong. Kiểm tra nhanh trên dashboard: Models → Main + Model việc nền."
