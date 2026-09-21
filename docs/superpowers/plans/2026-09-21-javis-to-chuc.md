# Javis tổ chức Implementation Plan

> **For agentic workers:** triển khai từng task; dùng checkbox `- [ ]` để theo dõi. **Không bắt đầu** cho đến khi user duyệt spec `docs/superpowers/specs/2026-09-21-javis-to-chuc-design.md` và bảo chạy plan này.

**Spec:** [2026-09-21-javis-to-chuc-design.md](../specs/2026-09-21-javis-to-chuc-design.md)

**Goal:** Tách bản đang chạy thành `javis-quan` (giữ nguyên volume/kết nối), dựng manager trống tại `javis.vietmycollege.com`, rồi thêm control plane (tạo/dừng/xóa, chính sách API, catalog, quota ổ).

**Architecture:** Một VPS, `javis-proxy` giữ 80/443, mỗi Javis một compose + volume. Bản quan mount **external** `javis_javis-data|brains|claude-auth|codex-auth`. Manager project mới, volume mới. Pool trường = API key trên manager, tenant nhận vé. CLI subscription chỉ cửa tự đấu nối.

**Tech Stack:** Docker Compose v2, Caddy docker-proxy, FastAPI sẵn có, plugin/tool Python trong `javis-manager`, dashboard JS IIFE, test `python tests/python/test_*.py` / `node tests/js/test_*.js`.

## Global Constraints

- **Không em dash (U+2014)** trong mã, docs, UI.
- **Cấm** `docker volume rm` / `compose down -v` trên volume `javis_javis-*` trong mọi task cutover.
- Volume bản quan luôn `external: true` + đúng tên inspect được từ container hiện tại. Sai tên = não trống.
- Javis con **không** mount `/var/run/docker.sock`. Manager không `docker exec` / `docker cp` / mount volume tenant.
- Admin app **không** đọc brain, skill riêng, chat, connector. Không impersonate. Không reset mật khẩu rồi tự vào. Quên mật khẩu = khôi phục của chủ tenant hoặc xóa cả bản.
- Vault tenant mã hóa at rest bằng khóa từ mật khẩu chủ; HMAC toàn vẹn. Root VPS không đọc plaintext nếu chưa login.
- Cursor/`main` chỉ lớp hệ thống + catalog trường. Không kéo `/brains` hay `/data` của `javis-quan` vào git.
- DNS: xem `deploy/org/DNS.md`. Cutover Task 4 chỉ sau khi `dig` ra `14.225.205.248` cho `javis-quan`.
- Pool trường không dùng Claude Pro/Max / ChatGPT plan chung. Chỉ API key.
- Xóa tenant: xong trong 72 giờ, audit, xác nhận 2 bước, không đụng volume quan.
- Khóa API trường mã hóa at rest (Fernet/`secrets_store` như settings hiện có).
- Cutover (Task 1-5) ship được **trước** UI manager đầy đủ. Không trộn "đổi DNS" với "viết trang tổ chức".
- Tiếng Việt có dấu trong `server/*.py` và chuỗi UI. File JS dashboard theo lệ file đang sửa.

---

### Task 1: Overlay compose "tenant gắn volume có sẵn" ✅

Chốt cách khai volume external trong repo để không đẻ volume trống khi đổi tên container.

**Files:**
- Create: `deploy/org/docker-compose.tenant-external.yml`
- Create: `deploy/org/env.quan.example`
- Test: `tests/python/test_org_tenant_volumes.py`

**Làm:**
- Overlay chỉ khai 4 volume `external: true` với tên đặt bằng biến (mặc định `javis_javis-data` v.v.).
- `env.quan.example`: `JAVIS_NAME=javis-quan`, `DOMAIN_NAME=javis-quan.vietmycollege.com`, `JAVIS_BIND=127.0.0.1`, `COMPOSE_PROJECT_NAME` ghi chú: không đổi project nếu đã dùng `javis`, hoặc giữ project `javis` và chỉ đổi `JAVIS_NAME`.
- Test: file YAML parse được; có `external: true`; có 4 tên volume; **không** có `down -v` trong file.

**Xong khi:** test xanh. Chưa SSH VPS.

---

### Task 2: Runbook cutover (người + script kiểm tra, chưa xóa gì) ✅

**Files:**
- Create: `deploy/org/CUTOVER.md` (copy ngắn từ spec, lệnh inspect/backup/gắn mạng, thứ tự tắt `javis-caddy`)
- Create: `scripts/org_cutover_preflight.sh` (chỉ đọc: in volume, domain, caddy vs proxy, từ chối nếu thiếu 4 volume)
- Test: `tests/python/test_org_cutover_preflight.py` (script tồn tại, `set -e`, không `volume rm`, không `down -v`)

**Làm:** script exit 1 nếu không thấy `javis_javis-brains`. Không sửa container.

**Xong khi:** test xanh. In được checklist.

---

### Task 3: Backup volume (chạy trên VPS khi user bảo) ✅ 2.7G `/var/backups/javis-quan-20260921-103129.tgz`

**Files:**
- Create: `scripts/org_backup_volumes.sh` (docker run alpine tar 4 volume ra `/var/backups/javis-quan-<date>.tgz` hoặc volume scratch)
- Test: `tests/python/test_org_backup_script.py` (có đủ 4 tên volume, không `volume rm`)

**Làm trên VPS (thủ công sau khi user duyệt):** chạy script, `ls -lh` file tar.

**Xong khi:** có file backup kích thước hợp lý (não hiện tại cỡ GB). Chưa đổi DNS.

---

### Task 4: DNS + proxy + nhãn, vẫn phục vụ `javis.vietmycollege.com` trên volume cũ (proxy ✅ 2026-09-21; DNS javis-quan còn thiếu)

Ops trên VPS. Code repo chỉ bổ sung nếu thiếu nhãn trong `docker-compose.multi.yml` (đã có).

**Files (nếu cần):**
- Modify: `deploy/org/CUTOVER.md` ghi lệnh đã chạy và kết quả
- Không đổi `scripts/vps-deploy.sh` theo hướng gỡ Caddy của bản quan cho đến khi proxy sống (Task 4 xong mới Task 5)

**Làm:**
1. User thêm A `javis-quan` (và wildcard `*` nếu zone cho phép). Làm theo `deploy/org/DNS.md`. `dig +short javis-quan.vietmycollege.com` phải ra `14.225.205.248`.
2. `docker network create javis-web`
3. `docker compose -f docker-compose.proxy.yml -p javis-proxy up -d`
4. Gắn javis vào `javis-web`, `JAVIS_BIND=127.0.0.1`, nhãn Caddy domain **hiện tại**
5. Stop `javis-caddy` (không `-v` data)
6. Kiểm tra `https://javis.vietmycollege.com/health` và đăng nhập thật

**Rollback:** `docker compose -f docker-compose.yml -f docker-compose.https.yml up -d caddy` nếu proxy hỏng.

**Xong khi:** HTTPS gốc vẫn đúng não cũ.

---

### Task 5: Đổi domain bản cũ → `javis-quan`, dựng manager trống trên gốc

**Files:**
- Create: `deploy/org/env.manager.example`
- Create: `deploy/org/docker-compose.manager.yml` (multi + **không** external volume quan)
- Modify: `scripts/vps-deploy.sh` chỉ khi cần: nếu có `javis-proxy` và network `javis-web` thì up kèm `docker-compose.multi.yml`, **không** `--remove-orphans` giết proxy. Test `test_vps_deploy_an_toan.py` cập nhật: không gỡ `javis-proxy`.

**Làm trên VPS:**
1. `.env` bản cũ: `DOMAIN_NAME=javis-quan.vietmycollege.com`, `JAVIS_NAME=javis-quan`, overlay external volumes
2. Recreate **container** (không xóa volume)
3. Kiểm tra `https://javis-quan.vietmycollege.com` = não cũ
4. `/root/javis-manager` up image mới, domain gốc, volume mới, admin mới
5. Kiểm tra gốc trống; quan không đổi
6. Ghi tenant `quan` vào file tạm `deploy/org/tenants.example.json` (slug, volumes) để Task 6 đọc format

**Xong khi:** hai URL đúng vai. Backup tar vẫn giữ.

---

### Task 6: Sổ tenant + API manager (tạo/dừng/start, chưa xóa volume)

**Files:**
- Create: `server/org_tenants.py` (store JSON dưới `/data/state/org-tenants.json` **chỉ** khi `JAVIS_ORG_MANAGER=true`)
- Create: `server/routes` hoặc gắn `main.py` các endpoint `/org/tenants` (auth admin)
- Create: `tests/python/test_org_tenants.py`
- Create: trang dashboard tối thiểu (danh sách + stop/start) - file JS/HTML theo lệ console, cache-bust

**Interfaces:**
- Tenant record: `id, slug, domain, compose_dir, container, volumes[], brain_mode, providers[], quota_gb, status`
- `JAVIS_ORG_MANAGER` false trên `javis-quan` → 404 mọi `/org/*`

**Xong khi:** test store + 404 khi không phải manager. UI manager thấy bản `quan` (nhập tay lần đầu).

---

### Task 7: Tạo Javis con mới (script host)

**Files:**
- Create: `scripts/org_provision_tenant.sh` (mkdir, env, compose multi, volume mới, không đụng `javis_javis-*`)
- Test: `tests/python/test_org_provision_script.py` (từ chối slug `quan` trùng volume gốc; slug chỉ `[a-z0-9-]`)

**Làm:** API Task 6 gọi script (manager có socket). Dry-run trong test không cần Docker.

**Xong khi:** provision từ chối tên volume của quan. Trên VPS: tạo 1 tenant thử rồi xóa bằng Task 9.

---

### Task 8: Chính sách API + gateway vé

**Files:**
- Create: `server/org_brain_policy.py` (mode, providers, quota token)
- Create: `server/org_gateway.py` hoặc nhánh trong engine: tenant không đọc master key
- Modify: trang Models (ẩn provider trường khi policy tắt; hiện "bắt tự đấu nối")
- Test: `tests/python/test_org_brain_policy.py`

**Làm:** manager PATCH policy. Tenant mỗi lần gọi model hỏi manager (hoặc file policy mount read-only). Hết hạn mức / `byo` chưa có key → lỗi tiếng Việt, không fallback subscription trường.

**Xong khi:** test 4 mode. `javis-quan` mặc định `both`, providers trường tắt cho đến khi bạn bật.

---

### Task 9: Xóa tenant 72h + audit

**Files:**
- Modify: `server/org_tenants.py` DELETE: stop, `volume rm` **chỉ** volume trong record, audit append-only
- Test: record `quan` bị từ chối xóa; slug thử mới thì xóa được trong test giả lập

**Xong khi:** không có đường code nào xóa `javis_javis-brains` từ API.

---

### Task 10: Quota ổ + usage (+ RAM/CPU tenant)

Overlay sẵn: `deploy/org/docker-compose.tenant-limits.yml` (768 MB, 0.75 CPU, plugin user tắt). Javis gốc và `javis-quan` không gắn file này.

**Files:**
- Create: `scripts/org_disk_usage.sh` (`du` trên mount)
- Modify: manager GET usage; tenant middleware chặn ghi khi vượt trần (đường write vault)
- Test: `tests/python/test_org_quota.py` (giả lập over quota)

**Xong khi:** `quan` trần rộng / tắt. Tenant thử bị chặn khi set trần 0 trong test.

---

### Task 11: Catalog trường (sync không đè user-modified)

Nguồn soạn: Javis gốc (`javis.vietmycollege.com`) brain `org-catalog`. Tenant mới nhận lúc tạo. Tenant cũ: nút đẩy. Không copy chat/MCP/não quan.

**Files:**
- Create: `server/org_catalog.py` (tái sử dụng hash/manifest như `system_sync.py`)
- Test: `tests/python/test_org_catalog.py` (file user-modified giữ; file chưa sửa nhận bản mới)

**Xong khi:** đẩy 1 skill org vào tenant thử; skill tự tạo trên quan không mất.

---

### Task 12: Manager không đụng nội dung tenant (allowlist Docker)

**Files:**
- Create: `scripts/org_compose_guard.py` hoặc wrapper: chỉ `up`/`down`/`ps` theo `compose_dir` trong sổ tenant
- Test: `tests/python/test_org_docker_guard.py` (cấm `exec`, `cp`, `run` tùy ý, cấm volume name `javis_javis-*` trừ start/stop bản quan)

**Xong khi:** API manager không có đường đọc file trong `/brains` tenant.

---

### Task 13: Mã hóa vault + HMAC (admin/root không đọc plaintext)

**Files:**
- Create: `server/org_vault_crypto.py` (KDF từ mật khẩu login, encrypt at rest, HMAC)
- Test: `tests/python/test_org_vault_crypto.py` (sai mật khẩu không giải mã; sửa 1 byte trên đĩa → từ chối đọc)

**Làm:** bật cho tenant mới ngay. `javis-quan`: migration mã hóa khi chủ đang login (một lần), backup tar trước. Không giữ khóa trên manager.

**Xong khi:** dump volume không ra được memory/skill plaintext.

---

### Task 14: CHANGELOG cho người đọc điện thoại

Sau khi Task 5 sống (cutover) ghi 1-2 dòng user-facing: có `javis-quan` và trang gốc là quản trị. Sau Task 8-13 ghi thêm tạo người / chính sách API / não riêng. `VERSION` khớp.

---

## Thứ tự ship

1. Task 1-2 (repo, an toàn) → DNS `deploy/org/DNS.md` + 3-5 (VPS) → 6-13 (sản phẩm, 12-13 là bảo mật) → 14.

Không implement Task 6-13 trước khi Task 5 xanh trên máy thật.
Không kéo brain `javis-quan` vào Cursor.
