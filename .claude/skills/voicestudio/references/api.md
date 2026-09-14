# VoiceStudio API local (rút từ README upstream)

Backend mặc định: `http://127.0.0.1:3900`

Đổi client OpenAI: `base_url="http://localhost:3900/v1"`, `api_key="local"`.

| Endpoint | Việc |
|---|---|
| `POST /v1/audio/speech` | TTS. `model` = engine, `voice` = profile, `response_format` = mp3/opus/aac/flac/wav/pcm |
| `POST /v1/audio/transcriptions` | STT. output json/text/verbose_json/srt/vtt |
| `WS /v1/audio/transcriptions/stream` | Chép lời sống |
| `GET /v1/audio/voices` | Danh sách voice + engine |
| `GET /.well-known/voicestudio-speech` | Discover HTTP / WS / MCP |
| `http://localhost:3900/mcp` | MCP (`generate_speech`, `clone_voice`, `transcribe`) |

Thử TTS:

```bash
curl http://127.0.0.1:3900/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model":"tts-1","input":"Xin chao","voice":"default","response_format":"wav"}' \
  --output exports/voice/thu.wav
```

Docker mẫu (linux/amd64): cổng `127.0.0.1:3900:3900`, image `palashdeb/omnivoice-studio:stable`.

Tài liệu đầy đủ: https://github.com/debpalash/VoiceStudio
