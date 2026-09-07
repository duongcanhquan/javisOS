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
- Tạo / giữ **`ACCESS_CODE` cố định** tại `~/openmaic/.access_code` (mặc định `vietmy-openmaic`).
- Ghi `TTS_OPENAI_*` + `ACCESS_CODE` vào `~/openmaic/.env.local`.
- Chạy container OpenMAIC với `--add-host=host.docker.internal:host-gateway`.
- Nginx `client_max_body_size 512m` (upload PDF / media dễ hơn).

## Mật khẩu site (ACCESS_CODE) — cài 1 lần

| Việc | Cách |
|------|------|
| Mã mặc định lần đầu | `vietmy-openmaic` (file `~/openmaic/.access_code`) |
| Đổi mã | `OPENMAIC_ACCESS_CODE='ma-moi' bash scripts/vps-deploy-openmaic.sh` |
| Tắt hỏi mật khẩu | `OPENMAIC_ACCESS_CODE_DISABLED=1 bash scripts/vps-deploy-openmaic.sh` |
| Dùng hàng ngày | Mở site → nhập **1 lần** → cookie ~7 ngày; **không** tạo mã mỗi bài |

**Không** lấy mã tạm trên [open.maic.chat](https://open.maic.chat/) — dùng site tự host của trường.

> Image community hiện báo `0.1.0`: cổng mật khẩu `ACCESS_CODE` có từ upstream **0.1.1+**. Env đã ghi sẵn; khi nâng image/build mới sẽ hỏi mã cố định. Dù vậy **không cần** tạo mã cloud mỗi bài — generate trực tiếp trên self-host.

Trong Javis: **Việc → Bài giảng → Lớp học** → ô URL + mã site (lưu trình duyệt) + **Copy brief** / **Mở OpenMAIC**.

## Sau khi lên

1. Mở `https://openmaic.vietmycollege.com` → nhập `ACCESS_CODE` (một lần).
2. Settings → **Text-to-Speech** → **OpenAI** (Base URL đã seed từ env).
3. Voice gợi ý: `nova` / `alloy` → Hoài My; `onyx` / `echo` → Nam Minh (hoặc `vi-VN-HoaiMyNeural`).
4. **Tạo bài nhanh:** dán đề cương / paste văn bản / upload PDF → Generate classroom (không cần mã mới).

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
