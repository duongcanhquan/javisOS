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

## Deploy

```bash
cd ~/javis-os && git pull
OPENMAIC_BUILD=0 bash scripts/vps-deploy-openmaic.sh
```

Script:

- Shared TTS key + `TTS_OPENAI_*` → Javis.
- **ACCESS_CODE mặc định tắt** (Javis là cửa chính). Bật: `OPENMAIC_ACCESS_CODE=...`.
- Nginx cho phép **iframe** từ `javis.vietmycollege.com`.
- Upload body 512MB.

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
```

## Clone giọng (tuỳ chọn)

ElevenLabs / VoxCPM: thêm key hoặc `TTS_VOXCPM_BASE_URL` vào `~/openmaic/.env.local`, restart OpenMAIC.
