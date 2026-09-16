---
name: Slide Wright
description: "Slide/pitch/proposal HTML đẹp: trình chiếu, PDF chiếu, pitch deck. Theme riêng, preview rồi gen. exports/slides/."
description_en: "Polished HTML slides/pitch/proposal decks: presentation, pitch PDF, unique theme, preview then full. Writes exports/slides/."
group: Nội dung
metadata:
  upstream: https://github.com/arifszn/slide-wright
  upstream_skill: slide-wright
  license: MIT
---

# Slide Wright

Installed from [arifszn/slide-wright](https://github.com/arifszn/slide-wright) (MIT).
Skill root: `.claude/skills/slide-wright/` - load `references/` only when the step needs them.

Turn a topic or rough notes into a polished, animated web presentation - a single
self-contained HTML file that runs in any browser.

## Khi nào dùng

- User muốn slide / presentation / pitch deck / talk deck / **PDF trình chiếu** / PowerPoint đẹp.
- Proposal hoặc nghiên cứu xong cần **chiếu** (không chỉ đọc Markdown).
- Tab **Việc → Bài giảng → Slide**, chat «làm slide / deck HTML / pitch / trình bày».
- Sửa deck HTML sẵn (thêm/bớt/đổi slide) mà giữ theme đã duyệt.

**Không dùng** khi user chỉ cần outline sư phạm + speaker note (Markdown) → `bai-giang-slide`.
Proposal nội dung (chữ) trước → `proposal-chien-luoc`, rồi mới skill này để chiếu.
Lớp học tương tác OpenMAIC → `bai-giang-lop-hoc`. Video → `lam-video` / `paperdesign`.
Gói PDF/PPTX tóm tắt research → `xuat-goi-nghien-cuu` (PPTX đơn giản); deck đẹp vẫn là skill này.

## Cách nói với user

Làm thầm. Không kể skill, không kể folder đã thấy, không kể sẽ preview hay full, không kể
lỗi PDF rồi sửa. User không cần nhật ký.

- Preview: một câu duyệt theme + embed 2 slide. Hết.
- Full xong: 1-3 câu + đường dẫn. Đúng: `Đã dựng 10 slide UAV + PDF. [mở deck](exports/slides/uav/index.html)`
- Sai: dãy "Em sẽ dùng slide-wright… Em đã thấy bộ… Em sẽ xuất PDF…"

## Javis output path

Ghi deck vào vault:

`exports/slides/<slug>/index.html`

(slug ASCII, không dấu). Khi preview/approve vẫn là **cùng một file** này (không file demo riêng).
Embed trong chat: `[mở deck](exports/slides/<slug>/index.html)`.

Giữ `slides.md` + speaker notes nếu workflow bài giảng cần (agent `bg-slide` có thể ghi cả hai).

## The rule that defines this skill

Propose the look before you build the deck. On the first pass you never produce a finished
presentation. You generate a theme, build a two-slide preview in it, and stop until the user
approves the direction. Only then do you build the rest.

- One proposal at a time, not a menu. If the user says no, throw the direction out and try a
  clearly different one.
- Every theme is invented for the deck in front of you. No preset library.
- Aim for a deck that looks deliberately designed, not averaged. See
  `references/design-aesthetics.md`.
- Output is one HTML file with theme CSS inline and the engine from a CDN. No build step, no npm.

## The engine (keep this internal)

Decks render with reveal.js loaded from a CDN, but that is an implementation detail the user
never sees. Don't name reveal.js, "reveal," or any library in conversation, in the README, or
anywhere in the deck itself. The user's vocabulary is slides, themes, and design. The library
name appears only inside the generated `<link>` and `<script>` tags.
`references/deck-template.md` has the exact setup.

## Editing a deck that already exists

If the user points at an existing HTML deck, check whether it's built on reveal.js (look for the
reveal.js `<link>`/`<script>` tags from a CDN). If it is - whether or not this skill built it -
don't start over: read it, keep its theme, and make the change in place. Skip the proposal gate.
After editing, check that nothing overflows or overlaps.

If the deck is HTML but not on reveal.js, say so rather than forcing a rewrite.

## Step 1 - Work out the deck from the request

Don't open with a questionnaire. Take whatever the user gave and infer purpose, audience,
length, and density.

- A deck **made to be spoken over**: one idea per slide, large type, more slides.
- A deck **made to be read alone**: structured grids, more words, still deliberate spacing.

Only ask if the request is too thin to design from. Never let a slide scroll, overflow, overlap,
or shrink text below comfortable reading - split instead.

## Step 2 - Propose a look

Read `references/theme-generation.md` and `references/design-aesthetics.md`, then:

1. Invent a theme: palette, display/body type from Fontshare or Google Fonts, layout grammar,
   one recurring visual device. Name it for your own use.
2. Build a two-slide preview with `references/deck-template.md` - real title + one content
   slide - at `exports/slides/<slug>/index.html`.
3. Open it / embed the relative vault path for the user.

Keep process language off the slide and out of the filename: no "demo," "preview," theme name,
or "option A."

## Step 3 - Get a yes

Stop and ask (JAVIS_ASK when on dashboard):

> "Đây là hướng thiết kế - *[theme name]*. Ổn chưa, hay đổi hướng?"

- **Ổn - làm full** → Step 4
- **Đổi hướng** → theme mới hoàn toàn, ghi đè cùng `index.html`
- **Chỉnh nhẹ** (ấm hơn / tối giản hơn…) → chỉnh rồi show lại

Do not build the full deck before a yes. In background/Kanban-only runs with no human in the
loop: still write the 2-slide preview and stop with a clear "chờ duyệt theme" note - never
silently expand to full.

## Step 4 - Build the deck

Keep building in the **same** `exports/slides/<slug>/index.html`. Keep the two approved slides;
append the rest. Read `references/motion-recipes.md`.

- Same palette, fonts, spacing, device throughout.
- Vary layouts: title, section break, two-column, quote, comparison, closing.
- Speaker notes in `<aside class="notes">` when content implies spoken delivery.
- One self-contained HTML file: theme CSS inline, engine from CDN.

After build, verify in a real browser render: no overflow, no overlapping panels, 16:9 intact,
fonts loaded.

## Step 5 - Hand it off

One to three sentences: path, slide count, embed. No process, no engine names, no print recipe
unless the user asked how to export.

Offer revise / retheme / PDF / deploy only if they ask what else is possible
(`references/deploy.md` - let user pick host).

## Liên kết

- Outline sư phạm + notes dài → `bai-giang-slide` (có thể chạy trước, rồi Slide Wright render HTML).
- Điều phối đầu ra bài giảng → `tao-bai-giang`.
- Biểu đồ trong slide → `diagram-design`.

## Bẫy

- Không gen full deck trước khi user duyệt theme (trừ khi user nói rõ «làm luôn full, khỏi preview»).
- Không em dash (U+2014) trong file hay chat.
- Không kể tên engine/library với user.
- Không ghi deck ra chỗ lung tung ngoài `exports/slides/<slug>/`.
- Không nhật ký bước với user. Xong mới nói, 1-3 câu.
