#!/usr/bin/env bash
# Bật Tự học + git-init brain mặc định trên VPS (container Javis).
# Idempotent: chạy lại an toàn; brain đã có git thì chỉ cập nhật .gitignore nếu cần.
set -euo pipefail

CONTAINER="${JAVIS_CONTAINER:-javis}"

echo "==> container: $CONTAINER"
if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  echo "ERROR: container '$CONTAINER' không chạy. Bật Javis trước: docker compose up -d"
  exit 1
fi

echo "==> git-init brain + bật learn_config (trong container)"
docker exec -u javis "$CONTAINER" python - <<'PY'
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, "/app/server")
import git_brain  # noqa: E402

brains_dir = os.environ.get("BRAINS_DIR", "/brains")
brain_root = str(Path(brains_dir) / "Brain Default")
state_dir = Path(os.environ.get("JAVIS_STATE_DIR", "/data/state"))
cfg_path = state_dir / "learn_config.json"

print(f"brain: {brain_root}")
print(f"config: {cfg_path}")

g = git_brain.ensure_git_repo(brain_root)
print("git:", json.dumps(g, ensure_ascii=False))

if not g.get("ok"):
    print("WARN: git-init chưa thành công - Tự học vẫn chạy nhưng chưa undo được commit.")
    sys.exit(1 if not git_brain.has_git() else 0)

default = {
    "enabled": True,
    "mode": "auto",
    "capabilities": {"memory": True, "wiki": True, "skill": True, "task": False},
    "brains": ["brain"],
}
cfg = dict(default)
if cfg_path.exists():
    try:
        data = json.loads(cfg_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                    cfg[k].update(v)
                else:
                    cfg[k] = v
    except Exception as e:
        print(f"WARN: đọc learn_config cũ lỗi ({e}), ghi đè phần bật học.")

cfg["enabled"] = True
cfg.setdefault("mode", "auto")
bs = set(cfg.get("brains") or [])
bs.add("brain")
cfg["brains"] = list(bs)
caps = cfg.setdefault("capabilities", {})
caps.setdefault("memory", True)
caps.setdefault("wiki", True)
caps.setdefault("skill", True)
caps.setdefault("task", False)

state_dir.mkdir(parents=True, exist_ok=True)
cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("learn_config: enabled=true, mode=", cfg.get("mode"))

repo_ok = git_brain.is_git_checkout(brain_root)
print("git_repo:", repo_ok)
if repo_ok:
    r = git_brain._git(brain_root, "log", "-1", "--oneline")
    if r.returncode == 0 and (r.stdout or "").strip():
        print("commit gần nhất:", (r.stdout or "").strip())
PY

echo ""
echo "==> XONG bật Tự học + git brain."
echo "    Xem trên dashboard: Tự học → 'Javis đã tự học gì' + Hoàn tác."
echo "    Sao lưu GitHub (repo Private + token): cấu hình thêm ở mục 'Đồng bộ brain với GitHub'."
