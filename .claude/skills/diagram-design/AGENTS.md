# Diagram Design — Agent Guide

Installed as skill **`diagram-design`** from
[cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design) (MIT).

Editorial HTML/SVG diagrams (architecture, flowchart, journey, charts, …). Not a
Python MCP plugin - follow `SKILL.md` and load `references/` only for the types you pick.

## How to use

1. Read **`SKILL.md`** (style-guide gate, type selection, density rules).
2. Before drawing, load the matching `references/type-*.md` (and style guide / onboarding if needed).
3. Run extract helpers from this skill root when redrawing sources:
   `python3 scripts/drawio_extract.py|mermaid_extract.py|excalidraw_extract.py …`
4. Write finished HTML under the vault (`attachments/` or `exports/diagrams/`) and embed a relative link.

## Javis routing

- UI page / product UI → `frontend-design` / `baseline-ui` / `improve-ui`
- DESIGN.md → `create-design-md`
- Editorial diagram → **this skill**
- Quick scratch in chat → Mermaid markdown is enough

Router map: `ui-skills-root`.
