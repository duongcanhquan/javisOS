# OpenMontage - họ năng lực (tóm tắt)

Registry runtime là nguồn sự thật. Trong clone:

```bash
python -c "from tools.tool_registry import registry; import json; registry.discover(); print(json.dumps(registry.capability_catalog(), indent=2))"
```

Họ capability thường gặp (selector tự chọn provider khi có):

| Capability | Việc |
|---|---|
| tts / music_* | Thoại, nhạc |
| video_generation / image_generation | Gen shot / ảnh |
| audio_processing / video_post / subtitle | Hậu kỳ ffmpeg |
| avatar / character_animation | Avatar, character |
| 3d_* | Thế giới / asset 3D |
| analysis / enhancement | Phân tích, enhance |

Khi user chưa chỉ provider → dùng selector của OpenMontage.
Brief ngắn / collage giấy → ưu tiên `paperdesign` trong Javis, không ép OpenMontage.
