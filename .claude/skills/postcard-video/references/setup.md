# Setup upstream video-shotcraft

## Where it lives

Clone **outside** the app image into state:

```text
$JAVIS_STATE_DIR/vendor/video-shotcraft
```

If `JAVIS_STATE_DIR` unset, script falls back to `~/.javis/vendor/video-shotcraft`.

Do **not** put the clone under the git repo `vendor/` (ignored) as the source of truth for production; prefer state dir so Docker volume persists across updates.

## Ensure (preferred)

From repo / container cwd that has the skill tree:

```bash
bash .claude/skills/postcard-video/scripts/ensure-shotcraft.sh
# or after brain sync:
bash skills/postcard-video/scripts/ensure-shotcraft.sh
```

Exit 0 prints the absolute path. Re-run is idempotent (fetch if already cloned).

## Manual install (same effect)

```bash
mkdir -p "${JAVIS_STATE_DIR:-$HOME/.javis}/vendor"
git clone --depth 1 https://github.com/Vincentwei1021/video-shotcraft.git \
  "${JAVIS_STATE_DIR:-$HOME/.javis}/vendor/video-shotcraft"
```

Optional: also link for Claude Code native load:

```bash
ln -sfn "${JAVIS_STATE_DIR:-$HOME/.javis}/vendor/video-shotcraft" \
  ~/.claude/skills/video-shotcraft
```

Javis routing uses skill **`postcard-video`**; upstream folder keeps name `video-shotcraft`.

## Host packages

| Need | Check |
|------|--------|
| Node ≥ 20 | `node -v` |
| npm | `npm -v` |
| ffmpeg | `ffmpeg -version` |
| CLI engine + Bash | Models page: Claude Code / Codex / Antigravity |

Template upstream:

```bash
cd "$SHOTCRAFT/template" && npm install
npm run dev    # Remotion studio
npm run render # example composition
```

Gallery of motions (browser): https://vincentwei1021.github.io/video-shotcraft/

## Network

First clone needs GitHub egress. Offline machine: copy a pre-cloned tree into the vendor path above.
