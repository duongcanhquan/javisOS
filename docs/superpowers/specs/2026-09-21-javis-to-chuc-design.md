# Javis tổ chức: manager + Javis con (javis-quan giữ dữ liệu gốc)

**Ngày:** 2026-09-21  
**Trạng thái:** chờ duyệt (user yêu cầu viết phương án + cách làm; chưa implement)  
**Pháp lý dữ liệu:** có lưu tài khoản, brain, kết nối, khóa API → cần đồng ý khi tạo người, mã hóa khóa at rest **bằng khóa từ mật khẩu chủ tenant** (admin/manager không giải mã được), API/quy trình xóa tenant trong 72 giờ (tinh thần NĐ 13/2023/NĐ-CP).
**Toàn vẹn:** não tenant có chữ ký/HMAC; file bị sửa ngoài app (kể cả từ host) thì bản đó từ chối đọc và báo chủ.

## Mục tiêu

Một VPS, hai vai:

- `javis.vietmycollege.com` = **manager** (bản mới, trống dữ liệu cá nhân). Tạo / dừng / xóa Javis con, cấp tên miền, cấp hạn mức ổ, bật/tắt từng API pool trường hoặc bắt tự đấu nối, đẩy skill/agent/workflow/kiến thức chung.
- `javis-quan.vietmycollege.com` = **Javis của bạn hôm nay**. Cùng volume, cùng đăng nhập, cùng MCP, cùng brain. Không export-import, không xóa volume gốc.

Người khác sau này: `javis-<slug>.vietmycollege.com`, volume riêng, không đọc được bản của bạn.

## Việc không làm trong bản này

- Biến bản đang chạy thành manager rồi copy não sang `javis-quan` (đảo vai, rủi ro mất/trộn dữ liệu).
- Dùng chung một gói Claude Pro/Max / ChatGPT plan cho cả trường (ngoài phạm vi plan cá nhân). Pool trường chỉ **API key**.
- SaaS đa VPS / Kubernetes đợt 1. Một máy `14.225.205.248` (javisos-hgsg).
- OpenMAIC: giữ trên host như hiện tại; không nhân bản theo từng Javis con đợt 1.

## Hiện trạng (không được đụng volume này trừ khi gắn lại đúng tên)

Máy mới sau migrate 2026-09-20:

- IP `14.225.205.248`, app `https://javis.vietmycollege.com`
- Thư mục `/root/javis`, compose project `javis`, container `javis` + `javis-caddy`
- Volume (tên Docker thật, project `javis`):
  - `javis_javis-data` → `/data` (settings, tài khoản, session, connector-cred, chat)
  - `javis_javis-brains` → `/brains` (Brain Default, School of Art, APC.HN, memory, wiki, skill/agent user)
  - `javis_claude-auth` → `~/.claude`
  - `javis_codex-auth` → `~/.codex`
- Caddy nằm **trong** project (`docker-compose.https.yml`), giữ 80/443. Muốn nhiều tên miền thì phải chuyển sang **proxy ngoài** (`docker-compose.proxy.yml`), không dựng Caddy thứ hai.

## Hình dung khi xong (người dùng thấy gì)

1. Mở `javis-quan.vietmycollege.com` → đúng Javis bạn đang dùng: chat cũ, Models, Kết nối, Studio, brain. Đăng nhập cũ.
2. Mở `javis.vietmycollege.com` → dashboard **quản trị tổ chức** (không phải não cá nhân của bạn): danh sách Javis con, nút tạo/dừng/xóa, hạn mức, chính sách API, catalog trường.
3. Tạo người mới: manager điền slug + dung lượng + chế độ não → DNS + container + volume trống + tài khoản admin bản đó.
4. Cập nhật chung: manager sửa catalog → từng Javis con bấm **Cập nhật từ trường** (hoặc manager bấm đẩy). File user đã sửa thì không đè (cùng luật `system_sync` hiện có).

## Kiến trúc

```
DNS *.vietmycollege.com  →  14.225.205.248
                              |
                         javis-proxy (Caddy docker-proxy)
                         mạng javis-web, giữ 80/443
                              |
          +-------------------+-------------------+
          |                                       |
   javis-manager                           javis-quan
   volume MỚI (trống)                      volume CŨ (external)
   domain gốc                              javis-quan.vietmycollege.com
          |                                       |
          |  chính sách + vé API (không đưa master key)
          +---------------------------------------+
          |  catalog org (skill/agent/workflow/wiki trường)
          +---------------------------------------+
```

Ba lớp năng lực trên mỗi Javis con:

1. **Hệ thống app** - skill/agent/workflow đi theo image (`system_sync`). Update Javis = update lớp này.
2. **Catalog trường** - do manager soạn, sync xuống tenant. User sửa thì giữ bản user.
3. **Của người đó** - brain, memory, skill/agent/workflow **tự tạo**, MCP, khóa riêng. **Không ai khác đọc được nội dung**, kể cả tài khoản manager trên `javis.vietmycollege.com`. Manager chỉ: bật/tắt máy, xóa cả bản (sau xác nhận), xem **số** GB và **số** token pool trường, đẩy catalog chung. Không xem file, không impersonate, không đặt lại mật khẩu rồi tự vào.

## Cursor / GitHub = nhà máy chung, không phải não của quan

Sau cutover, khi làm việc với Cursor trên repo `javisOS`:

| Làm trên Cursor / `main` | Không làm |
|---|---|
| Sửa lỗi app, tính năng chung | Sửa memory / wiki / chat của `javis-quan` |
| Skill, agent, workflow **mặc định** (`system/`, `.claude/skills/`) | Kéo volume `/brains` hay `/data` từ VPS về máy |
| Catalog trường (soạn trên **manager**, hoặc file org trong repo rồi đẩy) | Commit kết nối MCP, settings, API key |
| Test trên bản dev/trống hoặc manager | SSH `docker exec` vào `javis-quan` để "xem giúp" |

`javis-quan` = **user thường**. Bạn vào đó như mọi người: chat, tự tạo skill, tự nối MCP. Bản đó **không** phải nguồn để push ra cả trường.

Luồng cập nhật chung: Cursor → commit `main` → image GHCR → mọi Javis con nhận lớp hệ thống (`system_sync`). Kiến thức toàn trường: soạn trên manager → đẩy catalog. Không đi đường "sửa trên quan rồi copy sang người khác".

## Bảo mật và toàn vẹn (kể cả với admin)

**Yêu cầu:** thông tin cá nhân, kỹ năng/skill riêng, kết nối của từng Javis là bí mật. Admin **không** đọc/sửa được, trừ khi chủ bản đó **đưa mật khẩu** (đăng nhập UI như user).

Tách hai vai, nói thẳng:

1. **Admin trên app manager** (người mở `javis.vietmycollege.com`):
   - Không có nút "mở brain", "đăng nhập hộ", "xem file", "docker exec", "copy volume".
   - Không reset mật khẩu thành mật khẩu admin biết rồi vào. Quên mật khẩu = chủ bản đó khôi phục (email/2FA của **họ**) hoặc xóa cả tenant rồi tạo lại (mất dữ liệu, đúng 72h).
   - Script tạo/dừng máy trên host chỉ `compose up/down` đúng project. Cấm `docker exec`, `docker cp`, mount volume tenant vào container manager.
   - Javis con **không** gắn Docker socket.

2. **Root SSH trên VPS** (ai giữ chìa máy):
   - Nếu não chỉ là file thường trên volume Docker, root **vẫn đọc được** đĩa. "Admin app không xem" là chưa đủ.
   - Đợt sản phẩm: mã hóa vault tenant **at rest**, khóa mở từ mật khẩu đăng nhập của chủ bản (KDF). Trên đĩa = ciphertext. Manager, root, backup tar đều không đọc nội dung nếu không có mật khẩu. Javis đang chạy và user đã login thì app giải mã trong RAM.
   - Toàn vẹn: mỗi object não có HMAC bằng khóa vault. Sửa lén trên đĩa → app không nạp, báo chủ.

Ngoại lệ đúng như bạn nói: người đó **share mật khẩu** (hoặc đang mở session) thì người được share vào được UI, như mọi web app.

Pool trường: manager thấy **số token / nhà cung cấp**, không thấy nội dung chat hay file trong brain.

## Cách setup tên miền

IP VPS hiện tại: **`14.225.205.248`**. Chi tiết từng nút: [deploy/org/DNS.md](../../../deploy/org/DNS.md).

Tóm tắt:

1. Giữ bản ghi A `javis.vietmycollege.com` → `14.225.205.248` (đã có).
2. Thêm A `javis-quan.vietmycollege.com` → cùng IP.
3. Nên thêm wildcard A `*.vietmycollege.com` → cùng IP (Javis con sau này không phải khai DNS từng cái).
4. TTL 300 giây lúc cắt, xong mới tăng lại.
5. Kiểm tra: `dig +short javis-quan.vietmycollege.com` ra đúng IP rồi mới cutover.
6. HTTPS: sau khi có `javis-proxy`, Caddy xin Let's Encrypt **theo từng tên** lúc mở lần đầu. Wildcard DNS không cần wildcard certificate nếu dùng on-demand từng host.

Không đổi NS sang chỗ khác nếu không cần. Làm trên đúng panel đang giữ zone `vietmycollege.com` (Cloudflare, cPanel, nhà đăng ký).

## Chính sách bộ não (manager toàn quyền)

Mỗi tenant một hồ sơ. Javis con **không** tự bật lại cái manager đã tắt.

| Chế độ | Hành vi |
|---|---|
| `school` | Chỉ pool trường, đúng các provider đã bật, trừ hạn mức |
| `byo` | Bắt tự đấu nối (API key hoặc CLI trên đúng bản đó). Pool trường cắt. Chưa nối thì chat model báo phải nối |
| `both` | Pool trường trong hạn mức, hoặc key riêng. Hết hạn mức trường thì không tự nhảy sang plan Claude chung |
| `blocked` | Không gọi model. Vào được file nếu manager cho |

Pool trường = Anthropic API / OpenRouter / Gemini API / ... (key nằm **chỉ** trên manager, mã hóa at rest). Tenant nhận **vé** (token ngắn, scoped, hết hạn) hoặc gọi qua gateway manager. Không copy master key vào volume tenant.

CLI (Claude Code subscription, Codex, Grok, Antigravity) chỉ cửa **tự đấu nối** trên volume của bản đó.

Đổi chính sách có hiệu lực lần gọi model sau.

## Hạn mức ổ

Khi tạo tenant: trần GB cho tổng `/data` + `/brains` (và auth nhỏ). Vượt trần: ghi file mới bị chặn, báo trên bản đó và trên manager. Đợt 1: kiểm tra định kỳ (du) + chặn ghi qua hook/middleware, chưa bắt buộc project quota kernel.

`javis-quan` đợt 1: trần đủ lớn (hoặc không trần) để không kẹt bản đang dùng.

## Catalog trường vs não cá nhân

- Nguồn catalog: brain riêng của **manager** (vd `org-catalog`), không trộn với volume `javis-quan`.
- Đẩy: copy/sync vào thư mục chuẩn trên tenant, ví dụ `<brain>/org/...` hoặc class `org` trong Studio, không ghi đè `skills/` user-modified (hash manifest, giống `system_sync`).
- `javis-quan` nhận catalog khi bạn (hoặc manager) bấm cập nhật. Không tự xóa kiến thức APC/School of Art.

## Xóa người

Manager bấm xóa → stop container → xóa volume tenant đó → ghi audit. Hoàn tất trong **72 giờ**. Không xóa nhầm volume `javis_*` của bản quan. Xác nhận 2 bước, gõ đúng slug.

## Đồng ý / tài khoản

Tạo tenant = tạo chỗ xử lý dữ liệu cá nhân. Manager là người vận hành trường. Tenant admin tự tạo user trên bản họ. Manager không SSO đợt 1 (mỗi bản login riêng), trừ khi làm tiếp sau spec này.

---

# Cách chuyển bản đang chạy → javis-quan (không mất dữ liệu)

Nguyên tắc: **volume cũ sống; chỉ đổi tên miền, tên container, và Caddy.** Không `docker volume rm`, không `compose down -v` trên project `javis`.

## Bước 0 - Chụp an toàn (trước mọi đổi DNS)

Trên VPS, khi Javis vẫn chạy:

1. Ghi tên volume: `docker inspect javis --format '{{range .Mounts}}{{.Name}} {{.Destination}}{{println}}{{end}}'`
2. Tar volume ra chỗ khác đĩa (scratch), giữ `javis_javis-data`, `javis_javis-brains`, `javis_claude-auth`, `javis_codex-auth`, cộng volume Caddy nếu còn (`javis_caddy-data`) để khỏi xin lại cert nếu cần.
3. Không xóa tar cho đến khi `javis-quan` chat + Models + Kết nối đã kiểm tra xong.

## Bước 1 - DNS

Thêm bản ghi **A** `javis-quan.vietmycollege.com` → `14.225.205.248`.  
Giữ A `javis.vietmycollege.com` → cùng IP.  
Nên có wildcard `*.vietmycollege.com` cho Javis con sau này.

Chưa đổi app. Chờ DNS lan.

## Bước 2 - Proxy dùng chung (cắt Caddy trong project)

Một máy một cổng 443. Làm đúng thứ tự:

1. `docker network create javis-web` (nếu chưa có).
2. Gắn container `javis` vào mạng `javis-web` (chưa stop app).
3. Bật `javis-proxy` (`docker-compose.proxy.yml`). Proxy chưa nhận traffic nếu 443 còn do `javis-caddy`.
4. Gắn nhãn Caddy lên **đúng container đang giữ volume cũ** (`DOMAIN_NAME=javis.vietmycollege.com` lần đầu) + `JAVIS_BIND=127.0.0.1`.
5. Stop + remove **chỉ** `javis-caddy` (không `-v` trên volume data/brains/auth).
6. Proxy chiếm 80/443, lái `javis.vietmycollege.com` về container cũ.
7. Kiểm tra: HTTPS gốc vẫn vào **cùng** chat/brain/Models. Nếu sai: bật lại `javis-caddy` từ backup, chưa làm bước 3.

## Bước 3 - Đổi hostname bản cũ thành javis-quan

Vẫn **cùng** project/volume:

- `JAVIS_NAME=javis-quan`
- `DOMAIN_NAME=javis-quan.vietmycollege.com`
- `JAVIS_BIND=127.0.0.1`
- `JAVIS_HOST_PORT=7777` (loopback; proxy vào mạng Docker, không cần publish 7777 ra ngoài)
- Volume **external** trỏ đúng tên cũ:

```yaml
volumes:
  javis-data:
    external: true
    name: javis_javis-data
  javis-brains:
    external: true
    name: javis_javis-brains
  claude-auth:
    external: true
    name: javis_claude-auth
  codex-auth:
    external: true
    name: javis_codex-auth
```

Cấm tạo project Docker mới mà không khai `external`, vì Compose sẽ đẻ volume trống và trông như "mất não".

Kiểm tra `https://javis-quan.vietmycollege.com`: đăng nhập cũ, chat, MCP, Claude/Codex.  
Lúc này `javis.vietmycollege.com` có thể 404 vài phút cho đến bước 4.

## Bước 4 - Dựng manager trống trên đúng tên miền gốc

Thư mục mới (vd `/root/javis-manager`), project `javis-manager`, volume **mới** (không external vào volume quan):

- `JAVIS_NAME=javis-manager`
- `DOMAIN_NAME=javis.vietmycollege.com`
- `JAVIS_BIND=127.0.0.1`
- `JAVIS_HOST_PORT=7778`
- Admin mới (`JAVIS_ADMIN_*`), không copy `settings.json` của bạn.

Kiểm tra: gốc là app sạch. `javis-quan` không đổi.

## Bước 5 - Gắn bản quan vào sổ manager

Manager ghi một bản ghi tenant: slug `quan`, domain, container, volume names, chế độ não `both` (giữ cửa đang dùng + sau này bật pool trường khi có), trần ổ rộng. Không migrate file.

---

# Phần mềm manager (làm sau khi cutover sống)

Control plane chạy **trong** `javis-manager` (plugin/tool native + trang dashboard). Socket Docker: chỉ manager được mount; **Javis con không** mount socket (tránh một người `docker rm` bản khác).

API manager (ý định, auth = admin manager):

- `GET/POST /org/tenants` tạo (slug, domain, quota_gb, brain_mode, providers[])
- `POST /org/tenants/{id}/stop|start`
- `DELETE /org/tenants/{id}` (xóa volume, 72h)
- `PATCH /org/tenants/{id}/policy` chế độ + bật từng provider + hạn mức token
- `POST /org/catalog/push` sync catalog
- `GET /org/tenants/{id}/usage` dung lượng + token pool trường
- `DELETE` hoàn tất + audit log

Tạo tenant = script trên host: mkdir, `.env`, `docker compose up -d`, nhãn Caddy, volume mới. Deploy image `ghcr.io/duongcanhquan/javisos:latest` giống bản quan.

Gateway pool trường: service nhỏ cạnh manager (hoặc route trên manager). Tenant gửi vé. Hết hạn mức / provider tắt → 403 rõ tiếng Việt, không fallback plan Claude trường.

## Rủi ro và cách tránh

| Rủi ro | Tránh |
|---|---|
| Compose project mới đẻ volume trống | `external: true` + đúng tên `javis_javis-*` |
| `compose down -v` | Cấm trong runbook cutover |
| Hai Caddy tranh 443 | Tắt `javis-caddy` trước khi proxy listen |
| Bot Telegram/Zalo chạy hai nơi | Token bot **ở lại javis-quan**; manager không gắn bot cá nhân |
| Đẩy catalog đè skill bạn sửa | Manifest hash, luật `system_sync` |
| Share Claude Pro cả trường | Không đưa vào pool; chỉ API key |

## Tiêu chí xong cutover (trước khi code manager đầy đủ)

- [ ] `javis-quan.vietmycollege.com` = dữ liệu + kết nối như trước
- [ ] `javis.vietmycollege.com` = bản trống quản trị
- [ ] Volume `javis_javis-data|brains|claude-auth|codex-auth` vẫn attach vào container quan
- [ ] Backup tar còn cho đến khi bạn xác nhận 48h ổn
- [ ] Cổng 443 chỉ `javis-proxy`

## Tiêu chí xong sản phẩm tổ chức

- [ ] Tạo/dừng/xóa Javis con từ UI manager
- [ ] Bật/tắt từng API pool / bắt BYO / khóa, hiệu lực lần gọi sau
- [ ] Trần GB + usage (số, không phải nội dung)
- [ ] Catalog trường không đè file user-modified
- [ ] Xóa tenant xong trong 72h, có audit
- [ ] Manager không đọc/sửa brain, skill riêng, chat, MCP của tenant
- [ ] Volume tenant trên đĩa là ciphertext nếu chưa login; HMAC phát hiện sửa lén
- [ ] Cursor/`main` không chứa dữ liệu `javis-quan`
