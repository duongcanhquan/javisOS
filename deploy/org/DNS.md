# Setup DNS cho Javis tổ chức (vietmycollege.com)

IP VPS Javis: **`14.225.205.248`** (máy `javisos-hgsg`).

Làm trên **đúng nơi đang giữ zone** `vietmycollege.com` (Cloudflare, cPanel, internet.vn, v.v.). Không cần đổi nameserver nếu A record `javis` đã trỏ đúng IP này.

## Cần những bản ghi nào

| Loại | Tên (Host) | Giá trị | Việc |
|---|---|---|---|
| A | `javis` | `14.225.205.248` | **Giữ** - sau cutover đây là **manager** |
| A | `javis-quan` | `14.225.205.248` | **Thêm** - Javis cá nhân (não hiện tại) |
| A | `*` (wildcard) | `14.225.205.248` | **Nên thêm** - `javis-ten.vietmycollege.com` tự ra, không khai từng người |

Cùng một IP là đúng: Caddy trên VPS đọc **tên host** rồi lái vào đúng container.

TTL lúc cắt: **300** (5 phút). Ổn rồi có thể để 3600.

Không tạo CNAME `javis-quan` → `javis` nếu panel báo cấm CNAME trùng A. Dùng A như bảng trên.

## Cloudflare

1. Đăng nhập [Cloudflare](https://dash.cloudflare.com) → domain `vietmycollege.com` → **DNS** → **Records**.
2. Tìm `javis` loại A. Phải là `14.225.205.248`. Sai thì sửa (Proxy: DNS only **màu xám** lúc cutover cho dễ, hoặc giữ Proxied nếu đã chạy ổn với SSL Full).
3. **Add record**: Type A, Name `javis-quan`, IPv4 `14.225.205.248`, Proxy tùy: lúc mới cắt nên **DNS only**.
4. **Add record**: Type A, Name `*`, IPv4 `14.225.205.248`, DNS only.
5. Save. Đợi 1-5 phút.

SSL/TLS trên Cloudflare (nếu đang Proxied cam): **Full (strict)** sau khi VPS đã có chứng chỉ Let's Encrypt. **Flexible** (HTTPS tới CF, HTTP tới VPS) dễ lỗi cookie Secure - tránh.

## cPanel / DirectAdmin / nhà đăng ký

1. Zone Editor / DNS Management của `vietmycollege.com`.
2. Giữ A `javis`.
3. Add A: host `javis-quan` → `14.225.205.248`.
4. Add A: host `*` → `14.225.205.248` (một số panel ghi `*.vietmycollege.com`).
5. Nếu có A `*` cũ trỏ chỗ khác: **đừng ghi đè** nếu trường đang dùng `*.vietmycollege.com` cho mail/web khác. Khi đó chỉ thêm từng `javis-<slug>`, không dùng wildcard.

## Kiểm tra trước khi cutover

Trên máy bạn:

```bash
dig +short javis.vietmycollege.com A
dig +short javis-quan.vietmycollege.com A
dig +short foo.vietmycollege.com A
```

Cả `javis` và `javis-quan` phải ra `14.225.205.248`.  
`foo` ra cùng IP nếu đã có wildcard.

Windows (PowerShell): `Resolve-DnsName javis-quan.vietmycollege.com`.

`javis-quan` chưa mở HTTPS được là bình thường: app còn đang gắn tên cũ, chưa bật proxy. DNS chỉ cần **đúng IP**.

## HTTPS sau cutover

Không mua cert tay. `javis-proxy` (Caddy) xin Let's Encrypt khi **lần đầu** mở:

- `https://javis-quan.vietmycollege.com`
- `https://javis.vietmycollege.com` (manager)

Cổng **80 và 443** trên VPS phải mở (đã mở nếu `javis` đang có HTTPS).

Nếu Cloudflare Proxy cam bật: origin phải HTTPS, mode Full (strict), hoặc tạm DNS only đến khi Caddy cấp xong cert rồi mới bật proxy.

## Javis con mới

Có wildcard: manager tạo `javis-lan.vietmycollege.com` là xong DNS.

Không wildcard: mỗi người thêm một A `javis-<slug>` → `14.225.205.248` rồi mới bấm tạo trên manager.

## Không làm

- Không trỏ `javis-quan` sang IP máy cũ `165.101.46.238` (đã xóa Javis).
- Không trỏ một subdomain Javis sang IP khác rồi chờ Caddy trên máy này cấp cert (sẽ fail).
- Không xóa A `javis` trước khi manager đã sống trên đúng IP này.
