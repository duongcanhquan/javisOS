# Pháp chế cá nhân trên Javis

***Tiếng Việt** · [English](en/28-personal-legal-counsel.md)*

Mục tiêu: Javis đóng vai **pháp chế nội bộ** — tham chiếu nghị định, thông tư, luật đã lưu
trong kho của bạn khi hỏi hoặc khi chạy dự án. **Không** thay thế luật sư.

## Kiến trúc 3 lớp

| Lớp | Vai trò |
|---|---|
| **Google Drive** `Phap-che/{Linh-vuc}/{Ten}/` | Bản gốc PDF/DOCX, version, chia sẻ |
| **Brain** `sources/phap-che/` → **wiki** | Text đã extract + tri thức đã chắt, `[[cite]]` |
| **RAG sidecar** (tuỳ chọn) | Index cả folder PDF khi kho lớn; tool `phap_che_search` gọi thêm |

**Không** nhồi toàn bộ luật vào `memory/MEMORY.md`.

```
Drive PDF ──rclone──► corpus VPS ──► RAG-Anything (optional)
                │
                └──extract──► sources/phap-che/*.md ──INGEST──► wiki
                                                              │
                                              phap_che_search ┘
                                              skill phap-che / agent Pháp chế
```

## Phase A — Dùng ngay (không cần RAG)

1. Tạo trên Drive: `Phap-che/Lao-dong/`, `Phap-che/Thue/`, …
2. Extract văn bản quan trọng → `sources/phap-che/<linh-vuc>/YYYY-so-hieu-ten.md`
   (README tự seed trong brain khi scaffold).
3. Chat: ingest source đó (skill hệ thống **ingest-source**).
4. Bật skill **phap-che** (hệ thống) hoặc tạo agent:
   - Trang **Workflows / Agents** → hoặc API `POST /studio/seed-phap-che`.
5. Project: pin brief + các `.md` luật liên quan (pin **không** nhận PDF).

Disclaimer: mọi câu trả lời chỉ tham khảo nội bộ.

## Phase B — RAG folder / sidecar

1. Cài [rclone](https://rclone.org/), remote Google Drive.
2. Chạy `./scripts/sync-phap-che-drive.sh` (biến `RCLONE_REMOTE`, `PHAP_CHE_SYNC_DIR`).
3. Chạy RAG-Anything / LightRAG index thư mục sync (xem [RAG-Anything](https://github.com/HKUDS/RAG-Anything)).
4. Expose HTTP `POST /retrieve` JSON `{"query","top_k"}` → `{"results":[{"path","text","score"}]}`.
5. Đặt env:

```bash
JAVIS_PHAP_CHE_RAG_URL=http://127.0.0.1:8001
```

Stub minh họa hợp đồng API (chỉ đọc `.md`/`.txt`, không OCR PDF):
`scripts/phap_che_rag_sidecar_example.py`.

6. Plugin bundled **phap-che** cung cấp tool:
   - `phap_che_search` — local md + sidecar
   - `phap_che_status` — đã cấu hình RAG chưa

API debug (cần đăng nhập): `GET /phap-che/status`, `POST /phap-che/search`.

## Phase C — So sánh & snapshot web

- Skill **so-sanh-van-ban-phap-ly**: bảng Điều A vs B, xung đột, khuyến nghị; có thể lưu
  `wiki/.../so-sanh-....md`.
- Skill **snapshot-van-ban-web**: chụp văn bản công khai → `sources/phap-che/...md` (có ngày)
  rồi ingest (không phụ thuộc URL sống).

## Liên quan

- [13 - Second Brain](13-second-brain-bo-nho-wiki.md)
- [06 - Skills](06-skills.md)
- [20 - Plugins](20-plugins.md)
- [16 - Cấu hình .env](16-cau-hinh-env.md)
