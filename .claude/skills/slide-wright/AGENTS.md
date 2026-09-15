# Slide Wright — Agent Guide

Installed as skill **`slide-wright`** from
[arifszn/slide-wright](https://github.com/arifszn/slide-wright) (MIT).

HTML/Reveal deck skill: invent a theme, show a 2-slide preview, then build a full
self-contained `index.html` after the user approves. Not a Python plugin - follow
`SKILL.md` and load `references/` only for the step you are on.

## How to use

1. Read **`SKILL.md`** (Javis paths + approval gate).
2. Before drawing HTML, load `references/theme-generation.md`,
   `references/design-aesthetics.md`, and `references/deck-template.md`.
3. Write to `exports/slides/<slug>/index.html` in the vault.
4. After approval, extend the same file; use `references/motion-recipes.md`.

## Javis routing

| Need | Skill |
|------|--------|
| Beautiful HTML deck / pitch | **this skill** |
| Pedagogy outline + long speaker notes (MD) | `bai-giang-slide` |
| Interactive classroom | `bai-giang-lop-hoc` / OpenMAIC |
| Product UI / landing | `frontend-design` / `landing-page` |
| Editorial diagram asset | `diagram-design` |

Do not vendor the upstream repo beyond this skill folder. Keep MIT `LICENSE`.
