# Agent-Reach skills — Agent Guide

Upstream: [Panniantong/Agent-Reach](https://github.com/Panniantong/Agent-Reach) (MIT).

| Skill | Job |
|-------|-----|
| `agent-reach` | install / doctor / safety / fallback |
| `lang-nghe-mxh` | social listening → `exports/research/` |
| `tom-tat-video` | YT/Bilibili summaries → `sources/research/` |
| `theo-doi-rss-chu-de` | topic RSS digest (≠ `tong-hop-bao-chi`) |
| `y-tuong-noi-dung-tu-trend` | trends → content calendar ideas |

Do not vendor the Reach repo into the Javis image. CLI on the host/VPS; API engines
fall back to Tavily/MCP and state the gap.
