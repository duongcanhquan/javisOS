# OpenMontage - Agent Guide

Upstream: [calesthio/OpenMontage](https://github.com/calesthio/OpenMontage) (**AGPL-3.0**).

| Skill | Job |
|-------|-----|
| `openmontage` | Cài/doctor + điều phối studio OpenMontage |
| `lam-video` | Cổng brief + chọn pipeline (gồm OpenMontage) |
| `paperdesign` / `remotion-best-practices` / `pixcelvideo` | Pipeline Javis sẵn có |

**Không** vendor repo OpenMontage hay `.agents/skills` vào image Javis.
Clone trên host/VPS; làm việc trong thư mục đó; copy artifact vào `exports/video/` khi cần.
