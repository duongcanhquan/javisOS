# Kênh Agent-Reach (tóm tắt)

Upstream: https://github.com/Panniantong/Agent-Reach

| Nhu cầu | Kênh | Ghi chú |
|---------|------|---------|
| Đọc URL bất kỳ | Jina Reader | Thường zero-config |
| YouTube phụ đề / search | yt-dlp | Zero-config khi có binary |
| Bilibili | bili-cli | yt-dlp Bilibili đã yếu |
| RSS/Atom | feedparser | Zero-config |
| Semantic web search | Exa via mcporter | Cần cấu hình MCP |
| GitHub | gh CLI | Public OK; private cần login |
| Twitter/X | twitter-cli / OpenCLI | Cookie / session |
| Reddit | OpenCLI / rdt-cli | Cần login; anonymous chết |
| Facebook / Instagram | OpenCLI | Desktop Chrome session |
| Xiaohongshu | OpenCLI / xhs MCP | Cookie / session; VPS khó |
| LinkedIn | MCP / Jina | Public shallow vs MCP sâu |
| V2EX / Xueqiu | CLI kênh | Theo doctor |
| Podcast Xiaoyuzhou | Whisper path | Cần cấu hình |

Luôn tin `agent-reach doctor` hơn bảng này (backend đổi theo thời gian).
