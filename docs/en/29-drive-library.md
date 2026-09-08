# Drive library — Google Drive knowledge on a VPS

***English** · [Tiếng Việt](../29-kho-drive.md)*

Sync a Google Drive folder into the Second Brain with **rclone**, then work it as a **chat Project**: ask questions, `ingest-source`, write skills. No Google Workspace browser OAuth on the Javis host.

## Layout

| Layer | Path | Role |
|---|---|---|
| Drive | Google Drive folder | Source of truth |
| Corpus | `JAVIS_STATE_DIR/drive-corpus/<brain>/<slug>/` | Binary tree after `rclone sync` |
| Sources | `<brain>/sources/drive/<slug>/` | Mirrored `.md` / PDF stubs |
| Chat project | Auto-created | Pins README + instructions |

## One-time VPS setup

```bash
bash scripts/setup-rclone-drive-vps.sh
rclone config   # remote name: gdrive
```

Then in the dashboard: **Brain → Drive library** → create → **Sync now**.

## Daily use

Update Drive → Sync now → open the chat Project → ingest important files → write skills. Do not mass-ingest the whole library in one turn.
