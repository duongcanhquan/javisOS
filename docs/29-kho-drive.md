# Kho Drive — tri thức Google Drive trên VPS

***Tiếng Việt** · [English](en/29-drive-library.md)*

Đồng bộ một thư mục Google Drive vào Second Brain bằng **rclone**, rồi làm việc như một **Dự án chat**: hỏi, ingest-source, viết skill. Không cần thẻ Google Workspace (OAuth browser trên máy Javis).

## Kiến trúc

| Lớp | Đường dẫn | Vai trò |
|---|---|---|
| Drive | Folder trên Google Drive | Bản gốc, chia sẻ |
| Corpus | `JAVIS_STATE_DIR/drive-corpus/<brain>/<slug>/` | File nhị phân sau `rclone sync` (không vào git brain) |
| Sources | `<brain>/sources/drive/<slug>/` | `.md` mirror / stub PDF để Javis đọc |
| Dự án chat | Tự tạo khi lập kho | Ghim README + hướng dẫn dùng kho |

```
Google Drive ──rclone sync──► corpus (STATE)
                                 │
                                 └── mirror text / stub PDF ──► sources/drive/<slug>/
                                                              │
                                              Dự án chat (pin README)
                                              ingest-source → wiki → skill
```

## Setup một lần trên VPS

1. Image Javis từ 0.55.154 có sẵn binary `rclone` trong container.
2. Cấu hình remote **một lần** (token OAuth lưu trên volume state hoặc home trong container):

```bash
# Ví dụ vào container Javis
docker exec -it javis bash -lc 'RCLONE_CONFIG=/data/state/rclone.conf rclone config'
# tạo remote tên gdrive (Full Drive access)
# Config lưu tại /data/state/rclone.conf (volume STATE, sống qua update)
```

Hoặc trên host: `bash scripts/setup-rclone-drive-vps.sh` rồi mount `~/.config/rclone` vào container (xem docker-compose).

3. Lấy **Folder ID** từ URL Drive: `https://drive.google.com/drive/folders/FOLDER_ID`.
4. Dashboard: **Bộ não → Kho Drive** → tên + Folder ID → **Tạo kho** → **Đồng bộ ngay**.

## Dùng hằng ngày

1. Cập nhật file trên Drive.
2. Trang Kho Drive → **Đồng bộ ngay**.
3. Mở Dự án chat «Kho Drive · …» (hoặc Tệp tin → `sources/drive/<slug>/`).
4. Bảo Javis: *ingest source `sources/drive/<slug>/….md` rồi viết skill …*.

**Không** mass-ingest cả kho một lần. Chọn file quan trọng.

## API

- `GET /drive-projects?brain=…` / `GET /drive-projects/status`
- `POST /drive-projects` JSON `{name, drive_folder_id, rclone_remote?, brain?}`
- `POST /drive-projects/{id}/sync`
- `POST /drive-projects/{id}/update` · `…/delete`

## Khác pháp chế

[Pháp chế cá nhân](28-phap-che-ca-nhan.md) dùng cùng ý rclone nhưng folder cố định + agent Pháp chế. Kho Drive là **nhiều kho tùy ý**, UI dashboard, gắn Dự án chat chung.
