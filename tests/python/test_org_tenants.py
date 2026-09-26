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
check("idle mặc định 0 (không tự tắt)", oc.coord()["idle_minutes"] == 0)
check("idle 5 phút = 300 giây grace", oc.evict_grace_sec(idle_minutes=5) == 300)
check("idle 1 phút tôn trọng (không sàn cứng 5)", oc.evict_grace_sec(idle_minutes=1) == 60)
check("idle 0 → grace nhường chỗ 15 phút", oc.evict_grace_sec(idle_minutes=0) == 15 * 60)
check("handoff khi xếp hàng ~2 phút với idle 5", oc.handoff_grace_sec(idle_minutes=5) == 120)
check("handoff không đá dưới 90 giây", oc.handoff_grace_sec(idle_minutes=1) == 90)
check("pressure grace 90 giây", oc.evict_grace_sec(pressure=True) == 90)
check("máy 6GB gợi ý 2 chỗ người", oc.suggest_slots(6144) == 2)
check("máy 10GB gợi ý 6 chỗ (trần 1024)", oc.suggest_slots(10240) == 6)
check("trần tay 6 trên 6GB thành 2 chỗ thật", oc.effective_max(total_mb=6144) == 2)
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
create_fn = src.split("def create_and_start", 1)[-1].split("\ndef apply_public_hosts", 1)[0]
check("tạo tenant: health chậm không nuốt máy đã ghi sổ",
      "boot_warn" in create_fn and "inspect_name(cname)" in create_fn
      and create_fn.find("ot.upsert(rec)") < create_fn.find("wait_health"))
org_py = (ROOT / "server" / "routes" / "org.py").read_text(encoding="utf-8")
check("API tạo trả note khi boot_warn", "boot_warn" in org_py and "Khởi động chưa xong" in org_py)
check("org.js sau lỗi tạo vẫn kiểm tra sổ",
      "đã có trong sổ" in org_js and 'api("/org/tenants")' in org_js)
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
check("healthcheck không ghi last-active", "should_touch_last_active" in main_py)
oc_py = (ROOT / "server" / "org_coord.py").read_text(encoding="utf-8")
check("bỏ /health khỏi tín hiệu người", "should_touch_last_active" in oc_py and '"/health"' in oc_py)
check("bỏ poll /background + /connect/health",
      '"/background"' in oc_py and '"/connect/health"' in oc_py)
check("health không phải tín hiệu", oc.should_touch_last_active("/health") is False)
check("background poll không phải tín hiệu", oc.should_touch_last_active("/background") is False)
check("connect health không phải tín hiệu", oc.should_touch_last_active("/connect/health") is False)
check("ws không phải tín hiệu", oc.should_touch_last_active("/ws") is False)
check("ws/graph không phải tín hiệu", oc.should_touch_last_active("/ws/graph") is False)
check("mở trang chủ vẫn là tín hiệu", oc.should_touch_last_active("/") is True)
check("chat API vẫn là tín hiệu", oc.should_touch_last_active("/chat") is True)
check("stats one-shot trong org_docker", "one-shot=true" in (ROOT / "server" / "org_docker.py").read_text(encoding="utf-8"))
check("ram_live nhận danh sách running", "def ram_live_report(running" in (ROOT / "server" / "org_docker.py").read_text(encoding="utf-8"))
check("org soft refresh không xóa UI", "org-busy" in org_js and "Đang cập nhật sổ" in org_js)
check("RAM_MB trần 1024", oc.RAM_MB == 1024)
import org_docker as od_mem  # noqa: E402
check("768 MB thì nâng trần", od_mem.memory_should_raise(768 * 1024 * 1024) is True)
check("1024 MB thì giữ", od_mem.memory_should_raise(1024 * 1024 * 1024) is False)
check("gắn lại máy luôn đặt trần 1024",
      '"Memory": _MEM' in src and 'hc.get("Memory") or _MEM' not in src)
check("tick nâng trần máy người", "def ensure_people_memory" in src)
check("tick nhả cache file máy nghỉ", "def reclaim_idle_file_cache" in src and "reclaim_idle_file_cache()" in src)
check("cache file 10MB thì không nhả", od_mem.file_cache_reclaim_bytes({"file": 10 * 1024 * 1024}) == 0)
check("cache file 200MB thì nhả đúng số",
      od_mem.file_cache_reclaim_bytes({"file": 200 * 1024 * 1024}) == 200 * 1024 * 1024)
check("nghỉ 10 phút chưa nhả cache", od_mem.cache_reclaim_due(10 * 60, 0, 10_000) is False)
check("nghỉ 16 phút thì đến lượt nhả", od_mem.cache_reclaim_due(16 * 60, 0, 10_000) is True)
check("vừa nhả thì chưa nhả lại", od_mem.cache_reclaim_due(20 * 60, 10_000, 10_000 + 60) is False)
check("đọc memory.stat", od_mem.parse_cgroup_memory_stat("file 123\r\nanon 4\n")["file"] == 123)
check("org.js nói máy nghỉ tự nhả cache", "tự nhả cache file" in org_js)
check("route /org/ram_live", '"/org/ram_live"' in (ROOT / "server" / "routes" / "org.py").read_text(encoding="utf-8"))
check("org.js poll ram_live", 'api("/org/ram_live")' in org_js and "startRamPoll" in org_js)
check("org.js meter RAM đang dùng thật", "RAM đang dùng (Docker)" in org_js and "RAM ước cho" not in org_js)
check("gốc tự bật khi mở link", ("wake_or_wait" in main_py or "ensure_tenant_ready" in main_py) and "tick_coord" in main_py and "proxy_tenant_request" in main_py)
check("wake không còn trang Đang bật máy cho flow thường",
      "ensure_tenant_ready" in src and "proxy_tenant_request" in src)
check("chờ health máy con từ bên trong", "127.0.0.1" in src and "def _health_inside" in src)
check("nhận máy dở nếu lần tạo trước kẹt", "if existing and ot.get(slug)" in src)
moon = (ROOT / "scripts" / "fetch-moonshine-models.sh").read_text(encoding="utf-8")
check("Moonshine lấy tên máy từ JAVIS_NAME", "JAVIS_NAME:-javis" in moon)
check("deploy chép Moonshine vào mọi máy người", "def copy_moonshine_everywhere" in moon or "copy_moonshine_everywhere()" in moon)
check("bỏ qua manager khi chép model họp", "javis-manager" in moon and "javis-proxy" in moon)
check("máy người gắn model họp chỉ đọc", od_mem.moonshine_bind().endswith(":ro"))
check("bind model họp đúng đường trong container",
      "/app/dashboard/vendor/moonshine-models" in od_mem.moonshine_bind())
check("gắn bind không nhân đôi",
      len(od_mem.attach_moonshine_bind([od_mem.moonshine_bind(), "/a:/data"])) == 2)
check("tạo máy gắn phần chạy chung", "attach_shared_runtime_binds(" in create_fn)
check("gắn lại máy gắn phần chạy chung",
      "attach_shared_runtime_binds(binds)" in src.split("def apply_public_hosts", 1)[-1].split("def write_quota", 1)[0])
check("tick chép phần chạy chung khi máy thiếu",
      "def ensure_shared_runtime" in src and "ensure_shared_runtime()" in src)
_ids = {s["id"] for s in od_mem.shared_runtime_specs()}
check("bộ chung có họp, sơ đồ, font", {"moonshine", "mermaid", "turndown", "fonts"} <= _ids)
_share = od_mem.attach_shared_runtime_binds(["/a:/data"])
check("bốn thư mục chung chỉ đọc", sum(1 for b in _share if str(b).endswith(":ro")) == 4)
check("gắn phần chung không đè ổ não", "/a:/data" in _share)
check("không em dash org.js", "\u2014" not in org_js)
con = (ROOT / "dashboard" / "console.js").read_text(encoding="utf-8")
check("rail có nhóm Tổ chức riêng", 'nav.group.quan_tri' in con and 'ids: ["org"]' in con)
check("console lazy-load org.js",
      'file: "org.js"' in con and "ensurePageScript" in con and "withLazyPage" in con)
html = (ROOT / "dashboard" / "index.html").read_text(encoding="utf-8")
check("index không nạp org.js trước console (PAGE_LAZY)",
      "/static/org.js" not in html and "/static/console.js" in html)

# Chống xóa sổ: parse lỗi không save; save không cho 3+ → ≤1
ot_path = ot.store_path()
many = {"tenants": [
    {"slug": "quan", "protected": True, "container": "javis-quan"},
    {"slug": "a", "container": "javis-a"},
    {"slug": "b", "container": "javis-b"},
    {"slug": "c", "container": "javis-c"},
]}
ot_path.write_text(json.dumps(many), encoding="utf-8")
ot_path.write_text("{bad-json", encoding="utf-8")
got = ot.load()
check("JSON hỏng không ghi đè sổ (file vẫn bad hoặc được giữ)",
      ot_path.is_file() and ("bad-json" in ot_path.read_text(encoding="utf-8")
                             or any(ot_path.parent.glob("org-tenants.bad-*"))))
check("JSON hỏng không trả sổ đầy đủ từ đĩa nhưng cũng không xóa đĩa",
      len(got.get("tenants") or []) <= 1)
# khôi phục sổ nhiều người rồi thử save thu nhỏ
ot_path.write_text(json.dumps(many), encoding="utf-8")
blocked = False
try:
    ot.save({"tenants": [{"slug": "quan", "protected": True}]})
except RuntimeError as e:
    blocked = "Từ chối ghi" in str(e)
check("chặn ghi đè sổ nhiều người thành chỉ quan", blocked and len(json.loads(ot_path.read_text())["tenants"]) >= 3)
shrink_blocked = False
try:
    ot.save({"tenants": many["tenants"][:2]})
except RuntimeError as e:
    shrink_blocked = "Từ chối ghi" in str(e)
check("chặn ghi đè sổ 4 người thành 2",
      shrink_blocked and len(json.loads(ot_path.read_text())["tenants"]) == 4)
added = ot.adopt_missing(["lananh", "thuy"])
check("thêm lại người mất khỏi sổ, không xóa người cũ",
      added == 2 and {t["slug"] for t in json.loads(ot_path.read_text())["tenants"]} >= {"quan", "a", "b", "c", "lananh", "thuy"})
bak = ot_path.with_name("org-tenants.blocked-1.json")
bak.write_text(json.dumps({"tenants": [{"slug": "hang", "name": "Hằng", "login_user": "hang"}]}), encoding="utf-8")
added_bak = ot.adopt_missing(["hang"])
hang = next(t for t in json.loads(ot_path.read_text())["tenants"] if t["slug"] == "hang")
check("gắn lại lấy tên từ bản bị chặn ghi",
      added_bak == 1 and hang.get("login_user") == "hang" and hang.get("slug") == "hang")
check("mã nguồn có chống wipe sổ", "Từ chối ghi org-tenants" in (ROOT / "server" / "org_tenants.py").read_text(encoding="utf-8"))
check("nhận lại slug từ container và volume",
      ot.slugs_from_infra(
          ["javis-lananh", "javis-manager", "javis-proxy", "javis-park"],
          ["javis-thuy_javis-brains", "javis_javis-brains"],
      ) == ["lananh", "thuy"])
ot_path.write_text("", encoding="utf-8")
empty_view = ot.load()
check("file sổ rỗng không bị ghi thành chỉ quan",
      ot_path.read_text(encoding="utf-8") == "" and empty_view.get("_do_not_save") is True)
ot_path.unlink()
restored = ot.load()
restored_slugs = {t["slug"] for t in json.loads(ot_path.read_text())["tenants"]}
check("mất file sổ thì dựng lại từ bản giữ nhiều người nhất",
      restored.get("_do_not_save") is not True and restored_slugs >= {"quan", "a", "b", "c"})

if FAIL:
    print("\nFAILED:", ", ".join(FAIL))
    raise SystemExit(1)
print("\nOK - test_org_tenants")
