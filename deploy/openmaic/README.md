# OpenMAIC trên VPS (cùng máy với Javis)

## Mục tiêu

- Classroom live tự host.
- **TTS mặc định:** Edge-TTS tiếng Việt chuẩn (Hoài My / Nam Minh) qua proxy trên Javis — **không** dùng Browser Native (Chrome).
- **Clone giọng:** tuỳ chọn sau qua ElevenLabs hoặc VoxCPM2 (GPU) — không bật sẵn trên VPS CPU.

## Giới hạn thật

| Hạng mục | Trên VPS CPU? |
|----------|----------------|
| Chạy OpenMAIC + generate classroom | Cần **Gemini API key** (free tier Google AI Studio thường đủ) |
| Giọng đọc tiếng Việt chuẩn | **Có** — Javis `POST /v1/audio/speech` (Edge-TTS) |
| Clone mẫu giọng giảng viên | Cần ElevenLabs key hoặc VoxCPM trên GPU |

## Deploy

1. Đảm bảo Javis đã có **Models → Google Gemini** (key), hoặc secret `OPENMAIC_GOOGLE_API_KEY`.
2. DNS: bản ghi **A** `openmaic.vietmycollege.com` → IP VPS.
3. Push script/workflow lên `main`, rồi:

```bash
cd ~/javis-os && git pull
OPENMAIC_BUILD=0 bash scripts/vps-deploy-openmaic.sh
```

Hoặc GitHub → Actions → **Deploy OpenMAIC to VPS**.

Script sẽ:

- Tạo shared key `OPENMAIC_TTS_PROXY_KEY` (file trên host + `/data/state` trong container Javis).
- Ghi `TTS_OPENAI_*` vào `~/openmaic/.env.local`.
- Chạy container OpenMAIC với `--add-host=host.docker.internal:host-gateway`.

## Sau khi lên

1. Mở `https://openmaic.vietmycollege.com`.
2. Settings → **Text-to-Speech** → **OpenAI** (Base URL đã seed từ env).
3. Voice gợi ý: `nova` / `alloy` → Hoài My; `onyx` / `echo` → Nam Minh (hoặc `vi-VN-HoaiMyNeural`).
4. Generate classroom và nghe thử.

Kiểm tra proxy từ VPS:

```bash
KEY=$(cat ~/openmaic/.tts_proxy_key)
curl -fsS -X POST http://127.0.0.1:7777/v1/audio/speech \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"input":"Xin chào học viên.","voice":"nova"}' -o /tmp/om-tts.mp3
file /tmp/om-tts.mp3
```

## Bật clone giọng sau này

### ElevenLabs

Thêm vào `~/openmaic/.env.local`:

```env
TTS_ELEVENLABS_API_KEY=...
```

Restart OpenMAIC; Settings → TTS → ElevenLabs → upload / chọn voice clone.

### VoxCPM2 (GPU)

```env
TTS_VOXCPM_BASE_URL=http://<ip-gpu>:8000/v1
```

Settings → TTS → **VoxCPM2** → Clone voice (upload mẫu ngắn).
