"""Sổ tenant tổ chức: slug, volume bảo vệ, ẩn API khi không phải manager."""
from _paths import ROOT, SERVER  # noqa: E402,F401
import json
import os
import tempfile

os.environ["JAVIS_STATE_DIR"] = tempfile.mkdtemp(prefix="javis-org-")
os.environ.pop("JAVIS_ORG_MANAGER", None)

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import org_tenants as ot  # noqa: E402
import routes.org as org_routes  # noqa: E402

FAIL = []


def check(label, ok):
    print(("PASS" if ok else "FAIL") + ": " + label)
    if not ok:
        FAIL.append(label)


check("slug rỗng", ot.validate_slug("") is not None)
check("slug quan bị cấm", "hệ thống" in (ot.validate_slug("quan") or ""))
check("slug manager bị cấm", ot.validate_slug("manager") is not None)
check("slug lan ok", ot.validate_slug("lan") is None)
check("slug hoa ok", ot.validate_slug("aiot-01") is None)
check("slug chữ hoa được chuẩn hoá", ot.validate_slug("Lan") is None)

check("volume quan bị cấm trong tên hệ thống",
      all(v in ot.PROTECTED_VOLUMES for v in (
          "javis_javis-data", "javis_javis-brains", "javis_claude-auth", "javis_codex-auth")))
vols = ot.volume_names("lan")
check("volume tenant không trùng quan", not any(v in ot.PROTECTED_VOLUMES for v in vols))
check("volume tenant có slug", all("lan" in v for v in vols))

data = {"tenants": []}
check("ensure_quan lần đầu", ot.ensure_quan(data) is True)
check("ensure_quan không nhân bản", ot.ensure_quan(data) is False)
check("quan protected", data["tenants"][0].get("protected") is True)

app = FastAPI()
org_routes.register(app)
c = TestClient(app)
st = c.get("/org/status").json()
check("status không manager", st.get("manager") is False)
r = c.get("/org/tenants")
check("list 404 khi không manager", r.status_code == 404)
r = c.post("/org/tenants", json={"slug": "lan"})
check("create 404 khi không manager", r.status_code == 404)

os.environ["JAVIS_ORG_MANAGER"] = "true"
app2 = FastAPI()
org_routes.register(app2)
c2 = TestClient(app2)
check("status manager", c2.get("/org/status").json().get("manager") is True)
lst = c2.get("/org/tenants")
check("list 200 khi manager", lst.status_code == 200)
check("list có quan", any(t.get("slug") == "quan" for t in (lst.json().get("tenants") or [])))
bad = c2.post("/org/tenants", json={"slug": "quan"})
check("không tạo trùng quan", bad.status_code in (400, 409))

src = (ROOT / "server" / "org_docker.py").read_text(encoding="utf-8")
binds = ""
if '"Binds":' in src:
    binds = src.split('"Binds":', 1)[1].split("NetworkMode", 1)[0]
check("Binds tenant không có docker.sock", "docker.sock" not in binds)
check("docker không volume rm", "volume rm" not in src and "DELETE" not in src)
check("cấm volume hệ thống khi tạo", "PROTECTED_VOLUMES" in src)
check("tenant không phải manager", "JAVIS_ORG_MANAGER=false" in src)

main_py = (ROOT / "server" / "main.py").read_text(encoding="utf-8")
check("main.py đăng ký org routes", "org_routes.register(app)" in main_py)

console = (ROOT / "dashboard" / "console.js").read_text(encoding="utf-8")
check("console có trang org", '"org"' in console and "napOrgFlag" in console)
check("console ẩn org mặc định", 'RAIL_AN = new Set(["org"])' in console)
org_js = (ROOT / "dashboard" / "org.js").read_text(encoding="utf-8")
check("org.js có form tạo", "orgCreate" in org_js and "/org/tenants" in org_js)
html = (ROOT / "dashboard" / "index.html").read_text(encoding="utf-8")
check("index nạp org.js trước console.js",
      0 < html.find("/static/org.js") < html.find("/static/console.js"))
vi = json.loads((ROOT / "dashboard" / "i18n" / "vi.json").read_text(encoding="utf-8"))
en = json.loads((ROOT / "dashboard" / "i18n" / "en.json").read_text(encoding="utf-8"))
check("i18n vi page.org.label", vi.get("page.org.label") == "Tổ chức")
check("i18n en page.org.label", en.get("page.org.label") == "Organization")
check("không em dash org.js", "\u2014" not in org_js)

if FAIL:
    print("\nFAILED:", ", ".join(FAIL))
    raise SystemExit(1)
print("\nOK - test_org_tenants")
