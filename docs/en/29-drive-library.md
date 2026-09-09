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

## Setup in the dashboard (recommended)

1. Javis image ≥ 0.55.154 includes `rclone`.
2. **Brain → Drive library**:
   - **localhost:** click **Connect Google Drive** → Allow.
   - **VPS:** click to get download links → Mac (`.command`) or Windows (`.bat`) → double-click → Allow Google → return to the page.
3. **Name** + paste Drive folder **URL** → **Create & sync**.

## Daily use

Update Drive → Sync now → open the chat Project → ingest important files → write skills. Do not mass-ingest the whole library in one turn.
