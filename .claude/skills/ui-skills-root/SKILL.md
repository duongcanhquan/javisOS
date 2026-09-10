---
name: Design UI Skill
description: "Bộ skill thiết kế UI: chọn ngữ cảnh nhỏ nhất, polish layout, a11y, SEO meta, motion."
description_en: "UI skills router: pick the smallest useful context for layout, a11y, SEO meta, motion."
group: Marketing
license: MIT
---
# Design UI Skill

You are the routing layer for UI Skills.

This skill is shown by `npx ui-skills start` and is also available in the registry.

Use it when an agent in Codex, Cursor, or Claude Code has a clear UI goal.

If the goal is unclear, ask one short question.

If the goal is clear, choose the right category, load the smallest useful skill context, then implement.

## Javis skill map (ưu tiên trước CLI)

Khi brief khớp một skill hệ thống dưới đây, **nạp skill đó** (không chỉ `npx ui-skills`):

| Brief | Skill |
|---|---|
| UI sản phẩm distinctive (palette/type/layout) | `frontend-design` |
| Polish nhanh spacing/hierarchy (deslop) | `baseline-ui` |
| Audit UI có sẵn + plan handoff | `improve-ui` |
| Ghi / cập nhật `DESIGN.md` từ repo hoặc site | `create-design-md` |
| Sơ đồ editorial HTML/SVG (kiến trúc, flowchart, journey, chart…) | `diagram-design` |
| Landing / sales page HTML (brief hoặc chủ đề → copy + layout) | `landing-page` |
| A11y / meta / motion HTML | `forming-accessibility` / `forming-metadata` / `forming-motion-performance` |

**Diagram ≠ UI page.** Brief kiểu architecture diagram, flowchart, user journey map,
org chart, redraw draw.io/Mermaid → **`diagram-design`**, không tự vẽ SVG trong
`frontend-design`. Mermaid tạm trong chat vẫn ổn khi không cần bản editorial.

**Landing ≠ app UI.** Brief kiểu trang giới thiệu sản phẩm / sales page / waitlist →
**`landing-page`** (catalog + `exports/landing/`). `frontend-design` dành cho UI sản phẩm
trong app, không thay cổng chọn layout landing.

## Protocol

1. decide if the task is UI-related (hoặc diagram editorial - vẫn thuộc map trên)
2. if not, return `no skill needed`
3. identify the likely category **or** the Javis skill in the map above
4. if a Javis system skill matches, load it and stop CLI browsing for that goal
5. otherwise inspect that category with the CLI
6. select the smallest useful skill set
7. load only selected skill(s)
8. implement using that context

## CLI

```bash
npx ui-skills start
npx ui-skills categories
npx ui-skills list --category <category>
npx ui-skills get <slug>
```

## Selection Rules

Prefer 1 skill.

Use 2 only when the task needs two clear angles.

Use 3 only for broad review, redesign, or multi-surface work.

Never use more than 3.

Route by topic, then stack, then specificity.

Prefer specific skills over broad skills.

Prefer framework-specific skills when the stack is obvious.

For quick cleanup, prefer the most specific craft, visual, or layout skill available.

If unsure, inspect categories and pick the safest narrow skill.
