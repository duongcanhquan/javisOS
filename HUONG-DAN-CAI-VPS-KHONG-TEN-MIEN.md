# Cài Javis trên VPS (cho người chưa biết kỹ thuật)

Bạn vừa thuê một **máy chủ (VPS)**. File này đi từ lúc **chưa biết kết nối thế nào** tới lúc mở được Javis trên điện thoại bằng **link HTTPS** (tên miền miễn phí, không bắt buộc mua domain).

Không cần biết lập trình. Làm đúng thứ tự, **copy lệnh rồi dán**, đừng tự gõ lại.

Tài liệu ngắn (đã biết SSH): [CAI-DAT-DON-GIAN.md](CAI-DAT-DON-GIAN.md). Kỹ thuật sâu: [DEPLOY.md](DEPLOY.md).

---

## Bạn sẽ làm 6 việc, theo đúng thứ tự này

| Bước | Việc | Xong khi nào |
|---|---|---|
| **1** | Mua / mở VPS, ghi IP + mật khẩu | Có số IP (vd `103.20.1.50`) |
| **2** | Kết nối vào máy chủ từ laptop | Cửa sổ chữ (Linux) hoặc màn hình Windows hiện ra |
| **3** | Mở cổng trên tường lửa | Nhà cung cấp cho phép cổng **22**, **7777** (sau này thêm **80**, **443**) |
| **4** | Cài Docker rồi chạy Javis | `docker compose ps` thấy chữ **Up** |
| **5** | Mở trình duyệt, tạo admin, chọn Models | Chat được một câu |
| **6** | (Khuyến nghị) Tên miền miễn phí | Vào bằng `https://…` thay vì nhớ số IP |

**Đường dễ nhất theo chỗ bạn thuê máy:**

| Bạn thuê VPS ở đâu | Làm theo mục |
|---|---|
| **Hostinger** (Linux) | [A. Hostinger, không cần gõ lệnh](#a-hostinger-không-cần-gõ-lệnh--dễ-nhất) |
| VPS Linux khác (Ubuntu) | [B. Kết nối SSH](#b-kết-nối-ssh-vào-vps-linux) rồi [C. Cài Javis Linux](#c-cài-javis-trên-vps-linux) |
| VPS / máy chủ **Windows** | [D. Kết nối RDP](#d-kết-nối-rdp-vào-vps-windows) rồi [E. Cài Javis Windows](#e-cài-javis-trên-vps-windows) |

---

## Từ điển 1 phút (đọc trước khi làm)

| Chữ bạn sẽ gặp | Nghĩa thường ngày |
|---|---|
| **VPS** | Một máy tính thuê trên internet, bật 24/7, có địa chỉ riêng |
| **IP** | “Số nhà” của máy đó, dạng `103.20.1.50`. Dùng để vào và để trỏ tên miền |
| **SSH** | Cửa sổ chữ để ra lệnh cho máy **Linux**. Laptop của bạn điều khiển VPS từ xa |
| **RDP** | “Remote Desktop”: thấy màn hình máy **Windows** từ xa, dùng chuột như máy nhà |
| **Cổng (port)** | Cửa ra vào. Javis dùng cửa **7777**. SSH dùng **22**. Website HTTPS dùng **443** |
| **Tường lửa / Firewall** | Chốt cửa. Nếu chưa mở cổng 7777 thì trình duyệt không vào được, dù Javis đã chạy |
| **Docker** | “Hộp” có sẵn Javis. Cài Docker một lần, không cần cài Python trên VPS |
| **Tên miền** | Tên dễ nhớ (`javis-tenban.duckdns.org`) thay cho số IP |
| **HTTPS** | Ổ khóa trên trình duyệt. **Mic / giọng nói chỉ chạy khi có HTTPS** (hoặc `localhost`) |
| **Terminal / PowerShell** | Ô chữ trên laptop để gõ lệnh. Không phải trang web |

---

## 0. Mua VPS thế nào (nếu chưa có)

Chọn khi thanh toán:

| Mục | Chọn |
|---|---|
| Hệ điều hành | **Ubuntu 24.04** (hoặc 22.04). Đây là **Linux**. Đừng chọn Windows trừ khi bạn chỉ quen Windows Server |
| RAM | **4 GB** chạy được; **8 GB** nếu chạy nhiều việc nền |
| Ổ | 40 GB SSD càng tốt (tối thiểu 20 GB) |
| Vị trí | Gần Việt Nam (Singapore / Việt Nam) cho mạng nhanh |

Sau khi máy “Active”, vào trang quản lý VPS của nhà cung cấp, **chép ra giấy / Notepad**:

1. **Địa chỉ IP** (IPv4)
2. **Tên đăng nhập**: thường là `root` hoặc `ubuntu`
3. **Mật khẩu** (hoặc file khóa `.pem` nếu họ gửi khóa)

Bạn **không** cài Javis trên laptop ở bước này. Laptop chỉ dùng để **điều khiển** VPS.

---

## A. Hostinger (không cần gõ lệnh) - dễ nhất

Nếu VPS là **Hostinger Linux** và trên hPanel có **Docker Manager**, làm đường này. Không cần PuTTY, không cần nhớ lệnh.

### A1. Mở đúng chỗ

1. Vào [hpanel.hostinger.com](https://hpanel.hostinger.com) trên Chrome / Edge.
2. Đăng nhập tài khoản đã mua VPS.
3. Bấm **VPS** (menu trái hoặc ô máy chủ).
4. Bấm vào **máy VPS** của bạn (không phải Hosting website).
5. Tìm nút **Docker Manager** (hoặc **Docker**).

Chưa thấy Docker Manager: máy có thể là VPS thường. Làm mục [B](#b-kết-nối-ssh-vào-vps-linux) (SSH) rồi mục [C](#c-cài-javis-trên-vps-linux).

### A2. Lấy tên miền miễn phí sẵn có của Hostinger

Hostinger cho sẵn tên dạng `srv1782015.hstgr.cloud` (số của bạn khác).

1. Ở trang VPS, tìm **Hostname** (tên máy). Ví dụ: `srv1782015.hstgr.cloud`.
2. Tên miền Javis sẽ là: `javis.` + hostname đó.  
   Ví dụ: `javis.srv1782015.hstgr.cloud`
3. **Không** cần mua domain, **không** cần vào chỗ DNS. Hostinger đã trỏ sẵn `*.hstgr.cloud`.

### A3. Deploy Javis

1. Trong Docker Manager bấm **Compose** (hoặc **Add compose**).
2. Chọn nhập bằng **URL**, dán đúng một dòng này:

```text
https://raw.githubusercontent.com/duongcanhquan/javisOS/main/docker-compose.hostinger.yml
```

3. Ô **Environment** điền 3 dòng (đổi mật khẩu):

| Ô | Gõ gì |
|---|---|
| `DOMAIN_NAME` | `javis.srvXXXX.hstgr.cloud` (đúng hostname của bạn) |
| `JAVIS_ADMIN_USER` | `admin` |
| `JAVIS_ADMIN_PASSWORD` | mật khẩu mạnh, ít nhất 8 ký tự, **nhớ ghi ra** |

4. Bấm **Deploy**. Đợi 2–5 phút (lần đầu tải image).
5. Mở Chrome: `https://javis.srvXXXX.hstgr.cloud` (đổi đúng tên bạn đặt).  
   Có ổ khóa = xong. Mic trên điện thoại dùng được.

Chưa vào được: đợi thêm 2 phút (cấp chứng chỉ SSL). Hoặc tạm mở `http://IP-VPS:7777` (chat chữ, mic bị chặn).

Tiếp: [F. Lần đầu trong app](#f-lần-đầu-trong-app---làm-ít-nhất-cho-chạy-được).

---

## B. Kết nối SSH vào VPS Linux

SSH = bạn mở một **cửa sổ chữ trên laptop**, gõ lệnh, lệnh chạy **trên VPS** (không chạy trên laptop).

### B1. Lấy IP

Vào trang quản lý VPS (Hostinger / Contabo / DigitalOcean / nhà Việt Nam…). Tìm **IP Address** / **IPv4**. Chép, ví dụ `103.20.1.50`.

### B2. Mở đúng chương trình trên laptop

**Laptop Windows 10 / 11 (cách nên dùng):**

1. Bấm phím **Windows**, gõ `powershell`, Enter (mở **Windows PowerShell**).
2. Gõ thử:

```text
ssh
```

- Thấy vài dòng chữ (`usage: ssh ...`) = máy đã có SSH. Làm B3.
- Báo `'ssh' is not recognized` = chưa có. Làm một trong hai:
  - **Cài SSH có sẵn của Windows:** Cài đặt → Ứng dụng → Tính năng tùy chọn → **OpenSSH Client** → Cài đặt. Mở PowerShell **mới**, thử lại `ssh`.
  - **Hoặc tải PuTTY:** vào https://www.putty.org → Download → `putty.exe` → chạy file đó (không cần cài). Ở ô **Host Name** dán IP, **Port** để `22`, **Connection type** = SSH, bấm **Open**.

**Laptop Mac:**

1. Mở **Spotlight** (`Cmd + Space`), gõ `Terminal`, Enter.
2. Làm B3.

**Laptop Linux:** mở Terminal, làm B3.

### B3. Lệnh kết nối (thay IP thật)

Trong PowerShell / Terminal, dán (sửa IP và user):

```bash
ssh root@103.20.1.50
```

Nếu nhà cung cấp bảo user là `ubuntu` (không phải `root`):

```bash
ssh ubuntu@103.20.1.50
```

Enter.

| Máy hỏi | Bạn làm |
|---|---|
| `Are you sure you want to continue connecting (yes/no)` | Gõ `yes` rồi Enter (chỉ lần đầu) |
| `password:` | Gõ mật khẩu VPS rồi Enter. **Không hiện dấu sao, không hiện chữ** - đó là bình thường. Gõ xong Enter |

Thấy dòng kiểu `root@srv:~#` hoặc `ubuntu@srv:~$` = **đã vào VPS**. Mọi lệnh tiếp theo gõ ở cửa sổ này.

Sai mật khẩu: thử lại. Quên mật khẩu: vào trang nhà cung cấp bấm **Reset password**, rồi kết nối lại.

### B4. Cách dán lệnh (đừng tự gõ)

1. Bôi đen khối lệnh trong hướng dẫn này → Ctrl+C (Windows) hoặc Cmd+C (Mac).
2. Bấm vào cửa sổ SSH.
3. Dán: **chuột phải** (Windows PowerShell / PuTTY) hoặc **Cmd+V** (Mac).
4. Enter.

**Không gõ** các dòng bắt đầu bằng `#` (đó là chú thích).  
**Đổi** chỗ viết `DoiMatKhauManh` / `IP_VPS` thành của bạn.

---

## C. Cài Javis trên VPS Linux

Làm **trong cửa sổ SSH** (đã vào được máy).

### C1. Cập nhật máy (một lần, vài phút)

```bash
sudo apt update && sudo apt upgrade -y
```

Hỏi gì thì Enter hoặc gõ `Y` rồi Enter.

### C2. Mở cổng trên VPS

```bash
sudo ufw allow 22/tcp
sudo ufw allow 7777/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

Hỏi `Proceed with operation` → gõ `y` rồi Enter.

**Bắt buộc thêm:** nhiều nhà còn có **Firewall trên trang web** (Security Group). Vào panel → Firewall → thêm quy tắc **TCP** các cổng **22, 7777, 80, 443** từ mọi nơi (`0.0.0.0/0` hoặc Anywhere). Chỉ làm ufw mà quên panel thì trình duyệt nhà bạn vẫn không vào được.

### C3. Cài Docker (một lần)

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker "$USER"
```

**Đăng xuất rồi vào lại** (để quyền Docker có hiệu lực):

```bash
exit
```

Rồi SSH lại đúng lệnh B3. Kiểm tra:

```bash
docker version
docker compose version
```

Thấy số phiên bản (không báo `permission denied`) là được.

### C4. Chạy Javis

```bash
mkdir -p ~/javis && cd ~/javis
curl -fsSLO https://raw.githubusercontent.com/duongcanhquan/javisOS/main/docker-compose.yml
printf 'JAVIS_ADMIN_USER=admin\nJAVIS_ADMIN_PASSWORD=DoiMatKhauManh\n' > .env
docker compose up -d
```

**Đổi `DoiMatKhauManh` trước khi dán.** Đó là mật khẩu đăng nhập Javis.

Đợi 1–3 phút lần đầu. Xem đã lên chưa:

```bash
cd ~/javis
docker compose ps
```

Cột **STATUS** có chữ **Up** là xong.

### C5. Mở trên trình duyệt laptop

Trong Chrome / Edge trên **máy nhà** (không phải trên VPS), gõ:

```text
http://103.20.1.50:7777
```

Đổi thành IP của bạn. Có dấu hai chấm và `7777`, không có `www`.

Tiếp: [F. Lần đầu trong app](#f-lần-đầu-trong-app---làm-ít-nhất-cho-chạy-được).  
Muốn link đẹp + mic: [G. Tên miền miễn phí](#g-tên-miền-miễn-phí-để-vào-cho-dễ).

### Lệnh dùng sau này (Linux)

Luôn `cd ~/javis` trước:

```bash
cd ~/javis
docker compose logs -f          # xem nhật ký (Ctrl+C để thoát, không tắt Javis)
docker compose restart          # khởi động lại
docker compose pull && docker compose up -d   # cập nhật bản mới
docker compose down             # tắt (dữ liệu trong volume vẫn còn)
```

---

## D. Kết nối RDP vào VPS Windows

RDP = bạn **thấy nguyên màn hình** máy chủ Windows, dùng chuột như ngồi trước máy đó.

### D1. Bật Remote Desktop trên VPS (nếu nhà cung cấp chưa bật)

Khi tạo VPS Windows, họ thường gửi **IP + Administrator + mật khẩu**. Nhiều chỗ đã bật RDP sẵn (cổng **3389**).

### D2. Từ laptop Windows

1. Phím **Windows**, gõ `Remote Desktop` hoặc `Kết nối Máy tính Từ xa` / `mstsc`, Enter.
2. Ô **Máy tính** / Computer: dán **IP VPS**.
3. **Kết nối**.
4. User: `Administrator` (hoặc user họ gửi). Mật khẩu: mật khẩu VPS.
5. Cảnh báo chứng chỉ: **Yes / Connect**.

Thấy hình nền Windows Server / Windows 10 = đã vào. Mọi cài đặt Javis làm **trên màn hình này**.

### D3. Từ laptop Mac

1. Cài app **Windows App** (trước đây là Microsoft Remote Desktop) trên App Store (miễn phí).
2. Dấu **+** → Add PC → PC name = IP VPS.
3. User account = `Administrator` + mật khẩu.
4. Double-click máy vừa thêm.

### D4. Không vào được?

- Panel nhà cung cấp: mở firewall **TCP 3389**.
- Thử lại mật khẩu; Reset password trên panel.
- Công ty bạn chặn RDP: dùng mạng nhà, hoặc hỏi nhà cung cấp **console / VNC** (màn hình trên web).

---

## E. Cài Javis trên VPS Windows

Làm **trên màn hình RDP** (máy chủ), không phải trên laptop nhà.

### E1. Cách nên dùng: Docker Desktop

1. Trên VPS, mở Edge / Chrome → https://www.docker.com/products/docker-desktop/
2. Tải bản Windows, cài. Hỏi **WSL2** thì **bật / Install**.
3. Máy có thể **khởi động lại**. RDP vào lại.
4. Mở **Docker Desktop**, đợi con cá voi **xanh** (Engine running). Lần đầu 5–15 phút.
5. Mở **PowerShell** trên VPS (Windows, gõ `powershell`).
6. Dán (đổi mật khẩu):

```powershell
mkdir $HOME\javis; cd $HOME\javis
Invoke-WebRequest -Uri https://raw.githubusercontent.com/duongcanhquan/javisOS/main/docker-compose.yml -OutFile docker-compose.yml
@"
JAVIS_ADMIN_USER=admin
JAVIS_ADMIN_PASSWORD=DoiMatKhauManh
"@ | Set-Content -Encoding ascii .env
docker compose up -d
```

7. Mở cổng Windows:

- Phím Windows, gõ `Windows Defender Firewall` → **Advanced settings** → **Inbound Rules** → **New Rule**.
- **Port** → TCP → **7777** → Allow → đặt tên `Javis 7777`.
- Làm thêm quy tắc **80** và **443** nếu dùng tên miền HTTPS.

8. Panel nhà cung cấp: mở TCP **7777** (và **80**, **443**, **3389**).

9. Trên **laptop nhà**, Chrome: `http://IP-MAY:7777`.

### E2. Không dùng Docker (giống máy nhà, chạy 24/7)

Chỉ khi Docker Desktop cài mãi không xong.

1. Cài **Python 3.11 hoặc 3.12** từ https://www.python.org/downloads/ - **tick** *Add python.exe to PATH*. Không cài bản Microsoft Store.
2. (Nên) Cài **Node.js 22 LTS** từ https://nodejs.org/
3. Tải ZIP: https://github.com/duongcanhquan/javisOS → **Code → Download ZIP** → giải nén ra `C:\Javis` (không Desktop OneDrive).
4. Double-click **`1-Cai-dat.bat`**. SmartScreen: **More info → Run anyway**.
5. Mở file `.env` trong thư mục Javis bằng Notepad, thêm / sửa:

```text
JAVIS_HOST=0.0.0.0
JAVIS_ADMIN_USER=admin
JAVIS_ADMIN_PASSWORD=DoiMatKhauManh
```

6. Chạy **`2-Bat-Javis.bat`**. Muốn tự bật khi Windows đăng nhập: `javis-autostart.bat install`.
7. Mở firewall TCP **7777** như E1 bước 7.
8. Chrome máy nhà: `http://IP:7777`.

Javis **bắt buộc đăng nhập** khi mở ra internet. Đặt mật khẩu mạnh.

---

## F. Lần đầu trong app - làm ít nhất cho chạy được

Đừng cài Gmail / Zalo / Ads ngay. Chỉ 3 việc:

### 1) Tạo tài khoản admin

- User: `admin` (hoặc bạn đã ghi trong `.env`).
- Mật khẩu: đúng mật khẩu đã đặt, **ít nhất 8 ký tự**.
- Nếu màn hình hỏi **MÃ THIẾT LẬP** (bạn quên ghi mật khẩu vào `.env`):

**Linux SSH:**

```bash
cd ~/javis
docker compose exec javis cat /data/state/.setup_token
```

**Windows PowerShell** (thư mục `javis`):

```powershell
docker compose exec javis cat /data/state/.setup_token
```

Copy chuỗi → dán vào ô mã → tạo admin.

### 2) Chọn một bộ não (Models)

Menu trái → nhóm **Kết nối** → **Models**. Chọn **một** đường, đừng chọn hết:

| Bạn đã có sẵn | Bấm |
|---|---|
| ChatGPT Plus / Pro | ChatGPT (Codex) → đăng nhập |
| Claude Pro / Max | Claude Code → đăng nhập (link + mã) |
| Tài khoản Google muốn dùng Antigravity | Thẻ Antigravity - **cài tay** theo chữ trên thẻ (`agy` không tự cài) |
| Chỉ có thẻ tín dụng, chưa có gói chat | **OpenRouter** (hoặc OpenAI / Gemini): tạo key trên trang họ, dán vào Javis |

Xong: chọn **Main Model**. Chat thử: `xin chào`.

**Chưa chọn Models thì mở được app nhưng chat sẽ lỗi.** Đó không phải lỗi cài VPS.

### 3) Xong. Dùng vài ngày đã

Agent / skill chuẩn **đã có sẵn**. Không cần bấm Studio.

Khi quen: Kết nối Gmail / Zalo; rồi làm [G](#g-tên-miền-miễn-phí-để-vào-cho-dễ) nếu vẫn đang vào bằng `http://IP:7777`.

---

## G. Tên miền miễn phí để vào cho dễ

`http://103.20.1.50:7777` khó nhớ và **không bật được mic** trên điện thoại. Lấy một **tên + HTTPS** (miễn phí) theo bảng:

| Cách | Link bạn nhận | Phù hợp | Cố định? |
|---|---|---|---|
| **1. Hostinger `hstgr.cloud`** | `https://javis.srvXXXX.hstgr.cloud` | VPS Hostinger | Có |
| **2. DuckDNS** | `https://tenban.duckdns.org` | Mọi VPS Linux/Windows Docker | Có |
| **3. Cloudflare Tunnel** | `https://….trycloudflare.com` | Muốn HTTPS ngay, chưa sửa DNS | **Đổi** mỗi lần restart (trừ khi làm named tunnel) |
| **4. Mua domain sau** | `https://javis.tencuaban.com` | Khi đã có tiền / thương hiệu | Có |

**Người mới:** Hostinger → cách 1. VPS khác → cách 2 (DuckDNS). Cần mic gấp trong 2 phút → cách 3.

### G1. Hostinger (nhắc lại)

Làm mục [A](#a-hostinger-không-cần-gõ-lệnh--dễ-nhất). Chỉ cần `DOMAIN_NAME=javis.<hostname>.hstgr.cloud`.

### G2. DuckDNS (miễn phí, mọi nhà VPS) - từng nút

DuckDNS cho bạn tên dạng `tenban.duckdns.org`, trỏ về IP VPS. Không mất tiền.

**Trên laptop (trình duyệt):**

1. Mở https://www.duckdns.org
2. Bấm đăng nhập bằng **Google** (hoặc GitHub). Cho phép.
3. Ô tạo subdomain: gõ một tên **không dấu, không cách**, ví dụ `javis-tenban`.
4. Bấm **add domain**.
5. Ô IP: dán **IPv4 của VPS**. Bấm **update ip**.
6. Thấy dấu tick / `IP updated` = DNS đã trỏ. Tên đầy đủ: `javis-tenban.duckdns.org`.

**Trên VPS (đã chạy Javis bằng Docker):**

Mở cổng **80** và **443** (ufw + panel), rồi:

**Linux:**

```bash
cd ~/javis
curl -fsSLO https://raw.githubusercontent.com/duongcanhquan/javisOS/main/docker-compose.https.yml
docker compose -f docker-compose.yml -f docker-compose.https.yml up -d
```

**Windows PowerShell** (thư mục `javis`):

```powershell
cd $HOME\javis
Invoke-WebRequest -Uri https://raw.githubusercontent.com/duongcanhquan/javisOS/main/docker-compose.https.yml -OutFile docker-compose.https.yml
docker compose -f docker-compose.yml -f docker-compose.https.yml up -d
```

**Trong Javis** (vào bằng `http://IP:7777` lần này):

1. **Cài đặt → Giọng nói, thương hiệu & truy cập → TÊN MIỀN & SSL**.
2. Gõ `javis-tenban.duckdns.org` (không gõ `https://`).
3. **Lưu & kiểm tra**. Đợi badge **DNS: đã trỏ đúng**.
4. **Bật SSL**. Đợi khoảng 10–30 giây.
5. Mở `https://javis-tenban.duckdns.org` (không còn `:7777`).

Chi tiết nút / lỗi badge: [docs/15-thuong-hieu-ten-mien.md](docs/15-thuong-hieu-ten-mien.md).

**Không làm G2 trên Hostinger Docker Manager** (Traefik đã chiếm cổng 80/443). Hostinger dùng cách G1.

### G3. Cloudflare Tunnel (HTTPS ngay, không cần DuckDNS)

Vẫn trong thư mục `javis` trên VPS:

**Linux:**

```bash
cd ~/javis
docker compose --profile tunnel up -d
docker compose logs tunnel | grep trycloudflare
```

**Windows:**

```powershell
cd $HOME\javis
docker compose --profile tunnel up -d
docker compose logs tunnel
```

Tìm dòng có `https://….trycloudflare.com` → mở link đó. Mic chạy được.

- Link **đổi** khi bạn restart tunnel.
- Đặt mật khẩu admin **trước** khi gửi link cho người khác.
- Muốn link cố định: tài khoản Cloudflare miễn phí + *named tunnel* (`TUNNEL_TOKEN`) - xem [DEPLOY.md](DEPLOY.md).

### G4. Sau này mua tên miền riêng

1. Mua domain ở nhà bất kỳ (vd `.com`).
2. Vào chỗ **DNS** của họ, tạo bản ghi:

| Loại | Tên (Name) | Giá trị (Value) |
|---|---|---|
| **A** | `javis` | IP VPS của bạn |

3. Đợi vài phút đến vài giờ.
4. **Hostinger:** đổi `DOMAIN_NAME=javis.tencuaban.com` → **Redeploy**.
5. **VPS tự quản:** như G2, nhưng gõ `javis.tencuaban.com` trong Cài đặt rồi **Bật SSL**.

---

## H. Chỉ mình dùng từ laptop (không mở 7777 ra internet)

An toàn hơn nếu bạn chưa đặt mật khẩu chắc. Trên **laptop** (không phải VPS):

```bash
ssh -L 7777:localhost:7777 root@IP_VPS
```

Giữ cửa sổ SSH mở. Chrome laptop: `http://localhost:7777`. Mic chạy (vì localhost).

Windows: cùng lệnh trong PowerShell (đã có `ssh`).

---

## I. Checklist sau khi vào app

1. Đăng nhập **admin**, mật khẩu mạnh.
2. **Models** → một bộ não → chat một câu.
3. Cần mic / vào từ điện thoại: làm mục **G** (tên miền miễn phí hoặc tunnel).
4. Gmail / Zalo: làm sau, trong **Kết nối**. Không có sẵn trong bản cài.

---

## J. Lỗi hay gặp

| Hiện tượng | Làm gì |
|---|---|
| `ssh` không có trên Windows | Cài **OpenSSH Client** (Tính năng tùy chọn) hoặc dùng **PuTTY** |
| Hỏi password nhưng gõ không thấy chữ | Bình thường. Gõ xong Enter |
| `Permission denied` khi SSH | Sai user hoặc sai mật khẩu; thử `ubuntu@` thay `root@`; Reset password trên panel |
| Trình duyệt không vào `IP:7777` | Javis chưa Up (`docker compose ps`); **firewall panel + ufw** chưa mở **7777**; gõ thiếu `:7777` |
| Docker `permission denied` | Quên `exit` rồi SSH lại sau khi `usermod` |
| Hỏi MÃ THIẾT LẬP | `docker compose exec javis cat /data/state/.setup_token` |
| Pull image fail | Hết đĩa; hoặc image GHCR chưa Public |
| Mic bị chặn | Đang dùng `http://IP` - làm mục G |
| Tunnel không ra URL | `docker compose --profile tunnel up -d`, đợi 30 giây, xem `logs tunnel` |
| Windows: Docker đỏ | Mở Docker Desktop, đợi xanh; bật Virtualization trong BIOS; cài WSL2 |
| Hostinger không có ổ khóa HTTPS | Sai `DOMAIN_NAME` (phải đúng `javis.<hostname>.hstgr.cloud`) |
| DuckDNS badge “chưa trỏ” | Ô IP trên duckdns.org phải đúng IPv4 VPS; đợi 2–10 phút, bấm **Kiểm tra lại** |
| Chat lỗi dù mở được app | Chưa chọn bộ não ở **Models** |

---

*Image mặc định: `ghcr.io/duongcanhquan/javisos:latest`. Không gửi kèm thư mục `brains/` cá nhân khi hướng dẫn người khác.*
