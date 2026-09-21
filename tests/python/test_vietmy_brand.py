"""Cổng cá nhân hiện VietMy OS trên thanh bar; VMOS gốc giữ VMOS."""
from _paths import ROOT, SERVER  # noqa: E402,F401
import json
import os
import tempfile
from pathlib import Path

os.environ["JAVIS_STATE_DIR"] = tempfile.mkdtemp(prefix="javis-ws-")
os.environ.pop("JAVIS_ORG_MANAGER", None)
os.environ.pop("JAVIS_ORG_TENANT", None)
os.environ.pop("JAVIS_NAME", None)
os.environ.pop("WORKSPACE_NAME", None)
os.environ.pop("DOMAIN_NAME", None)

import config as cfgmod  # noqa: E402

FAIL = []


def check(label, ok):
    print(("PASS" if ok else "FAIL") + ": " + label)
    if not ok:
        FAIL.append(label)


def _reset():
    cfgmod._SETTINGS_CACHE["sig"] = None
    cfgmod._SETTINGS_CACHE["cfg"] = None


_reset()
check("mặc định không phải cổng cá nhân", cfgmod.read_settings().get("workspace_name") == "VMOS")

os.environ["JAVIS_ORG_TENANT"] = "true"
_reset()
check("học viên hiện VietMy OS", cfgmod.read_settings().get("workspace_name") == "VietMy OS")
src = (ROOT / "dashboard" / "index.html").read_text(encoding="utf-8")
html = cfgmod.stamp_html_brand(src)
check("HTML title VietMy OS", "<title>VietMy OS</title>" in html)
check("thanh bar VietMy OS", ">VietMy OS</span>" in html)
check("không còn VMOS trên bar", ">VMOS</span>" not in html)
check("không còn JAVIS OS trên bar", ">JAVIS OS</span>" not in html)

os.environ["JAVIS_ORG_MANAGER"] = "true"
_reset()
check("VMOS gốc giữ VMOS", cfgmod.read_settings().get("workspace_name") == "VMOS")
os.environ.pop("JAVIS_ORG_MANAGER", None)
os.environ.pop("JAVIS_ORG_TENANT", None)

os.environ["JAVIS_NAME"] = "javis-quan"
_reset()
check("bản quan hiện VietMy OS", cfgmod.read_settings().get("workspace_name") == "VietMy OS")
os.environ.pop("JAVIS_NAME", None)

p = Path(os.environ["JAVIS_STATE_DIR"]) / "settings.json"
p.write_text(json.dumps({"workspace_name": "Não Lan"}), encoding="utf-8")
os.environ["JAVIS_ORG_TENANT"] = "true"
_reset()
check("tên tự đặt không bị đè", cfgmod.read_settings().get("workspace_name") == "Não Lan")
os.environ.pop("JAVIS_ORG_TENANT", None)
p.unlink()
_reset()

src_py = (ROOT / "server" / "main.py").read_text(encoding="utf-8")
check("trả HTML đã đóng brand", "stamp_html_brand" in src_py and "ensure_personal_workspace" in src_py)
od = (ROOT / "server" / "org_docker.py").read_text(encoding="utf-8")
check("tenant env VietMy OS", "WORKSPACE_NAME=VietMy OS" in od)
compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
check("compose nhét WORKSPACE_NAME", "WORKSPACE_NAME: ${WORKSPACE_NAME:-}" in compose)
sh = (ROOT / "scripts" / "vps-deploy.sh").read_text(encoding="utf-8")
check("deploy quan ghi VietMy OS", "WORKSPACE_NAME=VietMy OS" in sh)
org = (ROOT / "server" / "routes" / "org.py").read_text(encoding="utf-8")
check("list không recreate Caddy mỗi lần mở", "apply_public_hosts" not in org.split("def org_list", 1)[-1].split("def org_create", 1)[0])

if FAIL:
    print("\nFAILED:", ", ".join(FAIL))
    raise SystemExit(1)
print("\nOK - test_vietmy_brand")
