#!/usr/bin/env bash
# Áp phân tầng model trên VPS:
#   Main     = Antigravity CLI (chat / làm việc / lệnh máy)
#   Việc nền = Ollama Local nếu đã cài, không thì Ollama Cloud (nhắc hẹn, loop, Kanban…)
#   Họp      = Ollama (module họp đã ưu tiên Ollama)
#
# Tuỳ chọn: JAVIS_NEW_ADMIN_PASSWORD=... để reset mật khẩu đăng nhập dashboard.
# Idempotent. Chạy trong thư mục repo trên VPS (cần docker container javis đang chạy).
set -euo pipefail

CONTAINER="${JAVIS_CONTAINER:-javis}"
MAIN_PROVIDER="${JAVIS_MAIN_PROVIDER:-antigravity-cli}"
MAIN_MODEL="${JAVIS_MAIN_MODEL:-}"
# Để trống = tự chọn: ollama-local (nếu đã cài) → ollama cloud (nếu có key) → giữ cũ.
# Ép cloud không key khi máy đã có Ollama local sẽ làm việc nền fallback Claude → lỗi /login.
AUX_PROVIDER="${JAVIS_AUX_PROVIDER:-}"
AUX_MODEL="${JAVIS_AUX_MODEL:-}"

echo "==> container: $CONTAINER"
if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  echo "ERROR: container '$CONTAINER' không chạy."
  exit 1
fi

echo "==> áp Main=$MAIN_PROVIDER model='${MAIN_MODEL:-<mặc định CLI>}' | Việc nền=${AUX_PROVIDER:-<tự chọn>} model=${AUX_MODEL:-<tự chọn>}"
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
aux_p = (os.environ.get("JAVIS_AUX_PROVIDER") or "").strip()
aux_mod = (os.environ.get("JAVIS_AUX_MODEL") or "").strip()
new_pw = os.environ.get("JAVIS_NEW_ADMIN_PASSWORD") or ""

# --- Main ---
old_main = dict(m.get("main") or {})
# Để trống MAIN_MODEL = giữ model đang dùng nếu cùng provider Antigravity (tránh xoá lựa chọn sẵn).
if not main_mod and old_main.get("provider") == main_p and (old_main.get("model") or "").strip():
    main_mod = (old_main.get("model") or "").strip()
# Lần deploy trước từng xoá model → nếu vẫn trống thì đặt lại model Antigravity phổ biến.
if main_p == "antigravity-cli" and not main_mod:
    main_mod = "gemini-3.8-flash-high"
m["main"] = {"provider": main_p, "model": main_mod}
m["engine"] = main_p if main_p != "anthropic-cli" else "cli"
print("main:", old_main, "->", m["main"])

# --- Việc nền (ưu tiên local để khỏi fallback Claude /login) ---
old_aux = dict(m.get("auxiliary") or {})
local_ep = (m.get("ollama_local_endpoint") or "").strip()
key = (m.get("ollama_key") or "").strip()


def _ollama_has(name: str) -> bool:
    """True nếu Ollama local đã có model (kể cả :latest). Lỗi mạng → False."""
    ep = (local_ep or "").rstrip("/")
    if not ep or not name:
        return False
    try:
        import json
        import urllib.request
        with urllib.request.urlopen(ep + "/api/tags", timeout=8) as r:
            models = (json.load(r) or {}).get("models") or []
        names = set()
        for m in models:
            n = (m.get("name") or "").strip()
            if not n:
                continue
            names.add(n)
            names.add(n.split(":")[0])
        return name in names or name.split(":")[0] in names
    except Exception as e:
        print("WARN: không liệt kê được model Ollama:", e)
        return False


def _pick_local_model():
    if aux_mod and "cloud" not in aux_mod:
        cand = aux_mod
    else:
        prev = (old_aux.get("model") or "").strip() if old_aux.get("provider") == "ollama-local" else ""
        if prev.startswith("javis-"):
            cand = prev
        elif prev and "cloud" not in prev:
            # Base tag (vd qwen3:4b-instruct) → biến thể Modelfile bake num_ctx
            cand = "javis-" + prev.replace(":", "-")
        else:
            cand = "javis-qwen3-4b-instruct"
    # Install từng fail vì index.lock → routing trỏ javis-* nhưng model chưa tạo.
    # Dùng tạm base đã kéo (qwen3:4b-instruct) thay vì để nhắc hẹn 404/fallback Claude.
    if cand.startswith("javis-") and not _ollama_has(cand):
        base = cand[len("javis-"):].replace("-", ":", 1)
        if _ollama_has(base):
            print(f"WARN: chưa có {cand} → dùng tạm base {base} (chạy lại Install Ollama)")
            return base
        print(f"WARN: chưa có {cand} trên Ollama - vẫn ghi (cần chạy Install)")
    return cand


if not aux_p:
    if local_ep:
        aux_p, aux_mod = "ollama-local", _pick_local_model()
        print("auto: có ollama_local_endpoint → việc nền = ollama-local")
    elif key:
        aux_p = "ollama"
        aux_mod = aux_mod or "gpt-oss:120b-cloud"
        print("auto: có ollama_key → việc nền = ollama cloud")
    elif old_aux.get("provider"):
        aux_p = (old_aux.get("provider") or "").strip()
        aux_mod = aux_mod or (old_aux.get("model") or "").strip()
        print("auto: giữ auxiliary cũ", aux_p, aux_mod)
    else:
        aux_p, aux_mod = "ollama-local", _pick_local_model()
        print("auto: chưa có nguồn → đặt ollama-local (cần cài Ollama trên host)")

# Cloud không key mà đã có local → đừng ép cloud (deploy từng làm vậy → /login).
if aux_p == "ollama" and not key and local_ep:
    print("WARN: ép ollama cloud nhưng chưa có key + đã có local → chuyển ollama-local")
    aux_p, aux_mod = "ollama-local", _pick_local_model()

if not aux_mod:
    aux_mod = _pick_local_model() if aux_p == "ollama-local" else "gpt-oss:120b-cloud"

m["auxiliary"] = {"provider": aux_p, "model": aux_mod}
if aux_p == "ollama-local":
    # VPS ~6GB: ctx >8k dễ swap → chậm; việc nền đã rút prompt nên 8k đủ
    cur_ctx = int(m.get("ollama_local_num_ctx") or 0)
    if cur_ctx <= 0 or cur_ctx > 8192:
        m["ollama_local_num_ctx"] = 8192
        print("ollama_local_num_ctx -> 8192 (tránh swap trên VPS 6GB)")
print("auxiliary:", old_aux, "->", m["auxiliary"])
print("ollama_local_endpoint:", local_ep or "(trống)")
print("ollama_key:", "có" if key else "không")
if aux_p == "ollama" and not key:
    print("WARN: việc nền = ollama cloud nhưng chưa có key - sẽ lỗi hoặc fallback.")
    print("      Vào Models → Ollama Cloud → dán key, hoặc cài Ollama local trên VPS.")
elif aux_p == "ollama-local" and not local_ep:
    print("WARN: việc nền = ollama-local nhưng chưa có endpoint - chạy install-ollama-vps.sh.")

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
