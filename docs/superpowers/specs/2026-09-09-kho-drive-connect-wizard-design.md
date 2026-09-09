# Kho Drive — wizard kết nối Google trong dashboard

**Ngày:** 2026-09-09  
**Trạng thái:** approved (user: làm theo hướng A)

## Mục tiêu

Người dùng chỉ thao tác trên trang **Bộ não → Kho Drive**: kết nối Google → dán link thư mục → tạo & đồng bộ. Không cần Terminal (trừ trường hợp VPS lấy token lần đầu).

## Luồng UI

1. **Trạng thái rclone** — đã cài? đã có remote `gdrive:`?
2. **Kết nối Google** (khi chưa có remote):
   - **Cùng máy (localhost):** bấm → mở link Google → Javis poll tới khi xong
   - **VPS / máy khác:** dán token JSON *hoặc* upload file `rclone.conf`
3. **Tạo kho:** tên + link/ID thư mục Drive (tự parse URL) → tạo + sync ngay  
   Ẩn ô rclone remote (mặc định `gdrive:`); hiện trong “Nâng cao”.

## API

- `POST /drive-projects/rclone/authorize/start` → `{ok, session_id, auth_url}`
- `GET /drive-projects/rclone/authorize/poll?session=` → `{ok, status: pending|done|error, ...}`
- `POST /drive-projects/rclone/connect` body `{token?}` hoặc multipart conf
- `POST /drive-projects/rclone/disconnect` (tuỳ chọn)
- `create`: chấp nhận full Drive URL, normalize folder id

## Ngoài phạm vi

- Service Account JSON
- OAuth client riêng theo domain (Google Cloud)
