# OpenMAIC trên VPS (cùng máy với Javis)

## Mục tiêu

- Classroom live — **dùng qua Javis** (Việc → Bài giảng → Lớp học → **Tạo lớp OpenMAIC**).
- Không bắt giảng viên mở domain OpenMAIC hay gõ access code / API key.
- **TTS mặc định:** Edge-TTS tiếng Việt (Hoài My / Nam Minh) qua Javis.
- Domain `openmaic.vietmycollege.com` chỉ để iframe + debug.

## Giới hạn thật

| Hạng mục | Trên VPS CPU? |
|----------|----------------|
| Generate classroom | Cần **Gemini API key** trên server (`.env.local`) |
| Giọng đọc tiếng Việt chuẩn | **Có** — Javis Edge-TTS |
| Clone mẫu giọng | ElevenLabs / VoxCPM GPU |

## Vì sao giọng bị «Trung nói Việt»

OpenMAIC gắn `audioUrl` theo origin của request generate. Javis gọi qua
`host.docker.internal` → MP3 Edge đúng nhưng URL kiểu
`http://host.docker.internal:3000/api/classroom-media/...` — trình duyệt **không tải được**
→ fallback Browser Native (giọng hệ thống Trung/Anh đọc Việt).

**Cách xử lý dứt điểm (đã có trong deploy + Javis ≥ 0.55.131):**

1. `OPENMAIC_PUBLIC_URL` = URL trình duyệt mở được (domain hoặc `http://IP:3000`).
2. Javis gửi `X-Forwarded-Host` / `X-Forwarded-Proto` khi generate → audioUrl đúng host.
3. Deploy rewrite classroom JSON cũ + tắt Browser Native.
4. **Tạo lại lớp** sau khi deploy (hoặc xoá site data OpenMAIC nếu vẫn nghe giọng cũ từ IndexedDB).

## Deploy

```bash
cd ~/javis-os && git pull
# Tuỳ chọn nếu DNS domain chưa trỏ:
# export OPENMAIC_PUBLIC_URL=http://<IP-VPS>:3000
OPENMAIC_BUILD=0 bash scripts/vps-deploy-openmaic.sh
```

Hoặc trên GitHub: **Actions → Deploy OpenMAIC to VPS → Run workflow**.

Đẩy thay đổi `scripts/vps-deploy-openmaic.sh` / `deploy/openmaic/**` / workflow lên `main` cũng tự chạy deploy (mặc định domain + BUILD=0).

Script:

- Shared TTS key + `TTS_OPENAI_*` → Javis.
- Ghi `OPENMAIC_PUBLIC_URL` vào Javis `/data/state/openmaic_public_url`.
- **ACCESS_CODE mặc định tắt** (Javis là cửa chính). Bật: `OPENMAIC_ACCESS_CODE=...`.
- Nginx cho phép **iframe** từ `javis.vietmycollege.com`.
- Upload body 512MB.
- Tắt Browser Native (`TTS_BROWSER_NATIVE_ENABLED=false` + `server-providers.yml`).

Javis compose cần `OPENMAIC_BASE_URL=http://host.docker.internal:3000` + `extra_hosts` host-gateway (đã có trong `docker-compose.yml`).

## Dùng trong Javis

1. Việc → Bài giảng → tab **Lớp học** → Chạy (tạo `lop-hoc.md`).
2. Cột Kết quả → **Tạo lớp OpenMAIC**.
3. Đợi poll → classroom hiện iframe trong trang Javis.

API language = `en-US` + nội dung tiếng Việt (tránh fallback `zh-CN` của OpenMAIC).

## Kiểm tra

```bash
curl -fsS http://127.0.0.1:3000/api/health
# Từ trong container Javis:
docker exec javis curl -fsS http://host.docker.internal:3000/api/health
# Public URL đã ghi:
docker exec javis cat /data/state/openmaic_public_url
```

## Clone giọng (tuỳ chọn)

ElevenLabs / VoxCPM: thêm key hoặc `TTS_VOXCPM_BASE_URL` vào `~/openmaic/.env.local`, restart OpenMAIC.
