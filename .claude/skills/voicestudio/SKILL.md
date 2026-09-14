---
name: voicestudio
description: "TTS, nhân bản giọng, lồng tiếng video, chép lời trên máy qua VoiceStudio (localhost:3900)."
description_en: "Local TTS, voice clone, video dub, and transcription via VoiceStudio (localhost:3900)."
group: Nội dung
license: AGPL-3.0
metadata:
  version: "1.0"
  upstream: "https://github.com/debpalash/VoiceStudio"
---

# VoiceStudio (giọng nói local)

## Dùng để làm gì

Chạy **giọng nói trên máy bạn**, không gửi audio lên cloud:

- Đọc văn bản thành file âm thanh (TTS)
- Nhân bản giọng từ clip mẫu ngắn
- Lồng tiếng video: chép lời → dịch → giữ speaker → xuất video
- Chép lời / dictation (ASR)
- Audiobook nhiều giọng

Nguồn: [debpalash/VoiceStudio](https://github.com/debpalash/VoiceStudio) (AGPL-3.0, beta). Javis **không** nhúng app; skill này bảo agent gọi API local khi user đã cài.

## Khi nào dùng

- «đọc thành tiếng», «TTS local», «lồng tiếng», «dub video», «chép lời file này», «nhân bản giọng»
- User muốn mic/voice **không** qua ElevenLabs / OpenAI Audio

**Không dùng** cho transcript họp đã có trong `sources/meetings` (`phan-tich-cuoc-hop`) hay tóm tắt YouTube công khai (`tom-tat-video`).

## Chuẩn bị

1. VoiceStudio phải **đang chạy** trên máy (app desktop hoặc Docker cổng 3900). **Không tự cài** nếu user chưa đồng ý.
2. Engine có shell/HTTP: kiểm tra API.

```bash
curl -sS -o /dev/null -w "%{http_code}" http://127.0.0.1:3900/v1/audio/voices
```

3xx/200 = sống. Lỗi kết nối → nói «chưa bật VoiceStudio» + link release, dừng.

3. Chi tiết endpoint: `references/api.md`.

## Cách chạy

Ưu tiên HTTP OpenAI-compatible (`base_url=http://127.0.0.1:3900/v1`). MCP: `http://localhost:3900/mcp` nếu user đã đấu.

| Việc | Làm |
|---|---|
| TTS | `POST /v1/audio/speech` → ghi file vào vault `exports/voice/` |
| Chép lời | `POST /v1/audio/transcriptions` (multipart file) |
| Liệt kê giọng | `GET /v1/audio/voices` |
| Lồng tiếng / clone | App UI hoặc MCP `clone_voice` / `generate_speech` - xem OpenAPI trong Settings VoiceStudio |

Ghi trong chat: file output + engine/voice đã dùng. Không dump log dài.

## Bẫy

- **Không** nhân bản giọng người thật khi chưa có **đồng ý** rõ (consent). Giọng thiết kế (age/accent) thì được.
- Không mở cổng 3900 ra internet. Localhost thôi.
- Model có thể CC-BY-NC: không hứa dùng thương mại.
- AGPL áp cho app VoiceStudio, không copy mã nguồn vào repo Javis.
- Plugin Javis bọc API: chỉ khi user yêu cầu tool native; skill này đủ cho agent gọi HTTP.

## Kiểm chứng

- [ ] API :3900 sống **hoặc** đã nói chưa cài
- [ ] Có file wav/mp3/txt trong `exports/voice/` khi làm TTS/STT
- [ ] Không clone giọng người lạ
