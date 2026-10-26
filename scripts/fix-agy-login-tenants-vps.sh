#!/usr/bin/env bash
# Chẩn đoán + vá env agy trên tenant: FORCE_FILE + TERMINAL_REMOTE, thử in link login.
# Không đè org_docker.py (có thể đang hot-patch wake riêng).
set -euo pipefail

DIR="${JAVIS_DIR:-}"
if [ -z "$DIR" ]; then
  if [ -d "$HOME/javis-os" ]; then DIR="$HOME/javis-os"
  elif [ -d /root/javis-os ]; then DIR=/root/javis-os
  else DIR="$(pwd)"
  fi
fi

echo "=== VERSION ==="
date -u
docker exec javis-manager cat /app/VERSION 2>/dev/null || echo missing

echo "=== HOT-PATCH terminal + antigravity_cli vào manager ==="
for f in terminal.py antigravity_cli.py; do
  src=""
  if [ -f "$DIR/server/$f" ]; then src="$DIR/server/$f"
  elif [ -f "/tmp/javis-fix-agy/server/$f" ]; then src="/tmp/javis-fix-agy/server/$f"
  elif [ -f "/tmp/javis-fix-agy/$f" ]; then src="/tmp/javis-fix-agy/$f"
  fi
  if [ -n "$src" ]; then
    echo "cp $f from $src"
    docker cp "$src" "javis-manager:/app/server/$f"
  else
    echo "skip $f (no source)"
  fi
done
docker restart javis-manager
for i in $(seq 1 40); do
  curl -fsS -m 3 http://127.0.0.1:7778/health >/dev/null 2>&1 && break
  sleep 2
done
sleep 2

echo "=== HEAL env thiếu trên mọi tenant (FORCE_FILE + TERMINAL_REMOTE) ==="
docker exec javis-manager python - <<'PY'
import sys
sys.path.insert(0, "/app/server")
import org_tenants as ot, org_docker as od

# Vá apply_public_hosts tại chỗ nếu bản trên máy còn early-return bỏ qua env.
src = open("/app/server/org_docker.py", encoding="utf-8").read()
if "need_force_file" not in src:
    # Gọi recreate bằng cách tạm xóa nhãn caddy lệch giả - an toàn hơn: tự gắn env rồi apply.
    print("org_docker chưa có heal env mới - dùng apply + ép DOMAIN giả rồi trả lại")
else:
    print("org_docker đã có heal env")

ts = ot.load().get("tenants") or []
for t in ts:
    if t.get("protected") or t.get("deleted_at") or t.get("paused"):
        continue
    slug = str(t.get("slug") or "")
    cname = str(t.get("container") or f"javis-{slug}")
    data = od.inspect_name(cname)
    if not data:
        print("missing", slug)
        continue
    env = ((data.get("Config") or {}).get("Env") or [])
    has_f = any(str(e) == "GEMINI_FORCE_FILE_STORAGE=true" or str(e).startswith("GEMINI_FORCE_FILE_STORAGE=true") for e in env)
    has_r = any(str(e).startswith("JAVIS_TERMINAL_REMOTE=") for e in env)
    st = od.container_status(cname)
    print("env", slug, "force_file", has_f, "term_remote", has_r, "st", st)
    if has_f and has_r:
        continue
    # Ép recreate: đổi tạm DOMAIN rồi apply lại đúng domain (apply luôn ghi FORCE_FILE/REMOTE ở bản mới;
    # bản cũ cũng append nếu thiếu).
    try:
        # Monkeypatch nhẹ: nếu early-return vì image khớp, xoá nhãn caddy tạm bằng inspect+recreate path
        # Cách đơn giản: gọi apply_public_hosts sau khi đặt label caddy khác qua update - Docker không
        # cho sửa label. Dùng apply với domain đúng - nếu early return, force bằng cách xóa Image id
        # giả... Thực tế: stop+gọi lại create body.
        od.apply_public_hosts(slug)
        data2 = od.inspect_name(cname)
        env2 = ((data2.get("Config") or {}).get("Env") or []) if data2 else []
        has_f2 = any("GEMINI_FORCE_FILE_STORAGE=" in str(e) for e in env2)
        has_r2 = any("JAVIS_TERMINAL_REMOTE=" in str(e) for e in env2)
        if has_f2 and has_r2:
            print("healed", slug)
            continue
        # Early-return: recreate thủ công bằng cách đổi DOMAIN_NAME tạm rồi apply lại
        wanted = ot.tenant_domain(slug)
        # Gọi create path: xóa container, giữ volume - dùng apply sau khi "đánh dấu" image lệch
        # Hack: truyền env bằng recreate copy từ apply_public_hosts nội bộ
        # Fallback: docker API recreate với env bổ sung
        from urllib.parse import quote
        cfg = data.get("Config") or {}
        hc = data.get("HostConfig") or {}
        labels = dict(cfg.get("Labels") or {})
        env_new = [e for e in (cfg.get("Env") or [])
                   if not str(e).startswith("GEMINI_FORCE_FILE_STORAGE=")
                   and not str(e).startswith("JAVIS_TERMINAL_REMOTE=")]
        env_new.append("GEMINI_FORCE_FILE_STORAGE=true")
        env_new.append("JAVIS_TERMINAL_REMOTE=1")
        was = st == "running"
        od._docker_api("POST", f"/containers/{quote(cname)}/stop", timeout=60.0)
        rm = od._docker_api("DELETE", f"/containers/{quote(cname)}?force=true", timeout=30.0)
        if rm.status_code not in (204, 200, 404):
            print("heal_rm_fail", slug, rm.status_code)
            continue
        body = {
            "Image": od._self_image(),
            "Hostname": cfg.get("Hostname") or cname,
            "Env": env_new,
            "Labels": labels,
            "HostConfig": {
                "Memory": hc.get("Memory") or od._MEM,
                "MemorySwap": hc.get("MemorySwap") or od._MEM,
                "NanoCpus": hc.get("NanoCpus") or od._NANO_CPUS,
                "PidsLimit": hc.get("PidsLimit") or od._PIDS,
                "RestartPolicy": hc.get("RestartPolicy") or {"Name": "unless-stopped"},
                "Binds": od.attach_shared_runtime_binds(list(hc.get("Binds") or [])),
                "NetworkMode": hc.get("NetworkMode") or "javis-web",
            },
        }
        user = cfg.get("User")
        if isinstance(user, str) and user.strip():
            body["User"] = user.strip()
        cr = od._docker_api("POST", f"/containers/create?name={quote(cname)}", json_body=body, timeout=120.0)
        if cr.status_code not in (200, 201):
            print("heal_create_fail", slug, cr.status_code, (cr.text or "")[:200])
            continue
        if was:
            od._docker_api("POST", f"/containers/{quote(cname)}/start", timeout=60.0)
        od.invalidate_status_cache(cname)
        print("healed_manual", slug, "was_running", was)
    except Exception as e:
        print("heal_fail", slug, type(e).__name__, e)
try:
    od.sync_park()
except Exception as e:
    print("park", e)
PY

echo "=== Bật 1 máy mẫu + patch terminal vào tenant ==="
SAMPLE=$(docker exec javis-manager python - <<'PY'
import sys
sys.path.insert(0, "/app/server")
import org_docker as od
for slug in ("thuha", "bach"):
    cname = "javis-" + slug
    try:
        if od.container_status(cname) != "running":
            od.start_with_capacity(slug)
        if od.container_status(cname) == "running":
            print(slug)
            break
    except Exception as e:
        print("err", slug, e, file=sys.stderr)
PY
)
SAMPLE=$(echo "$SAMPLE" | grep -E '^[a-z0-9-]+$' | tail -1 | tr -d '\r')
echo "sample=$SAMPLE"
if [ -z "$SAMPLE" ]; then
  echo "FAIL: không bật được máy mẫu"
else
  CNAME="javis-$SAMPLE"
  for f in terminal.py antigravity_cli.py; do
    if [ -f "$DIR/server/$f" ]; then
      docker cp "$DIR/server/$f" "$CNAME:/app/server/$f" && echo "patched_into_tenant $f"
    fi
  done
  docker restart "$CNAME"
  for i in $(seq 1 50); do
    if docker exec "$CNAME" curl -fsS -m 2 http://127.0.0.1:7777/health >/dev/null 2>&1; then
      echo "tenant health ok"
      break
    fi
    sleep 2
  done
  echo "=== env + agy probe ($CNAME) ==="
  docker exec "$CNAME" sh -c 'echo FORCE=$GEMINI_FORCE_FILE_STORAGE; echo REMOTE=$JAVIS_TERMINAL_REMOTE; echo DISPLAY=$DISPLAY; which agy; agy --version 2>&1 | head -5'
  echo "=== agy với SSH_* (timeout 15s) ==="
  OUT=$(docker exec -i "$CNAME" script -q -c "export GEMINI_FORCE_FILE_STORAGE=true JAVIS_TERMINAL_REMOTE=1 SSH_CONNECTION='127.0.0.1 0 127.0.0.1 22' SSH_CLIENT='127.0.0.1 0 22' SSH_TTY=\$(tty); unset DISPLAY WAYLAND_DISPLAY; timeout 15 agy" /dev/null 2>&1 | head -60 || true)
  echo "$OUT"
  low=$(echo "$OUT" | tr 'A-Z' 'a-z')
  if echo "$low" | grep -qE 'http|accounts.google|authoriz|login|paste|oauth'; then
    echo AGY_LOGIN_PROMPT_OK
  else
    echo AGY_LOGIN_PROMPT_EMPTY_OR_UNKNOWN
  fi
fi

echo FIX_AGY_LOGIN_DONE
