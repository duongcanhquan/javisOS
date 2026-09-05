"""Hợp đồng deploy VPS: một hàng SSH, pull GHCR, Pixelle tắt trước up.

Chạy: python tests/run.py vps_deploy_an_toan

Bối cảnh (2026-09-05): mỗi push lên main chạy song song Deploy + Seed + Routing + Recover
trên cùng VPS, `docker compose up --build` tại chỗ (kèm Pixelle/Playwright), rồi Conflict
tên container `/javis` và SSH timeout. Bốn chốt:

1. Mọi workflow SSH vào VPS chung concurrency group, không huỷ job đang chạy.
2. Deploy VPS kéo image GHCR của CHÍNH repo, không `--build` mỗi push.
3. Ép Pixelle=false TRƯỚC `docker compose up`, không đợi optimize.
4. Deploy không còn trigger `push` song song với publish: chờ Docker image xanh.
"""
from _paths import ROOT  # noqa: E402,F401
import re
import sys

import yaml


FAIL = []


def check(label, ok):
    print(("PASS" if ok else "FAIL") + ": " + label)
    if not ok:
        FAIL.append(label)


SSH_WORKFLOWS = (
    "apply-model-routing-vps.yml",
    "check-bots-vps.yml",
    "check-vps-health.yml",
    "cleanup-vps.yml",
    "deploy-vps.yml",
    "enable-learn-vps.yml",
    "force-morning-brief-today.yml",
    "install-antigravity-vps.yml",
    "install-ollama-vps.yml",
    "recover-vps-javis.yml",
    "seed-htdt-profile-vps.yml",
)


def wf(name):
    return (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")


def wf_data(name):
    return yaml.safe_load(wf(name))


# PyYAML biến key `on:` thành True (boolean). Lấy trigger cho đúng.
def triggers(data):
    if "on" in data:
        return data["on"]
    return data.get(True) or {}


for name in SSH_WORKFLOWS:
    data = wf_data(name)
    conc = data.get("concurrency") or {}
    check(
        f"{name}: chung group vps-ssh",
        conc.get("group") == "vps-ssh",
    )
    check(
        f"{name}: không huỷ job SSH đang chạy (cancel-in-progress: false)",
        conc.get("cancel-in-progress") is False,
    )


deploy_txt = wf("deploy-vps.yml")
deploy = wf_data("deploy-vps.yml")
on = triggers(deploy)
check(
    "deploy-vps: chờ Docker publish xong mới SSH (workflow_run)",
    isinstance(on, dict)
    and "workflow_run" in on
    and "Build & Publish Docker image (GHCR)" in str(on.get("workflow_run")),
)
check(
    "deploy-vps: không còn trigger push (tránh đua với publish + seed)",
    not (isinstance(on, dict) and "push" in on),
)
check(
    "deploy-vps: vẫn bấm tay được (workflow_dispatch)",
    isinstance(on, dict) and "workflow_dispatch" in on,
)
check(
    "deploy-vps: chỉ deploy khi publish xanh hoặc bấm tay",
    "workflow_run.conclusion" in deploy_txt and "workflow_dispatch" in deploy_txt,
)
check(
    "deploy-vps: truyền JAVIS_IMAGE (image GHCR của repo, không hardcode upstream)",
    "JAVIS_IMAGE" in deploy_txt,
)
check(
    "deploy-vps: đăng nhập GHCR trước pull (GITHUB_TOKEN)",
    "GHCR_TOKEN" in deploy_txt and "GITHUB_TOKEN" in deploy_txt,
)

script = (ROOT / "scripts" / "vps-deploy.sh").read_text(encoding="utf-8")
# Bỏ comment để không tính dòng chú thích có chữ --build.
code = "\n".join(
    ln for ln in script.splitlines()
    if not ln.lstrip().startswith("#")
)
check("vps-deploy.sh: không `up --build`", "up -d --build" not in code)
check("vps-deploy.sh: có `docker compose pull`", re.search(r"docker compose .*pull", code) is not None)
check(
    "vps-deploy.sh: không gắn compose build/source (cái đó ép build tại chỗ)",
    "docker-compose.build.yml" not in code and "docker-compose.source.yml" not in code,
)
check(
    "vps-deploy.sh: không bật profile Pixelle lúc up",
    "docker-compose.pixelle.yml" not in code and "--profile pixelle" not in code,
)
check(
    "vps-deploy.sh: không còn nhánh bật Pixelle theo .env cũ (=true)",
    "ENABLE_PIXELLE=true" not in code,
)
check("vps-deploy.sh: dùng biến JAVIS_IMAGE", "JAVIS_IMAGE" in code)

# Ép false phải đứng trước lệnh up. Không được chỉ dựa vào optimize-vps.sh.
idx_false = script.find("JAVIS_ENABLE_PIXELLE=false")
idx_up = script.find("up -d")
check(
    "vps-deploy.sh: ghi JAVIS_ENABLE_PIXELLE=false trước `up -d`",
    idx_false >= 0 and idx_up >= 0 and idx_false < idx_up,
)
idx_opt = script.find("optimize-vps.sh")
check(
    "vps-deploy.sh: không đợi optimize mới tắt Pixelle",
    idx_false >= 0 and (idx_opt < 0 or idx_false < idx_opt),
)

compose_src = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
check(
    "docker-compose.yml: image đọc JAVIS_IMAGE (fork kéo GHCR của mình, không dính upstream)",
    "${JAVIS_IMAGE:-" in compose_src,
)

if FAIL:
    print("\nFAILED:", ", ".join(FAIL))
    sys.exit(1)
print("\nOK - test_vps_deploy_an_toan: tất cả pass")
