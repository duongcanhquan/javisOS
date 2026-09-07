# OpenMAIC trên VPS (cùng máy với Javis)

## Mục tiêu

- Classroom live tự host.
- **TTS mặc định miễn phí:** Browser Native (Chrome / giọng `vi-VN` Google trên máy học viên).
- **Clone giọng:** tuỳ chọn sau qua VoxCPM2 (cần GPU hoặc máy TTS riêng) - không bật sẵn trên VPS CPU.

## Giới hạn thật

| Hạng mục | Miễn phí trên VPS CPU? |
|----------|-------------------------|
| Chạy OpenMAIC + generate classroom | Cần **Gemini API key** (free tier Google AI Studio thường đủ bắt đầu) |
| Giọng đọc tiếng Việt | **Browser Native** - miễn phí, chất lượng phụ thuộc trình duyệt học viên |
| Clone mẫu giọng giảng viên | **Không** ổn định trên VPS CPU nhỏ; bật VoxCPM khi có GPU |

## Deploy

1. Đảm bảo Javis đã có **Models → Google Gemini** (key), hoặc thêm secret `OPENMAIC_GOOGLE_API_KEY`.
2. DNS: bản ghi **A** `openmaic.vietmycollege.com` → IP VPS (cùng IP với `javis.vietmycollege.com`).
3. Push các file script/workflow lên `main`.
4. GitHub → Actions → **Deploy OpenMAIC to VPS** → Run workflow  
   (mặc định `build_from_source=0` = image nhanh; VPS nhỏ nên giữ 0).

Thiếu Gemini key: container vẫn lên (TTS Browser Native). Generate classroom cần key - dán ở Javis Models rồi chạy lại workflow.

Hoặc trên VPS:

```bash
cd ~/javis-os && git pull
OPENMAIC_BUILD=0 bash scripts/vps-deploy-openmaic.sh
```

## Sau khi lên

1. Mở `https://openmaic.vietmycollege.com` (hoặc `http://IP:3000`).
2. Settings → **Text-to-Speech** → **Browser Native**.
3. Generate classroom (hoặc nhờ Javis skill `openmaic` trỏ URL self-host).

## Bật clone giọng sau này

1. Chạy VoxCPM trên máy GPU, mở API OpenAI-compatible.
2. Trên VPS: thêm vào `~/openmaic/.env.local`:

```env
TTS_VOXCPM_BASE_URL=http://<ip-gpu>:8000/v1
```

3. `docker compose -f ~/openmaic/docker-compose.yml up -d` (hoặc restart container).
4. Settings → TTS → **VoxCPM2** → Clone voice (upload mẫu ngắn).
