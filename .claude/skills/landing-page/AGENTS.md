# Landing page — Agent Guide

System skill **`landing-page`**: brief/topic → curated layout → Tailwind HTML in
`exports/landing/<slug>/` → chat preview + zip + optional Webcake.

Inspired by [Cruip Simple Light](https://github.com/cruip/tailwind-landing-page-template)
aesthetics only. Do **not** copy GPL Cruip source into the skill or vault templates.

## Flow

1. Read `SKILL.md`, then only the `references/` file for the current step.
2. Gate on design pick (`design-catalog.md`) before writing HTML.
3. Start from `assets/starter-simple-light.html`; customize tokens + copy.
4. Deliver per `references/delivery.md`. Pack zip with
   `python3 scripts/pack_landing.py <path-to-slug-dir>`.
5. Next.js Cruip only if explicitly requested → `references/next-cruip.md`.

## Routing

Landing / sales page HTML → **this skill**. Product app UI → `frontend-design`.
Diagrams → `diagram-design`. SEO article only → `viet-bai-seo`.
