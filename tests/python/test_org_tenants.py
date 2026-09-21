"""Sổ tenant tổ chức: slug, mật khẩu mạnh, API chung, ẩn khi không phải manager."""
from _paths import ROOT, SERVER  # noqa: E402,F401
import json
import os
import tempfile
from pathlib import Path

os.environ["JAVIS_STATE_DIR"] = tempfile.mkdtemp(prefix="javis-org-")
os.environ.pop("JAVIS_ORG_MANAGER", None)

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import org_policy as op  # noqa: E402
import org_quota  # noqa: E402
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

check("username rỗng", op.validate_username("") is not None)
check("username lan ok", op.validate_username("lan") is None)
check("username 12 ok", op.validate_username("lan.01") is None)
check("mk ngắn", op.validate_password("abc") is not None)
check("mk admin dễ đoán", op.validate_password("admin12345", "lan") is not None)
check("mk chỉ chữ", op.validate_password("abcdefghij") is not None)
check("mk mạnh", op.validate_password("LanHopLe99") is None)

check("volume tenant không trùng quan",
      not any(v in ot.PROTECTED_VOLUMES for v in ot.volume_names("lan")))

app = FastAPI()
org_routes.register(app)
c = TestClient(app)
st0 = c.get("/org/status").json()
check("status không manager", st0.get("manager") is False)
check("status không tenant", st0.get("tenant") is False)
check("list 404 khi không phải manager", c.get("/org/tenants").status_code == 404)
check("pool settings 404 khi không manager", c.get("/org/settings/pool").status_code == 404)

os.environ["JAVIS_ORG_MANAGER"] = "true"
app2 = FastAPI()
org_routes.register(app2)
c2 = TestClient(app2)
check("status manager", c2.get("/org/status").json().get("manager") is True)
lst = c2.get("/org/tenants")
check("list 200 khi manager", lst.status_code == 200)
body = lst.json()
check("list có quan", any(t.get("slug") == "quan" for t in (body.get("tenants") or [])))
check("list không lộ vé", all("pool_token" not in t and "pool_token_hash" not in t
                              for t in (body.get("tenants") or [])))
check("không tạo trùng quan", c2.post("/org/tenants", json={"slug": "quan"}).status_code in (400, 409))
weak = c2.post("/org/tenants", json={"slug": "lan-test", "password": "admin", "login_user": "lan"})
check("từ chối mật khẩu yếu", weak.status_code == 400)
nopw = c2.post("/org/tenants", json={"slug": "lan-test2", "login_user": "lanhai"})
check("từ chối thiếu mật khẩu", nopw.status_code == 400)

pool = c2.get("/org/settings/pool").json()
check("pool có danh sách nhà", "openrouter" in (pool.get("providers") or {}))
c2.put("/org/settings/pool", json={"openrouter": "sk-or-v1-ABCDEFGH9999"})
got = c2.get("/org/settings/pool").json()["providers"]["openrouter"]
check("pool đã lưu và che khóa", got.get("set") is True and "ABCD" not in (got.get("mask") or ""))
check("pool không trả khóa thô", "sk-or-v1-ABCDEFGH9999" not in json.dumps(got))

tok = op.new_pool_token()
rec = {
    "slug": "demo", "name": "Demo", "shared_api": True, "token_quota": 10,
    "tokens_used": 0, "tokens_month": op.month_key(),
    "pool_token_hash": op.hash_token(tok),
}
ot.upsert(rec)
me = c2.get("/org/pool/me", headers={"Authorization": "Bearer " + tok})
check("vé pool /me 200", me.status_code == 200 and me.json().get("shared_api") is True)
bad = c2.get("/org/pool/me", headers={"Authorization": "Bearer sai"})
check("vé sai 401", bad.status_code == 401)
deny = c2.post("/org/pool/openrouter/chat", headers={"Authorization": "Bearer sai"}, json={})
check("proxy vé sai 401", deny.status_code == 401)

# quota: file 0 = không trần dù env còn số
os.environ["JAVIS_QUOTA_GB"] = "2"
p = Path(os.environ["JAVIS_STATE_DIR"]) / "org-quota"
p.write_text("0", encoding="utf-8")
check("file 0 thắng env, không trần", org_quota.quota_bytes() == 0)
p.write_text("1", encoding="utf-8")
check("file 1 GB", org_quota.quota_bytes() == 1024 * 1024 * 1024)
p.unlink()
os.environ.pop("JAVIS_QUOTA_GB", None)
check("không env không trần", org_quota.quota_bytes() == 0)

src = (ROOT / "server" / "org_docker.py").read_text(encoding="utf-8")
binds = src.split('"Binds":', 1)[1].split("NetworkMode", 1)[0] if '"Binds":' in src else ""
check("Binds tenant không có docker.sock", "docker.sock" not in binds)
check("không nhét MK user vào env container", 'JAVIS_ADMIN_PASSWORD=admin"' not in src.replace(" ", ""))
check("tenant không phải manager", "JAVIS_ORG_MANAGER=false" in src)
check("engine có cổng pool", "_u(" in (ROOT / "server" / "engine.py").read_text(encoding="utf-8"))

org_js = (ROOT / "dashboard" / "org.js").read_text(encoding="utf-8")
check("org.js có mật khẩu + API chung", "password" in org_js and "shared_api" in org_js and "orgPool" in org_js)
check("không em dash org.js", "\u2014" not in org_js)
html = (ROOT / "dashboard" / "index.html").read_text(encoding="utf-8")
check("index nạp org.js trước console.js",
      0 < html.find("/static/org.js") < html.find("/static/console.js"))

if FAIL:
    print("\nFAILED:", ", ".join(FAIL))
    raise SystemExit(1)
print("\nOK - test_org_tenants")
