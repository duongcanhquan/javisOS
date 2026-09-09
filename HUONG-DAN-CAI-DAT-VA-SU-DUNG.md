# Hướng dẫn cài đặt & sử dụng Javis OS (sau đóng gói)

***Tiếng Việt** · Bản này dành cho người nhận **bản đóng gói** (ZIP máy cá nhân hoặc image Docker trên VPS).*

Tài liệu này dẫn từ lúc **cài lần đầu** tới lúc **dùng được chat, Studio, Kết nối**.  
**PDF tải về (có hình / sơ đồ):** [Cài đặt](docs/huong-dan/HUONG-DAN-CAI-DAT-Javis-OS.pdf) · [Sử dụng ban đầu](docs/huong-dan/HUONG-DAN-SU-DUNG-Javis-OS.pdf) - mục lục đầy đủ trong [docs/huong-dan/README.md](docs/huong-dan/README.md).  
Chi tiết từng trang trong app: [docs/README.md](docs/README.md).  
Cài nhanh theo đối tượng trường: [CAI-DAT-TRUONG.md](CAI-DAT-TRUONG.md).  
**VPS mới, chưa có tên miền (IP / tunnel / Hostinger miễn phí):** [HUONG-DAN-CAI-VPS-KHONG-TEN-MIEN.md](HUONG-DAN-CAI-VPS-KHONG-TEN-MIEN.md).  
**Máy local Windows / Mac (+ Ollama tùy chọn):** [HUONG-DAN-CAI-MAY-LOCAL.md](HUONG-DAN-CAI-MAY-LOCAL.md).  
Kỹ thuật VPS sâu: [DEPLOY.md](DEPLOY.md).

---

## 1. Bản đóng gói gồm gì / không gồm gì

### Có sẵn (dùng chung trên cùng một Javis)

| Loại | Nội dung |
|---|---|
| **Phần mềm** | Dashboard + server + cập nhật theo phiên bản |
| **Skills hệ thống** | Toàn bộ skill trong `.claude/skills/` (đồng bộ vào mỗi brain mới) |
| **Agents / Workflows chuẩn** | Tự đồng bộ từ `system/agents/` + `system/workflows/` vào mỗi brain (không cần bấm Studio). Studio chỉ để làm mới / bổ sung |
| **Plugins hệ thống** | Tool native đi kèm app (lịch VN, schedule, task, ảnh ChatGPT, Zalo image…) |

Skills / agent / workflow **dùng chung** trên cùng một bản Javis: mọi brain đều nhận được bộ năng lực chuẩn.  
**Project (dự án chat)** thuộc **đúng một brain** - không lẫn giữa các não.

### Không đi kèm (người dùng tự làm)

| Loại | Lý do |
|---|---|
| **Bộ nhớ / wiki / sources cá nhân** | Kiến thức riêng của người phát hành - không đóng gói |
| **Kết nối MCP** (Gmail, Ads, Zalo, POS…) | Mỗi người tự đăng nhập / dán key / quét QR |
| **API key / đăng nhập Claude / ChatGPT / Antigravity** | Thuộc tài khoản cá nhân |
| **Tên miền / SSL** | Phụ thuộc VPS và DNS của bạn |

> **Nguyên tắc phân phối:** gửi phần mềm + hướng dẫn này. **Không** gửi thư mục `brains/` có memory, Drive cá nhân, mật khẩu hay hội thoại thật.

---

## 2. Chọn đúng đường cài

| Bạn đang cài trên… | Hệ điều hành | Mục đọc |
|---|---|---|
| Laptop / PC cá nhân | **Windows** | [§3](#3-máy-cá-nhân---windows) |
| Laptop / PC cá nhân | **macOS** | [§4](#4-máy-cá-nhân---macos) |
| VPS / máy chủ | **Linux** (Ubuntu, Debian, Hostinger…) | [§5](#5-vps-linux---docker-khuyến-nghị) |
| VPS / máy chủ | **Windows Server** (hoặc PC Windows chạy 24/7) | [§6](#6-vps--máy-chủ-windows) |
| Muốn link đẹp + HTTPS | Có VPS + domain (hoặc subdomain Hostinger) | [§7](#7-map-tên-miền--https) |

Cổng mặc định: **7777**. Trên máy mình: `http://localhost:7777`.

---

## 3. Máy cá nhân - Windows

### 3.1 Chuẩn bị (một lần)

1. Cài **Python 3.11+** từ [python.org](https://www.python.org/downloads/).  
   Khi cài: **tick** *Add python.exe to PATH*.
2. (Khuyến nghị) Cài **Node.js 22 LTS** từ [nodejs.org](https://nodejs.org/) - cần cho Claude Code / Codex / một số kết nối (Zalo…).
3. Tải **ZIP bản đóng gói** (hoặc Download ZIP từ GitHub do admin gửi).
4. Giải nén ra thư mục dễ nhớ, ví dụ `D:\Javis`.

### 3.2 Cài lần đầu

1. Mở thư mục vừa giải nén.
2. Double-click **`1-Cai-dat.bat`** (lần đầu có thể vài phút: tạo venv, cài thư viện).
3. Thấy dòng có `http://localhost:7777` là xong.
4. Mở Chrome / Edge → **http://localhost:7777**.
5. Tạo tài khoản admin (máy cá nhân có thể bỏ trống mật khẩu nếu chỉ mình dùng; vẫn nên đặt mật khẩu).

### 3.3 Các ngày sau

| Việc | File |
|---|---|
| Bật Javis | `2-Bat-Javis.bat` (chạy nền) hoặc `JAVIS OS.bat` (mở như app) |
| Tắt | `3-Tat-Javis.bat` hoặc `stop-javis.bat` |
| Tự chạy khi đăng nhập Windows | `javis-autostart.bat install` |

Chi tiết ngắn: [CAI-DAT-MAY-CA-NHAN.md](CAI-DAT-MAY-CA-NHAN.md).

---

## 4. Máy cá nhân - macOS

### 4.1 Chuẩn bị (một lần)

1. Mở Terminal, chạy (nếu chưa có công cụ build):

```bash
xcode-select --install
```

2. Cài Python 3 từ [python.org/macos](https://www.python.org/downloads/macos/) hoặc `brew install python`.
3. (Khuyến nghị) Node.js 22 LTS.
4. Tải ZIP → giải nén, ví dụ `~/Desktop/Javis`.

### 4.2 Cài lần đầu

1. Chuột phải **`1-Cai-dat.command`** → **Open** (macOS có thể hỏi xác nhận nhà phát triển).
2. Đợi script xong → mở **http://localhost:7777**.
3. Tạo tài khoản admin.

Nếu báo *không xác định được nhà phát triển*: **System Settings → Privacy & Security → Open Anyway**, rồi chạy lại.

### 4.3 Các ngày sau

| Việc | File |
|---|---|
| Bật | `2-Bat-Javis.command` hoặc double-click `JAVIS OS.app` |
| Tắt | `3-Tat-Javis.command` |
| Tự chạy khi đăng nhập | `./bin/javis-autostart.sh install` |

---

## 5. VPS Linux - Docker (khuyến nghị)

Cần quyền SSH vào VPS. Image mặc định fork:

`ghcr.io/duongcanhquan/javisos:latest`

> Package GHCR phải **Public** (hoặc bạn đã `docker login ghcr.io`) thì Hostinger / máy mới pull được.

### 5.1 Cài Docker (nếu chưa có)

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker "$USER"
# Đăng xuất SSH rồi vào lại để group docker có hiệu lực
```

### 5.2 Cách nhanh - VPS bất kỳ (IP:7777)

```bash
mkdir -p ~/javis && cd ~/javis
curl -fsSLO https://raw.githubusercontent.com/duongcanhquan/javisOS/main/docker-compose.yml

# (Tuỳ chọn) đăng nhập Claude trong container một lần
docker compose run --rm javis claude auth login --claudeai

docker compose up -d
```

Mở `http://<IP-VPS>:7777`.  
Xem log / MÃ THIẾT LẬP:

```bash
docker compose logs javis | tail -80
# hoặc trong container:
docker compose exec javis cat /data/state/.setup_token
```

Lệnh hằng ngày:

```bash
docker compose logs -f      # theo dõi
docker compose restart      # khởi động lại
docker compose pull && docker compose up -d   # cập nhật image
docker compose down         # tắt (data trong volume vẫn còn)
```

### 5.3 Hostinger Docker Manager (HTTPS dễ nhất)

1. hPanel → **VPS** → **Docker Manager** → **Compose** → **URL**.
2. Dán:

```text
https://raw.githubusercontent.com/duongcanhquan/javisOS/main/docker-compose.hostinger.yml
```

(Hoặc bản trường: `.../deploy/school/docker-compose.hostinger.yml`)

3. Ô **Environment** điền tối thiểu:

| Biến | Ví dụ | Ý nghĩa |
|---|---|---|
| `DOMAIN_NAME` | `javis.srvXXXX.hstgr.cloud` hoặc `javis.tencuaban.com` | Link HTTPS |
| `JAVIS_ADMIN_USER` | `admin` | Tài khoản |
| `JAVIS_ADMIN_PASSWORD` | mật khẩu mạnh (≥8) | Đăng nhập ngay, không cần MÃ THIẾT LẬP |

4. **Deploy** → đợi 1-3 phút Traefik cấp SSL → mở `https://<DOMAIN_NAME>`.

**Subdomain miễn phí Hostinger (không mua domain):**

1. Xem hostname VPS ở hPanel (vd `srv1782015.hstgr.cloud`).
2. Đặt `DOMAIN_NAME=javis.srv1782015.hstgr.cloud`.
3. Không cần tạo bản ghi DNS tay - wildcard `*.hstgr.cloud` đã có.

### 5.4 Linux native (không Docker)

```bash
git clone https://github.com/duongcanhquan/javisOS.git javis && cd javis
chmod +x install.sh && ./install.sh
```

Script cài Python/Node/CLI, tạo venv, đăng ký **systemd** tự chạy khi boot. Chi tiết: [DEPLOY.md](DEPLOY.md).

---

## 6. VPS / máy chủ Windows

### 6.1 Docker Desktop (gần giống Linux)

1. Cài [Docker Desktop](https://www.docker.com/products/docker-desktop/) (bật WSL2 nếu được hỏi). Đợi engine xanh.
2. PowerShell:

```powershell
mkdir $HOME\javis; cd $HOME\javis
Invoke-WebRequest -Uri https://raw.githubusercontent.com/duongcanhquan/javisOS/main/docker-compose.yml -OutFile docker-compose.yml
docker compose up -d
```

3. Mở `http://<IP>:7777`. Mở **Windows Firewall** inbound TCP **7777** (và **80/443** nếu dùng reverse proxy).
4. Cập nhật: `docker compose pull` rồi `docker compose up -d`.

### 6.2 Native Windows (không Docker, chạy 24/7)

Giống máy cá nhân (§3) nhưng:

1. Giải nén trên ổ máy chủ, chạy `1-Cai-dat.bat`.
2. `javis-autostart.bat install` để tự bật khi đăng nhập.
3. Bind ra mạng: cấu hình lắng nghe `0.0.0.0` (xem [DEPLOY.md](DEPLOY.md) / [docs/16-cau-hinh-env.md](docs/16-cau-hinh-env.md)).
4. Javis **bắt buộc đăng nhập** khi chạy public - đặt admin mạnh.
5. Đăng nhập Claude / Antigravity trên VPS không màn hình: dùng tab **Code / Terminal** trong dashboard (link + dán mã).

---

## 7. Map tên miền & HTTPS

### 7.1 Vì sao cần HTTPS

- Link đẹp, không nhớ IP:cổng.
- **Micro / giọng nói** trên trình duyệt **chỉ** chạy trên `https://` hoặc `localhost`.  
  Mở `http://IP:7777` từ máy khác → mic bị chặn.

### 7.2 Hostinger (Traefik) - cách ngắn

Đã mô tả ở §5.3: chỉ cần `DOMAIN_NAME` đúng.

**Tên miền riêng trên Hostinger:**

1. Mua / trỏ domain về VPS.
2. DNS nhà cung cấp domain:

| Loại | Name | Value |
|---|---|---|
| **A** | `javis` (hoặc `@` nếu dùng root) | IP VPS Hostinger |

3. Đặt `DOMAIN_NAME=javis.tencuaban.com` trong Docker Manager → Redeploy.
4. Đợi DNS lan (vài phút đến vài giờ) → mở `https://javis.tencuaban.com`.

Trên Hostinger, nút **Bật SSL** trong Cài đặt app thường **ẩn** - Traefik lo SSL.

### 7.3 VPS tự quản + Caddy (docker-compose.https.yml)

1. Deploy Javis bằng `docker-compose.yml` trước (chạy được bằng IP).
2. Trỏ DNS **A** của `javis.tencuaban.com` → IP VPS. Mở firewall **80** và **443**.
3. Chạy kèm lớp HTTPS:

```bash
cd ~/javis
# file https nằm cùng repo; tải thêm nếu chỉ có compose gốc:
curl -fsSLO https://raw.githubusercontent.com/duongcanhquan/javisOS/main/docker-compose.https.yml
docker compose -f docker-compose.yml -f docker-compose.https.yml up -d
```

4. Trong app: **Cài đặt → Giọng nói, thương hiệu & truy cập → TÊN MIỀN & SSL**:
   - Nhập `javis.tencuaban.com` → **Lưu & kiểm tra**.
   - Khi badge DNS = đã trỏ đúng → **Bật SSL**.
   - Mở `https://javis.tencuaban.com`.

Hướng dẫn UI đầy đủ: [docs/15-thuong-hieu-ten-mien.md](docs/15-thuong-hieu-ten-mien.md).

### 7.4 Cloudflare Tunnel (HTTPS không cần mua domain)

Trên máy đã có `docker-compose.yml` có profile tunnel:

```bash
docker compose --profile tunnel up -d
docker compose logs tunnel | grep trycloudflare
```

Mở URL `https://….trycloudflare.com`. URL đổi mỗi lần restart trừ khi cấu hình *named tunnel* + `TUNNEL_TOKEN` (xem [DEPLOY.md](DEPLOY.md)).

### 7.5 Checklist DNS nhanh

1. `ping javis.tencuaban.com` (hoặc tra A record) phải ra **đúng IP VPS**.
2. Cổng 80/443 mở với thế giới (hoặc Traefik Hostinger đã mở).
3. Không trỏ CNAME vòng về chỗ khác khi đang dùng bản ghi A.
4. Sau khi đổi DNS, đợi TTL rồi **Kiểm tra lại** trong Cài đặt.

---

## 8. Thiết lập lần đầu trong app (mọi đường)

Làm theo thứ tự:

### Bước A - Tài khoản admin

- Máy cá nhân: wizard chào mừng → Workspace + (tuỳ chọn) mật khẩu.
- VPS công khai: **bắt buộc** mật khẩu ≥8 ký tự. Nếu chưa set sẵn trong compose → nhập **MÃ THIẾT LẬP** (lấy từ log / file `.setup_token`).

Chi tiết: [docs/01-bat-dau-thiet-lap.md](docs/01-bat-dau-thiet-lap.md).

### Bước B - Chọn bộ não (Models)

Nhóm **Kết nối → Models**. Chọn **một** trong các đường phổ biến:

| Đường | Cần gì | Ghi chú |
|---|---|---|
| **Claude Code** | Đăng nhập subscription (link + code) | Đủ tool + shell; cẩn thận khi chạy nền 24/7 trên gói Pro/Max |
| **ChatGPT (Codex)** | Đăng nhập ChatGPT Plus/Pro | Vẫn dùng MCP hub của Javis |
| **Grok Build** | Đăng nhập SuperGrok / X Premium+ | CLI `grok`, gắn plan không cần API key |
| **Antigravity CLI** | Cài `agy`, đăng nhập một lần | Lineup model Google plan; VPS: in link trong terminal |
| **OpenRouter / OpenAI / Gemini / Anthropic / Groq / DeepSeek / Ollama** | API key | Không cần CLI; không chạy lệnh máy |

Sau khi kết nối: chọn **Main Model** + (tuỳ chọn) **Model việc nền** rẻ hơn.

Chi tiết: [docs/10-models-va-engine.md](docs/10-models-va-engine.md).

### Bước C - Năng lực chuẩn (tự có sẵn)

Image / bản đóng gói **tự đồng bộ** skill + agent + workflow hệ thống vào mỗi brain mới (qua `system_sync`). Không bắt buộc bấm Studio.

Vào **Studio** (nhóm Năng lực) chỉ khi muốn **làm mới / bổ sung** bộ seed biến thể:

| Nút Studio | Khi nào cần |
|---|---|
| **Bộ Trường** / **Bộ Bài giảng** / **Bộ Marketing** / … | Làm mới nội dung seed hoặc brain cũ trước khi có sync agent |

Agents / workflows chuẩn nằm trong `system/agents/` và `system/workflows/` của app. Agent HTĐT / dự án APC nội bộ **không** đi kèm image.
### Bước D - Brain & Project

1. Tạo / chọn **brain** theo ngữ cảnh (vd công việc vs học tập). Mỗi brain có memory / wiki / sources riêng.
2. **Project** chỉ thuộc brain đang chọn. Không kỳ vọng thấy dự án của não khác.
3. Agent / workflow / skill **chuẩn** dùng chung trên instance; nội dung vault vẫn riêng từng não.

---

## 9. Danh mục năng lực đóng gói (tham chiếu)

### Skills hệ thống (ví dụ nhóm chính)

Đi kèm image / ZIP (đồng bộ qua `system_sync`):

- **Lõi Javis:** `javis-builder`, `ingest-source`, `query-wiki`, `lint-wiki`, `notes`, `html-to-webcake`
- **Nghiên cứu & KD/MKT:** `nghien-cuu-thi-truong`, `ke-hoach-kinh-doanh`, `ke-hoach-marketing`, `phan-tich-tai-chinh-mkt`, `proposal-chien-luoc`, `quy-trinh-van-hanh-kd-mkt`, `writing-plans`, `brainstorming`
- **Marketing / SEO:** `marketing-hub`, `kiem-tra-seo`, `seo-gpt`, `viet-bai-seo`, `bao-cao-facebook-ads`, `tong-ket-facebook`
- **Bài giảng / nội dung:** `tao-bai-giang`, `bai-giang-lop-hoc`, `bai-giang-slide`, `bai-giang-van-ban`, `openmaic`
- **Video:** `lam-video`, `paperdesign`, `pixcelvideo`, `remotion-best-practices`
- **Pháp chế:** `phap-che`, `so-sanh-van-ban-phap-ly`, `snapshot-van-ban-web`
- **Vận hành ngày:** `tong-ket-sang`, `tong-hop-bao-chi`, `phan-tich-cuoc-hop`, `tong-ket-chat-ngay`, `deep-research`
- **UI / web:** `frontend-design`, `improve-ui`, `baseline-ui`, `create-design-md`, …

Danh sách đầy đủ: thư mục `.claude/skills/` trong bản đóng gói.

### Agents / Workflows không đưa vào bản công khai

Ví dụ kiến thức / vai trò **riêng tổ chức** (giữ trên brain admin, không seed cho người lạ) - danh sách đủ: [`system/EXCLUDE-AGENTS.md`](system/EXCLUDE-AGENTS.md):

- Agent HTĐT nội bộ: thực tập DN, hợp tác quốc tế HTĐT, tư vấn BGH, đánh giá đối tác HTĐT, đổi mới công nghệ nhà trường…
- Agent dự án APC: `du-an-uav`, `du-an-dien-tu-fdi`
- Memory, Drive corpus, sources pháp chế đã ingest, hội thoại, Project cá nhân

Người nhận tự xây agent riêng trong brain của họ khi cần. Caps dùng chung: [`system/README-CAPS.md`](system/README-CAPS.md).

---

## 10. Kết nối dịch vụ ngoài (người dùng tự làm)

Bản đóng gói **không** sẵn Gmail/Ads/Zalo của người phát hành. Mỗi người vào **Kết nối** và tự gắn.

### 10.1 Luồng chung

1. Rail trái → nhóm **Kết nối** → **Kết nối**.
2. Nhiều dịch vụ nằm trong tab **Javis Store**: tìm → **Cài đặt** → quay lại **Kết nối sẵn có**.
3. Bấm **Kết nối** trên thẻ dịch vụ → dán key / OAuth / quét QR theo hướng dẫn trong hộp thoại.
4. Chọn **mức quyền** trên chip tài khoản: Chỉ đọc / Ghi nháp / Toàn quyền.
5. Kiểm tra bằng chat: “kiểm tra kết nối …” hoặc hỏi số liệu thật.

Chi tiết đầy đủ từng dịch vụ: [docs/09-mcp-va-so-lieu.md](docs/09-mcp-va-so-lieu.md).

### 10.2 Bảng lối tắt theo kênh

| Muốn… | Làm gì | Tài liệu |
|---|---|---|
| Đổi / thêm bộ não AI | Models | [docs/10-models-va-engine.md](docs/10-models-va-engine.md) |
| Hỏi Javis trên điện thoại | Kết nối Telegram bot | [docs/11-telegram.md](docs/11-telegram.md) |
| Zalo Bot chính thức | Kênh Zalo Bot | [docs/26-kenh-zalo-bot.md](docs/26-kenh-zalo-bot.md) |
| Đọc/gửi Zalo cá nhân (MCP) | Zalo Agent - quét QR | [docs/12-zalo.md](docs/12-zalo.md) |
| Gmail / Lịch / Drive / Sheets | Thẻ Google trên Kết nối | [docs/09-mcp-va-so-lieu.md](docs/09-mcp-va-so-lieu.md) |
| Meta Ads / Facebook Page | Cài từ Store rồi OAuth / token | [docs/09](docs/09-mcp-va-so-lieu.md) + skill báo cáo Ads |
| Kho Drive → Second Brain | Bộ não → Kho Drive (rclone) | [docs/29-kho-drive.md](docs/29-kho-drive.md) |
| Sao lưu brain lên GitHub | Cài đặt / Sao lưu | [docs/18-sao-luu-github.md](docs/18-sao-luu-github.md) |
| Logo + domain trong UI | Cài đặt → Thương hiệu & tên miền | [docs/15-thuong-hieu-ten-mien.md](docs/15-thuong-hieu-ten-mien.md) |

### 10.3 Lưu ý an toàn khi kết nối

- Không dán API key vào chat công khai; chỉ vào ô Kết nối (key được mã hoá trong state).
- Zalo Agent MCP **không chính thức** - nên dùng số phụ; đọc cảnh báo trong UI.
- Mức **Toàn quyền** cho phép thao tác tiền / gửi tin / đăng bài - chỉ bật khi thật sự cần.
- Không chia sẻ một subscription Claude Pro cho nhiều người chạy nền 24/7 trên VPS (rủi ro khoá tài khoản).

---

## 11. Checklist người phát hành (trước khi gửi bản đóng gói)

Dùng khi bạn **đóng gói để người khác cài**:

1. [ ] Image GHCR / ZIP build từ `main` đã xanh CI.
2. [ ] README / compose trỏ đúng registry fork (`ghcr.io/duongcanhquan/javisos`).
3. [ ] Skills hệ thống nằm trong `.claude/skills/` (đủ bộ bạn muốn ship).
4. [ ] Agents / workflows chuẩn có đường nạp: Studio seed và/hoặc `deploy/caps-bundles/*.zip` + script seed.
5. [ ] **Không** đóng gói `brains/*/memory`, sources cá nhân, `.env` có secret, volume state cũ.
6. [ ] Kèm file này + [docs/huong-dan/HUONG-DAN-SU-DUNG-Javis-OS.pdf](docs/huong-dan/) (nếu có).
7. [ ] Thử sạch trên máy trống / VPS trống: cài → Models → chat một câu (đã thấy agent/workflow chuẩn) → Kết nối một dịch vụ thử.
8. [ ] Viết rõ cho người nhận: họ **tự** Models + Kết nối; không kỳ vọng sẵn Gmail/Ads của bạn.

---

## 12. Lỗi thường gặp

| Hiện tượng | Cách xử lý |
|---|---|
| Windows: `python` không nhận | Cài lại Python, tick Add to PATH, mở lại CMD, chạy lại `1-Cai-dat.bat` |
| Mac không mở `.command` | Chuột phải → Open; hoặc `chmod +x *.command` |
| Pull image fail | GHCR chưa Public / sai tên image / hết disk |
| Mở app hỏi MÃ THIẾT LẬP | `docker compose logs` hoặc `cat /data/state/.setup_token`; hoặc điền sẵn admin trong `.env` |
| Chat báo chưa có bộ não | Models chưa đăng nhập / thiếu API key |
| Studio trống năng lực | Bấm seed **Bộ …** tương ứng; đợi sync skill hệ thống |
| Mic không bật trên VPS | Chưa HTTPS - làm §7 |
| Hostinger không HTTPS | Sai / thiếu `DOMAIN_NAME` |
| Thấy Project não khác | Sai brain đang chọn, hoặc project gắn nhầm tag brain - chọn đúng não / sửa/xoá project lệch |
| Firewall Windows chặn | Mở inbound TCP 7777 (và 80/443 nếu proxy) |
| Docker Desktop chưa sẵn sàng | Mở Docker Desktop, đợi xanh, `docker compose up -d` lại |

Thêm FAQ: [docs/17-khac-phuc-su-co.md](docs/17-khac-phuc-su-co.md).

---

## 13. Bản đồ tài liệu liên quan

| File | Khi nào mở |
|---|---|
| [CAI-DAT-MAY-CA-NHAN.md](CAI-DAT-MAY-CA-NHAN.md) | Chỉ Windows/Mac double-click |
| [CAI-DAT-TRUONG.md](CAI-DAT-TRUONG.md) | Phát cho giáo viên / trường |
| [DEPLOY.md](DEPLOY.md) | VPS, HTTPS, nhiều bản trên một máy |
| [QUICKSTART.md](QUICKSTART.md) | Chạy dev từ source |
| [docs/01-bat-dau-thiet-lap.md](docs/01-bat-dau-thiet-lap.md) | Wizard lần đầu |
| [docs/09-mcp-va-so-lieu.md](docs/09-mcp-va-so-lieu.md) | Kết nối từng dịch vụ |
| [docs/15-thuong-hieu-ten-mien.md](docs/15-thuong-hieu-ten-mien.md) | Domain trong UI |
| [docs/README.md](docs/README.md) | Mục lục toàn bộ chức năng |

---

*Cập nhật theo phiên bản app trong file `VERSION`. Khi sửa hướng dẫn này, giữ nguyên quy ước: không dùng em dash; Project theo brain; skill/agent/workflow chuẩn dùng chung instance; kết nối do người dùng tự gắn.*
