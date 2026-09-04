# Pixelle-Video — API & vận hành (tóm tắt)

Nguồn: [docs/en/reference/api-overview.md](https://github.com/ATH-MaaS/Pixelle-Video/blob/main/docs/en/reference/api-overview.md),
`api/schemas/video.py`.

## Chạy server

```bash
git clone https://github.com/ATH-MaaS/Pixelle-Video.git
cd Pixelle-Video
cp config.example.yaml config.yaml   # điền llm + image/tts
# WebUI:
./start_web.sh    # hoặc start_web.bat → thường http://localhost:8501
# REST:
uv run uvicorn api.app:app --host 0.0.0.0 --port 8000
# Swagger: http://localhost:8000/docs
```

Javis gọi qua `PIXELLE_API_BASE` (vd `http://172.17.0.1:8000` từ Docker).

## Endpoints chính

| Method | Path | Dùng khi |
|--------|------|----------|
| POST | `/api/video/generate/async` | Mặc định — trả `task_id` |
| GET | `/api/tasks/{task_id}` | Poll tới `completed` / failed |
| POST | `/api/video/generate/sync` | Video ngắn, chấp nhận chờ |

### Body `VideoGenerateRequest` (rút gọn)

| Field | Ý nghĩa |
|-------|---------|
| `text` | Topic **hoặc** script đầy đủ |
| `mode` | `generate` = AI viết narration; **`fixed` = dùng text như script** |
| `n_scenes` | 1–20; chỉ có hiệu lực khi `generate` |
| `title` | Tiêu đề |
| `frame_template` | vd `1080x1920/image_default.html` |
| `template_params` | màu, background… theo template |
| `prompt_prefix` | Style ảnh |
| `media_workflow` / `tts_workflow` | Override workflow Comfy/RunningHub |
| `bgm_path` / `bgm_volume` | Nhạc nền (0–1, mặc định 0.3) |
| `ref_audio` | Voice clone (nếu workflow hỗ trợ) |

### Ví dụ fixed (skill mặc định)

```http
POST /api/video/generate/async
Content-Type: application/json

{
  "text": "Câu hook.\n\nCâu ý 2.\n\nCTA cuối.",
  "mode": "fixed",
  "title": "Thói quen 1%",
  "frame_template": "1080x1920/image_default.html",
  "prompt_prefix": "minimal clean illustration, soft light"
}
```

Poll:

```http
GET /api/tasks/{task_id}
→ status: completed, result.video_url, duration, file_size
```

## Python SDK (máy có cài Pixelle)

```python
from pixelle_video.service import PixelleVideoCore
import asyncio

async def main():
    pixelle = PixelleVideoCore()
    await pixelle.initialize()
    result = await pixelle.generate_video(
        text="...",  # script fixed
        mode="fixed",
        title="...",
        frame_template="1080x1920/image_default.html",
    )
    print(result.video_path)

asyncio.run(main())
```

## Config cần nhớ (`config.yaml`)

- `llm`: mọi API OpenAI-compatible (Qwen / OpenAI / DeepSeek / Ollama)
- `comfyui.image.default_workflow`: thường `runninghub/image_flux.json`
- `comfyui.tts.default_workflow`: `selfhost/tts_edge.json`
- `template.default_template`: `1080x1920/image_default.html`

Không commit `config.yaml` (có key).

## Khi không gọi được API Pixelle

**Đừng dừng.** Gọi tool Javis `javis_render_script_video` với cùng kịch bản (mỗi cảnh
một đoạn) → ra `attachments/*.mp4` ngay.

Chỉ xuất Manual pack (title + narration + image prompt + template) khi user **cố ý**
muốn tự dán WebUI Pixelle / máy khác.
