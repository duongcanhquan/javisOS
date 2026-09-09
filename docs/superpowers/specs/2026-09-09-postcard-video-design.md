# Postcard Video (video-shotcraft) - design

Date: 2026-09-09  
Status: approved for ship (user asked to install as **postcard video**)

## Goal

Add a Javis system skill named **`postcard-video`** that wraps upstream
[Vincentwei1021/video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft)
for short cinematic product / promo clips ("postcard" length and format), without
vendoring the ~100MB upstream tree into the Docker image.

## What upstream is

- An **agent skill** (not a SaaS): recipe cards + Remotion demos + SFX/BGM + Ink Press template.
- Default template: **1920×1080 @ 30fps, ~36s**.
- Audio focus: **BGM + SFX**. Narration VO/TTS is optional; sister repo **video-talkcraft** is for VO-locked narration.
- Needs: Node 20+, Remotion project, ffmpeg; product URL/screenshots; a CLI engine with shell (Claude Code / Codex / Antigravity).

## Duration (honest limits)

| Range | Guidance |
|-------|----------|
| **15-45s** | Sweet spot for postcard / Reels / product teaser (recommended default **30s**) |
| **~36s** | Upstream Ink Press template length |
| **60-90s** | Possible but costly: more shots, longer Remotion render, higher agent error rate |
| **>2 min** | Not a fit; use paperdesign / html-video / external NLE, or split into chapters |

Hard cap is not encoded in Remotion; the limit is **agent + render cost**. Postcard mode defaults to ≤45s and warns above 60s.

## Postcard fit

"Postcard video" in Javis means:

1. Short cinematic product/promo (not long explainer with dense VO).
2. Aspect chosen per brief: **9:16** (phone postcard / Stories), **1:1**, or **16:9** (upstream default).
3. Shotcraft recipe cards + SFX/BGM; optional user-supplied VO file (TTS not first-class here).

Upstream demos are landscape-first; vertical/square requires remounting the Remotion composition (document in skill).

## Approach chosen

**Thin adapter skill in-repo + clone-on-demand to state dir.**

- Ship only `SKILL.md` + small `references/` + `scripts/ensure-shotcraft.sh` under `.claude/skills/postcard-video/`.
- First run clones upstream shallow into `$JAVIS_STATE_DIR/vendor/video-shotcraft` (gitignored `vendor/` pattern; state dir is outside image).
- Wire pipeline id `postcard-video` into `lam-video` catalog.
- Do **not** copy 100MB assets into GHCR image.

### Rejected

- Full vendor into `.claude/skills` (image bloat, CI sync cost).
- Only documenting a manual `npx skills add` (user asked to install into Javis).

## Requirements to actually render

1. CLI Main Model with Bash (Claude Code / Codex / Antigravity).
2. Node.js 20+ and npm on the machine running the agent.
3. ffmpeg.
4. Upstream clone (script) + `npm install` in template or project folder.
5. Product assets: URL and/or screenshots (2x full-page preferred).
6. Optional: finished VO file if user wants speech; otherwise SFX/BGM only.

## Integration points

- Skill: `.claude/skills/postcard-video/`
- Catalog: `lam-video/references/catalog.md` row `postcard-video`
- Brief checklist: allow Pipeline value `postcard-video`
- Outputs: Remotion `out/*.mp4` then copy/link into brain `attachments/videos/` when user asks to keep in vault

## Out of scope (v1)

- Bundling Motion Workbench UI into Javis dashboard
- Auto TTS (point users to pixcelvideo/paperdesign or talkcraft)
- JianYing export automation inside Javis
