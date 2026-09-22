"""Sổ tenant tổ chức: slug, mật khẩu mạnh, API chung, ẩn khi không phải manager."""
from _paths import ROOT, SERVER  # noqa: E402,F401
import json
import os
import tempfile
from pathlib import Path

os.environ["JAVIS_STATE_DIR"] = tempfile.mkdtemp(prefix="javis-org-")
os.environ.pop("JAVIS_ORG_MANAGER", None)
os.environ.pop("JAVIS_ORG_TENANT", None)
os.environ.pop("JAVIS_NAME", None)
os.environ.pop("DOMAIN_NAME", None)

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import org_coord as oc  # noqa: E402
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
check("domain mặc định javis-lan", ot.tenant_domain("lan") == "javis-lan.vietmycollege.com")
os.environ["JAVIS_ORG_HOST_PREFIX"] = "vmos"
check("domain prefix vmos", ot.tenant_domain("lan") == "vmos-lan.vietmycollege.com")
check("vmos vẫn giữ alias javis-", "javis-lan.vietmycollege.com" in ot.public_hosts("lan"))
check("bóc slug vmos-lan", oc.slug_from_host("vmos-lan.vietmycollege.com") == "lan")
check("bóc alias javis-lan khi prefix vmos", oc.slug_from_host("javis-lan.vietmycollege.com") == "lan")
check("không bóc javis gốc", oc.slug_from_host("javis.vietmycollege.com") == "")
os.environ.pop("JAVIS_ORG_HOST_PREFIX", None)
check("trần máy mặc định 6", oc.coord()["max_running"] == 6)
check("idle mặc định 30", oc.coord()["idle_minutes"] == 30)
check("máy 6GB gợi ý 3 chỗ người", oc.suggest_slots(6144) == 3)
check("máy 10GB gợi ý không quá 8", oc.suggest_slots(10240) == 8)
check("trần tay 6 trên 6GB thành 3 chỗ thật", oc.effective_max(total_mb=6144) == 3)
check("trần tay 2 không bị đẩy lên", oc.effective_max({"coord": {"max_running": 2, "idle_minutes": 30}}, 6144) == 2)
disk_t, disk_f, disk_p = oc.host_disk_bytes()
check("host_disk_bytes trả tổng/trống", isinstance(disk_t, int) and isinstance(disk_f, int) and disk_t >= disk_f >= 0)
c_host = oc.coord()
check("coord có ổ + CPU + reserve",
      "host_disk_total_bytes" in c_host and "host_cpus" in c_host
      and c_host.get("reserve_mb") == oc.RESERVE_MB
      and int(c_host.get("host_disk_total_bytes") or 0) >= 0)
snap = oc.snapshot(2)
check("snapshot có chỗ còn + ổ VPS",
      snap.get("slots_left") == max(0, int(snap.get("effective_max") or 0) - 2)
      and "host_disk_free_bytes" in snap and "suggest" in snap)
cset = oc.put_coord(max_running=99, idle_minutes=-1)
check("kẹp trần 20", cset["max_running"] == 20)
check("kẹp idle 0", cset["idle_minutes"] == 0)
oc.put_coord(max_running=6, idle_minutes=30)
oc.enqueue_wait("lan")
oc.enqueue_wait("minh")
check("peek không xóa hàng đợi", oc.peek_waiter() == "lan" and oc.wait_len() == 2)
oc.clear_wait("lan")
check("xóa đầu hàng còn minh", oc.peek_waiter() == "minh" and oc.wait_len() == 1)
oc.clear_wait("minh")

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
os.environ["JAVIS_NAME"] = "javis-manager"
check("tên javis-manager hiện Tổ chức", ot.manager_enabled() is True)
os.environ["JAVIS_ORG_MANAGER"] = "false"
check("cờ false thắng tên máy (Javis con)", ot.manager_enabled() is False)
os.environ.pop("JAVIS_ORG_MANAGER", None)
os.environ.pop("JAVIS_NAME", None)
check("list 404 khi không phải manager", c.get("/org/tenants").status_code == 404)
check("pool settings 404 khi không manager", c.get("/org/settings/pool").status_code == 404)

os.environ["JAVIS_ORG_MANAGER"] = "true"
app2 = FastAPI()
org_routes.register(app2)
c2 = TestClient(app2)
check("status manager", c2.get("/org/status").json().get("manager") is True)
coord = c2.put("/org/settings/coord", json={"max_running": 6, "idle_minutes": 30}).json()
check("API điều phối 200", coord.get("ok") is True and (coord.get("coord") or {}).get("max_running") == 6)
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
gone = c2.request("DELETE", "/org/tenants/quan", json={"confirm": "quan"})
check("không xóa bản quan", gone.status_code == 400)
ot.upsert({"slug": "xoa-thu", "name": "Xoa", "protected": False})
sai = c2.request("DELETE", "/org/tenants/xoa-thu", json={"confirm": "sai"})
check("xóa phải gõ đúng tên máy", sai.status_code == 400 and ot.get("xoa-thu") is not None)
okd = c2.request("DELETE", "/org/tenants/xoa-thu", json={"confirm": "xoa-thu"})
rec_soft = ot.get("xoa-thu")
check("xóa mềm khi gõ đúng", okd.status_code == 200 and ot.is_soft_deleted(rec_soft))
ok_restore = c2.post("/org/tenants/xoa-thu/restore")
check("khôi phục sau xóa mềm", ok_restore.status_code == 200 and not ot.is_soft_deleted(ot.get("xoa-thu")))
ok_purge = c2.request("DELETE", "/org/tenants/xoa-thu", json={"confirm": "xoa-thu", "purge_now": True})
check("xóa hẳn với purge_now", ok_purge.status_code == 200 and ot.get("xoa-thu") is None)
pq = c2.post("/org/tenants/quan/pause")
check("không tạm dừng bản quan", pq.status_code == 400)
ot.upsert({"slug": "dung-thu", "name": "Dung", "protected": False})
okp = c2.post("/org/tenants/dung-thu/pause")
check("tạm dừng được", okp.status_code == 200 and bool((ot.get("dung-thu") or {}).get("paused")))

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
check("phân biệt thiếu socket và thiếu quyền", "def docker_status" in src and "DOCKER_GID" in src)
check("không nhét MK user vào env container", 'JAVIS_ADMIN_PASSWORD=admin"' not in src.replace(" ", ""))
check("tenant không phải manager", "JAVIS_ORG_MANAGER=false" in src)
check("engine có cổng pool", "_u(" in (ROOT / "server" / "engine.py").read_text(encoding="utf-8"))

org_js = (ROOT / "dashboard" / "org.js").read_text(encoding="utf-8")
check("org.js có mật khẩu + API chung", "password" in org_js and "shared_api" in org_js and "orgPool" in org_js)
check("org.js mặc định API riêng não riêng", "não riêng" in org_js and "tự gắn" in org_js)
check("org.js thẻ người + hạn mức", "org-card" in org_js and "data-org-usage" in org_js)
check("org.js chia tab tổng hợp/cài/tạo/quản",
      'data-org-tab="tong"' in org_js and 'data-org-tab="cai"' in org_js
      and 'data-org-tab="tao"' in org_js and 'data-org-tab="quan"' in org_js)
check("org.js tìm và lọc người", "orgSearch" in org_js and "orgSt" in org_js and "orgApi" in org_js)
check("org.js placeholder Ví dụ", "Ví dụ: lan" in org_js)
check("org.js dùng host_prefix từ API", "host_prefix" in org_js and "hostOf" in org_js)
check("gắn lại luôn 4 ổ tenant, không ổ rỗng",
      "Từ chối gắn lại máy không có ổ não" in src and "ot.volume_names" in src.split("def apply_public_hosts", 1)[-1].split("def write_quota", 1)[0])
lock_fn = src.split("def start_with_capacity", 1)[-1].split("with _LOCK:", 1)[-1].split("def tick_coord", 1)[0]
check("giữ khóa chỗ đến khi bật máy",
      "_acquire_slot(slug)" in lock_fn and lock_fn.find("_acquire_slot") < lock_fn.find("start(slug)"))
check("Caddy một hostname, không ghép phẩy", '"caddy": domain' in src)
check("gắn lại khi nhãn cũ khác đúng một tên", "old == wanted" in src)
check("làm mới image máy con theo Javis gốc", "want_id" in src and "WORKSPACE_NAME=VietMy OS" in src)
check("điều phối trần + idle + park",
      "def start_with_capacity" in src and "def tick_coord" in src
      and "def sync_park" in src
      and "javis-park" in (ROOT / "server" / "org_coord.py").read_text(encoding="utf-8"))
park_fn = src.split("def sync_park", 1)[-1].split("def wake_or_wait", 1)[0] if "def sync_park" in src else ""
check("park không gắn volume", "Binds" not in park_fn and "volume rm" not in park_fn)
check("org.js điều phối trần máy", "orgCoord" in org_js and "max_running" in org_js and "idle_minutes" in org_js)
check("org.js điều phối theo RAM thật", "effective_max" in org_js and "xếp hàng" in org_js)
check("org.js hiện cấu hình VPS để phân bổ",
      "Máy chủ VPS" in org_js and "host_disk_total_bytes" in org_js
      and "Gợi ý chỗ người" in org_js and "Trần ổ đã cấp" in org_js)
check("index không nạp org.js eager (lazy trong console)",
      "/static/org.js" not in (ROOT / "dashboard" / "index.html").read_text(encoding="utf-8"))
check("org.js có Lưu thay đổi và Xóa người", "Lưu thay đổi" in org_js and "data-org-del" in org_js and "Xóa vĩnh viễn" in org_js)
check("org.js tạm dừng tài khoản", "Tạm dừng tài khoản" in org_js and "Chạy lại" in org_js and "/pause" in org_js)
check("org.js xóa mềm 72h + khôi phục", "Khôi phục" in org_js and "data-org-restore" in org_js and "72 giờ" in org_js)
check("org.js hiện last_active / image", "hoạt động" in org_js and "image_digest" in org_js)
check("org.js Đợt B policy + catalog + audit + consent",
      "brain_mode" in org_js and "Đẩy catalog" in org_js and "orgAuditBody" in org_js and "consent" in org_js)
check("policy helpers", callable(op.apply_policy) and callable(op.allowed_pool_providers))
check("mode blocked từ chối pool", op.quota_ok({"brain_mode": "blocked", "shared_api": True})[0] is False)
check("mode byo không pool", op.quota_ok({"brain_mode": "byo", "shared_api": False})[0] is False)
m = op.apply_policy({}, brain_mode="school", providers=["openrouter", "nope"])
check("apply_policy school + lọc provider", m["brain_mode"] == "school" and m["shared_api"] is True and m["providers"] == ["openrouter"])
ot.upsert({
    "slug": "policy-lan", "name": "Policy Lan", "protected": False,
    "brain_mode": "school", "shared_api": True, "providers": ["openrouter"],
    "container": "javis-policy-lan", "status": "stopped",
})
patched = c2.patch("/org/tenants/policy-lan", json={
    "brain_mode": "byo", "providers": ["openai", "gemini"],
})
rec_pol = ot.get("policy-lan")
check("PATCH chính sách byo + providers",
      patched.status_code == 200
      and (patched.json().get("tenant") or {}).get("brain_mode") == "byo"
      and (patched.json().get("tenant") or {}).get("shared_api") is False
      and (patched.json().get("tenant") or {}).get("providers") == ["openai", "gemini"]
      and rec_pol.get("brain_mode") == "byo"
      and rec_pol.get("providers") == ["openai", "gemini"])
listed = next((t for t in (c2.get("/org/tenants").json().get("tenants") or [])
               if t.get("slug") == "policy-lan"), {})
check("list giữ brain_mode/providers sau PATCH",
      listed.get("brain_mode") == "byo" and listed.get("providers") == ["openai", "gemini"])
ot.remove("policy-lan")
check("org.js một form Lưu gồm brain_mode (không tách Lưu chính sách)",
      'select[name="brain_mode"]' in org_js
      and "Lưu chính sách" not in org_js
      and "data-org-policy" not in org_js
      and 'input[name^="prov_"]' in org_js)
check("audit_tail tồn tại", callable(ot.audit_tail))
ot.audit("policy", "lan", "test")
check("audit_tail đọc được", any(r.get("action") == "policy" for r in ot.audit_tail(20)))
check("tạm dừng không tự bật khi mở link", "pause_account" in src and 'rec.get("paused")' in src)
check("xóa mềm trong docker", "def soft_delete" in src and "purge_soft_deleted" in src)
check("hàng đợi ghi đĩa", "wait_queue" in (ROOT / "server" / "org_coord.py").read_text(encoding="utf-8"))
check("soft_delete_mark / restore_mark", hasattr(ot, "soft_delete_mark") and hasattr(ot, "restore_mark"))
oc.enqueue_wait("lan")
oc.enqueue_wait("minh")
data_w = ot.load()
check("wait_queue lưu sau enqueue", isinstance(data_w.get("wait_queue"), dict) and "lan" in data_w["wait_queue"])
# Giả lập restart: xóa RAM rồi hydrate lại
oc._WAIT.clear()
oc._WAIT_LOADED = False
check("wait sống sau hydrate", oc.peek_waiter() == "lan" and oc.wait_len() == 2)
oc.clear_wait("lan")
oc.clear_wait("minh")
fake = {
    "id": "t1", "slug": "lan", "name": "Lan", "domain": ot.tenant_domain("lan"),
    "container": "javis-lan", "quota_gb": 2, "protected": False, "status": "stopped",
    "login_user": "lan", "shared_api": False, "token_quota": 0, "tokens_used": 0,
}
ot.upsert(fake)
marked = ot.soft_delete_mark("lan")
check("soft delete có deleted_at", ot.is_soft_deleted(marked))
pub = op.public_tenant(marked)
check("public status deleted", pub.get("status") == "deleted" and pub.get("purge_after") > 0)
restored = ot.restore_mark("lan")
check("restore gỡ deleted_at", not ot.is_soft_deleted(restored) and restored.get("paused") is True)
ot.remove("lan")
# hết hạn 72h
fake2 = dict(fake)
fake2["deleted_at"] = 1
ot.upsert(fake2)
check("purge_due nhận slug hết hạn", "lan" in ot.purge_due_slugs(now=ot.SOFT_DELETE_SEC + 10))
ot.remove("lan")
html = (ROOT / "dashboard" / "index.html").read_text(encoding="utf-8")
check("form sửa người hiện sẵn, không hidden", 'data-org-edit="${esc(t.slug)}">' in org_js and 'data-org-edit="${esc(t.slug)}" hidden' not in org_js)
check("quan không ghi Não gốc ở cột API", "Não gốc" not in org_js)
check("quan ghi bản cũ + API riêng", "bản cũ của bạn" in org_js and "Riêng (bản cũ)" in org_js)
dest = src.split("def destroy", 1)[-1].split("def people_running", 1)[0] if "def destroy" in src else ""
check("xóa máy không gắn v=true (không xóa nhầm volume)", "?v=true" not in dest and "PROTECTED_VOLUMES" in dest)
check("xóa không đụng javis-quan", "javis-quan" in dest)
main_py = (ROOT / "server" / "main.py").read_text(encoding="utf-8")
check("tenant ghi last-active", "touch_last_active" in main_py)
check("gốc tự bật khi mở link", "wake_or_wait" in main_py and "tick_coord" in main_py)
check("chờ health máy con từ bên trong", "127.0.0.1" in src and "def _health_inside" in src)
check("nhận máy dở nếu lần tạo trước kẹt", "if existing and ot.get(slug)" in src)
moon = (ROOT / "scripts" / "fetch-moonshine-models.sh").read_text(encoding="utf-8")
check("Moonshine lấy tên máy từ JAVIS_NAME", "JAVIS_NAME:-javis" in moon)
check("không em dash org.js", "\u2014" not in org_js)
con = (ROOT / "dashboard" / "console.js").read_text(encoding="utf-8")
check("rail có nhóm Tổ chức riêng", 'nav.group.quan_tri' in con and 'ids: ["org"]' in con)
check("console lazy-load org.js",
      'file: "org.js"' in con and "ensurePageScript" in con and "withLazyPage" in con)
html = (ROOT / "dashboard" / "index.html").read_text(encoding="utf-8")
check("index không nạp org.js trước console (PAGE_LAZY)",
      "/static/org.js" not in html and "/static/console.js" in html)

if FAIL:
    print("\nFAILED:", ", ".join(FAIL))
    raise SystemExit(1)
print("\nOK - test_org_tenants")
