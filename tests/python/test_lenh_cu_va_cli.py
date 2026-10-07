"""Kết nối cũ lên lệnh catalog mới, và trang Models đọc được trạng thái Docker tự cài CLI."""
from _paths import ROOT, SERVER  # noqa: E402,F401
import json
import os
import tempfile
import time

os.environ["JAVIS_STATE_DIR"] = tempfile.mkdtemp(prefix="javis-lenhcu-")
os.environ["JAVIS_HOME_PERSIST"] = tempfile.mkdtemp(prefix="javis-clihome-")

import cli_autoinstall  # noqa: E402
import mcp_catalog  # noqa: E402
import mcp_store  # noqa: E402

fails = []


def check(name, cond, them=""):
    print(("ok   " if cond else "FAIL ") + name + (("  [" + str(them)[:240] + "]") if them and not cond else ""))
    if not cond:
        fails.append(name)


ads = mcp_catalog.get("google-ads")
check("Google Ads chạy bản PyPI mới nhất", (ads.get("args") or []) == ["google-ads-mcp@latest"])
check("Google Ads không còn ô Project ID",
      all(f.get("key") != "project_id" for f in (ads.get("auth") or {}).get("fields") or []))

old = ["--from", "git+https://github.com/googleads/google-ads-mcp.git", "google-ads-mcp"]
cid, err = mcp_store.add_connection("google-ads", {
    "label": "cu", "command": "uvx", "args": old,
    "fields": {"client_id": "x", "client_secret": "y", "developer_token": "D"}})
check("tạo được kết nối Ads cũ", bool(cid) and not err, err)
got = next(r for r in mcp_store.resolved(enabled_only=False) if r["id"] == cid)
check("kết nối Ads cũ chạy lệnh hiện hành", got["args"] == ["google-ads-mcp@latest"], got["args"])

custom = ["google-ads-mcp==0.0.3"]
cid2, err2 = mcp_store.add_connection("google-ads", {
    "label": "tay", "command": "uvx", "args": custom,
    "fields": {"client_id": "x", "client_secret": "y", "developer_token": "D"}})
check("tạo được kết nối Ads tự sửa", bool(cid2) and not err2, err2)
got2 = next(r for r in mcp_store.resolved(enabled_only=False) if r["id"] == cid2)
check("lệnh tự sửa được giữ", got2["args"] == custom, got2["args"])

raw = json.loads((ROOT / "system" / "mcp-catalog.json").read_text(encoding="utf-8"))
for c in raw["connectors"]:
    for cu in c.get("lenh_cu") or []:
        check(f"{c['id']}: lệnh cũ không trùng lệnh hiện hành",
              (cu.get("command"), cu.get("args")) != (c.get("command"), c.get("args")))

d = cli_autoinstall.state_dir()
d.mkdir(parents=True, exist_ok=True)
(d / "agy").write_text("installing %s\n" % time.time(), encoding="utf-8")
check("đang cài thì báo installing", cli_autoinstall.state("agy") == "installing")
(d / "agy").write_text("installing %s\n" % (time.time() - 20 * 60), encoding="utf-8")
check("cài treo quá 15 phút thì báo failed", cli_autoinstall.state("agy") == "failed")
(d / "grok").write_text("ok 1\n", encoding="utf-8")
check("cài xong thì báo ok", cli_autoinstall.state("grok") == "ok")
check("máy không có file thì không nói gì", cli_autoinstall.state("khong-co") == "")

if fails:
    print(f"\nFAIL - {len(fails)}: {fails}")
    raise SystemExit(1)
print("\nOK - test_lenh_cu_va_cli")
