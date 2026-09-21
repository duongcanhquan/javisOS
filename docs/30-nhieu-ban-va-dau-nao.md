# Nhiều bản Javis trên một VPS & đấu nối bộ não

***Tiếng Việt***

Khi một VPS chạy **nhiều bản Javis** (mỗi người một subdomain), mỗi bản là một máy độc lập: brain, mật khẩu admin, đăng nhập Claude / ChatGPT / Antigravity **không tự dùng chung**. Tài liệu này hướng dẫn thao tác thường gặp cho **người dùng từng tenant** và **người quản trị (manager)**.

Xem thêm: [Models & engine](10-models-va-engine.md) · [Tab Code / Terminal](27-tab-code-terminal.md) · [DEPLOY - nhiều bản](../DEPLOY.md#nhiều-bản-javis-trên-cùng-một-vps).

---

## 1. Bạn đang dùng bản nào?

| Vai trò | Ví dụ domain | Việc chính |
|---|---|---|
| **Tenant** (người dùng) | `vmos-hanh…`, `vmos-maihuong…` | Đăng nhập admin riêng → đấu **não** của mình → làm việc |
| **Manager** (bản gốc chuẩn) | `javis.vietmycollege.com` | Soạn skill / agent / workflow chuẩn → **Đồng bộ** xuống tenant |
| **Quan / admin kỹ thuật** | `vmos-quan…` | Bản dữ liệu đầy đủ; thường dùng chung auth với manager |

Skill / agent / workflow chuẩn từ manager **không** tự nhảy sang tenant. Phải bấm đồng bộ (mục 4).

---

## 2. Lần đầu trên tenant: đấu nối bộ não

Mở **Kết nối → Models**. Chọn **một** bộ não chính (Main Model). Mỗi loại cần bước riêng **một lần** trên **đúng bản** bạn đang mở (đúng subdomain).

### 2.1. Antigravity CLI (Google - lệnh `agy`)

1. Mở nhóm **Code → Terminal** trong dashboard (hoặc SSH vào container user `javis`).
2. Cài (chỉ khi chưa có lệnh `agy`):

```bash
curl -fsSL https://antigravity.google/cli/install.sh | bash
```

3. Nếu gõ `agy` báo `command not found` (session cũ chưa nạp PATH):

```bash
hash -r
export PATH="$HOME/.local/bin:$PATH"
# hoặc dùng đường đầy đủ:
~/.local/bin/agy
```

Trên nhiều VPS đã gắn sẵn symlink `/usr/local/bin/agy` - mở **terminal mới** rồi gõ `agy` là đủ.

4. Đăng nhập Google:

```bash
agy
```

Làm 3 bước trên thẻ Models: mở link → đăng nhập Google → trình duyệt báo lỗi `localhost` (đúng) → **copy cả URL** trên thanh địa chỉ → dán vào terminal → Enter.

5. Về **Models** → **Kiểm tra lại** trên thẻ Antigravity → chọn Main Model.

> Dòng `ERROR: logging before google.Init` lúc cài thường chỉ là log ồn của installer, không phải lỗi cài.

### 2.2. Claude Code (gói Claude)

Trong Terminal:

```bash
claude auth login --claudeai
```

Làm theo link / mã. Về **Models → Kiểm tra lại**.

### 2.3. ChatGPT / Codex

```bash
codex login
```

Làm theo hướng dẫn. Về **Models → Kiểm tra lại**.

### 2.4. API key (OpenRouter, OpenAI, Gemini, …)

Không cần CLI: vào **Models** → thẻ nhà cung cấp → dán key → Lưu → chọn Main Model.

---

## 3. Cái gì dùng chung, cái gì riêng?

| Mục | Chung giữa các tenant? |
|---|---|
| Phần mềm / image Javis | Cùng loại image; mỗi container cập nhật riêng |
| Skill / agent / workflow **chuẩn** từ manager | Chỉ sau khi **Đồng bộ template** |
| Memory, wiki, hội thoại, brain riêng | **Riêng** từng tenant |
| Đăng nhập Claude / Codex / Antigravity | **Riêng** từng tenant (trừ khi admin cố ý gắn chung volume) |
| Tài khoản admin web | **Riêng** từng `.env` / lần setup |

**Không** kỳ vọng: “quan đã login Antigravity thì maihuong cũng vào được”. Mỗi subdomain phải đấu não một lần (trừ manager đã được admin copy auth cố ý).

---

## 4. Manager: thêm skill rồi đẩy xuống mọi tenant

1. Đăng nhập bản **manager**.
2. Thêm / sửa skill, agent, workflow trên brain **Brain Default**.
3. Đồng bộ bằng một trong hai cách:
   - **Tổng quan** → khối **Manager — đồng bộ tenant** → **Xem trước** / **Đồng bộ ngay**
   - **Cài đặt** → nhóm **Đồng bộ xuống tenant** → cùng hai nút
4. Trên VPS (ops):

```bash
python3 /root/javis-ops-sync/scripts/sync_manager_template.py --sync
# hoặc từ thư mục repo:
python3 scripts/sync_manager_template.py --sync
```

**Chính sách sync:** file mới / bản tenant chưa sửa → cập nhật; tenant đã sửa file → **giữ nguyên**; không xóa file trên tenant khi manager xóa; không đụng brain riêng (`APC.HN`, …) - chỉ **Brain Default**.

**Function / tính năng mới trong code** (không phải skill): cần **deploy image** mới cho từng container - không đi qua nút Đồng bộ.

---

## 5. Checklist nhanh khi “não không chạy”

| Triệu chứng | Việc cần làm |
|---|---|
| `agy: command not found` | `export PATH="$HOME/.local/bin:$PATH"` hoặc mở terminal mới; kiểm tra `ls ~/.local/bin/agy` |
| Antigravity chưa kết nối | Chạy `agy` đăng nhập Google; Models → Kiểm tra lại |
| Claude / Codex chưa kết nối | `claude auth login` / `codex login` trên **đúng** tenant |
| Chat được nhưng thiếu skill mới | Nhờ manager **Đồng bộ template**; F5 / Ctrl+Shift+R |
| Sai subdomain | Kiểm tra URL: mỗi người một `vmos-…` riêng |

---

## 6. Gợi ý cho người phát hành / admin VPS

- Tạo tenant mới → gửi link subdomain + mật khẩu admin (hoặc hướng dẫn setup) + **link tài liệu này**.
- Sau `compose up`, chạy sync template một lần từ manager.
- Có thể pre-install binary `agy` vào `/usr/local/bin` trên mọi container; **đăng nhập Google vẫn do từng user**.
- Manager dùng chung Claude/Codex với bản kỹ thuật: xem `docker-compose.manager-auth.yml` trong [DEPLOY.md](../DEPLOY.md).

---

## Liên kết

- [01 - Bắt đầu & thiết lập](01-bat-dau-thiet-lap.md)
- [10 - Models & engine](10-models-va-engine.md)
- [27 - Tab Code / Terminal](27-tab-code-terminal.md)
- [17 - Khắc phục sự cố](17-khac-phuc-su-co.md)
- [Hướng dẫn đóng gói](../HUONG-DAN-CAI-DAT-VA-SU-DUNG.md)
