---
name: OpenMontage
description: "Studio video agentic OpenMontage: cài/doctor, chọn pipeline, điều phối từ lam-video. AGPL - không vendor."
description_en: "OpenMontage agentic video studio: install/doctor, pick pipeline, route from lam-video. AGPL - do not vendor."
group: "Video & Motion"
license: AGPL-3.0
metadata:
  version: "1.0"
  upstream: "https://github.com/calesthio/OpenMontage"
---

# OpenMontage

## Dùng để làm gì

Biến coding agent thành studio sản xuất video (nhiều pipeline, tool registry, skill Layer 2/3).
Nguồn: [calesthio/OpenMontage](https://github.com/calesthio/OpenMontage) (**AGPL-3.0**).

**Cấm** copy `.agents/skills/**` hay mã OpenMontage vào vault/image Javis. Chỉ clone/cài
trên host hoặc VPS riêng, rồi điều phối từ đây / `lam-video`.

## Khi nào dùng

- «OpenMontage», «Monty», «studio video agentic», «12 pipeline video»
- User muốn production video phức tạp hơn paperdesign/Remotion đơn lẻ

**Không dùng** khi brief ngắn collage Vox → `paperdesign`; Remotion UI → `remotion-best-practices`;
điều phối chung → `lam-video` trước.

## Chuẩn bị

1. Engine có **Bash** (Claude Code / Codex / Antigravity / Grok Build).
2. Đọc `references/install.md` + `references/pipelines.md`.
3. Kiểm tra clone: `test -d "$OPENMONTAGE_HOME" || test -d ~/OpenMontage`.
4. API key theo pipeline (xem docs upstream `docs/PROVIDERS.md`) - thiếu thì nói thẳng.

## Cách chạy

### Doctor

```bash
OM="${OPENMONTAGE_HOME:-$HOME/OpenMontage}"
test -d "$OM" && echo "OM_HOME=$OM" || echo "MISSING_CLONE"
command -v python3; command -v ffmpeg; command -v node
# Trong thư mục OpenMontage (nếu đã setup):
# python -c "from tools.tool_registry import registry; registry.discover(); print(registry.capability_catalog())"
```

### Quy trình với Javis

1. Nạp **`lam-video`** - cổng brief bắt buộc (chủ đề, mục tiêu, độ dài, tỉ lệ, ngôn ngữ).
2. Nếu chọn OpenMontage: làm việc **trong clone** OpenMontage (cwd = `$OM`), theo `AGENT_GUIDE.md` upstream.
3. Artifact video/export: copy kết quả sang brain `exports/video/` nếu user muốn lưu trong Javis.
4. Engine API thuần (không Bash): **không** chạy OpenMontage; đề xuất paperdesign / Pixcel / Manual pack và nêu gap.

## Bẫy

- Vendor AGPL vào repo Javis → rủi ro license. Chỉ link + clone ngoài.
- Bỏ brief `lam-video` rồi gen tốn tiền.
- Hứa «xong sẽ báo» mà không queue Kanban / không làm trong lượt.
- Không em dash.

## Kiểm chứng

- [ ] Đã doctor: có clone + ffmpeg/python hoặc nêu thiếu
- [ ] Brief đã chốt qua `lam-video`
- [ ] Không copy skill AGPL vào `skills/` Javis
