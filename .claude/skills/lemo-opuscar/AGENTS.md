# Lemo-Opuscar - Agent Guide

Upstream: [lemomo-ai/lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar) (**MIT**).

| Skill | Job |
|-------|-----|
| `lemo-opuscar` | Phim ngắn code-render theo 51 style |
| `lam-video` | Cổng brief + chọn pipeline |
| `remotion-topic-explainer` / `remotion-best-practices` / `paperdesign` | Pipeline khác |

**Không** vendor cả thư viện (styles/demo ~ trăm MB) vào image Javis.
Clone sparse qua `scripts/ensure-lemo.sh` → `$JAVIS_STATE_DIR/vendor/lemo-opuscar`.
Làm phim trong `exports/video/<slug>/`.

Chi tiết điều phối: đọc `$LIB/AGENTS.md` sau khi ensure.
