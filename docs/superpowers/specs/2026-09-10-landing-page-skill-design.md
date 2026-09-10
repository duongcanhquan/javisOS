# Landing page skill (chat → HTML Tailwind)

Date: 2026-09-10  
Status: approved to implement (chat)

## Goal

From Javis chat: full brief or topic → copy → curated layout pick → Tailwind
landing in vault → preview + zip + optional Webcake. Optional Next/Cruip path.

## Non-goals

- Vendoring Cruip GPL into the Docker image or `.claude/skills/`
- New dashboard page solely for landing preview
- Replacing `frontend-design` for product app UI

## Shape

- System skill `landing-page` + references + MIT starter HTML + `pack_landing.py`
- Wire: `ui-skills-root`, `marketing-hub`, `frontend-design`, `html-to-webcake`
- Output: `exports/landing/<slug>/`

## License

Starter assets: MIT (Javis). Cruip: clone-on-demand only (`next-cruip.md`).
