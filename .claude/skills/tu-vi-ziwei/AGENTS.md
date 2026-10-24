# Tử Vi Ziwei - Agent Guide

Upstream: [Renhuai123/ziwei-doushu](https://github.com/Renhuai123/ziwei-doushu) (**MIT**).

| Skill / agent | Job |
|---------------|-----|
| `tu-vi-ziwei` | Lập lá số + tra cổ thư + quy trình luận |
| Agent hệ thống `tu-vi-chuyen-gia` | Vai chuyên luận giải (nạp skill trên) |

**Không** vendor app Next hay dataset ~56GB vào image.
Clone shallow qua `scripts/ensure-ziwei.sh` → `$JAVIS_STATE_DIR/vendor/ziwei-doushu`.
Runtime `iztro` → `$JAVIS_STATE_DIR/vendor/javis-ziwei-runtime`.

Artifact: `exports/tu-vi/<slug>/`.
