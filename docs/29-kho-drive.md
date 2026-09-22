# Kho Drive — tri thức Google Drive trên VPS

***Tiếng Việt** · [English](en/29-drive-library.md)*

Đồng bộ **một thư mục** Google Drive vào Second Brain. Không cần thẻ Google Workspace.

> Trang **Bộ não → Kho Drive** khác menu **Kết nối → Google**. Ở đây chỉ kéo file thư mục vào bộ não.

## Làm lần đầu (3 bước trên trang Kho Drive)

### Bước 1 - Kết nối Google

**Nếu mở VMOS trên máy bạn (localhost):**  
1. Bấm **Kết nối Google Drive**.  
2. Allow trên Google.  
3. Quay lại trang - trạng thái chuyển sang đã kết nối.

**Nếu VMOS chạy trên VPS:**  
1. Chọn **Tôi dùng Mac** hoặc **Tôi dùng Windows**.  
2. Bấm **Bắt đầu kết nối**.  
3. **Mac:** Sao chép lệnh → dán vào Terminal → Enter → Allow Google.  
4. **Windows:** Tải `.bat` → double-click → Allow Google.  
5. Quay lại trang Kho Drive (chờ vài giây).

### Bước 2 - Tạo kho

1. Đặt tên kho (ví dụ: Giáo trình Marketing).  
2. Trên Drive: mở thư mục → Sao chép liên kết (hoặc copy URL thanh địa chỉ).  
3. Dán link vào ô → **Tạo và đồng bộ**.

### Bước 3 - Dùng hàng ngày

1. Sửa file trên Google Drive.  
2. Trang Kho Drive → **Đồng bộ lại**.  
3. Tệp tin → `sources/drive/…` hoặc Dự án chat của kho.  
4. Bảo Javis đọc / ingest từng file quan trọng (không nuốt cả kho một lần).

Config rclone lưu tại `/data/state/rclone.conf` (Docker).

## Kiến trúc (tóm tắt)

| Lớp | Đường | Vai trò |
|---|---|---|
| Drive | Thư mục Google | Bản gốc |
| Corpus | `JAVIS_STATE_DIR/drive-corpus/…` | File sau rclone |
| Sources | `<brain>/sources/drive/<slug>/` | Cho Javis đọc |
| Dự án chat | Tự tạo | Hỏi đáp / ingest |

## API

- `GET /drive-projects/status` · `POST /drive-projects` · `…/{id}/sync` · `…/delete`
- Kết nối: `…/rclone/authorize/*` (localhost) · `…/rclone/pair/*` (VPS)
