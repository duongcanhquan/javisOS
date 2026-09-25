# Drive library - Google Drive knowledge on a VPS

***English** · [Tiếng Việt](../29-kho-drive.md)*

Sync **one Google Drive folder** into the Second Brain. You do **not** need the Google Workspace connection card.

> **Brain → Drive library** is different from **Connect → Google**. Here you only pull a folder into the brain.

## First-time setup (3 steps on the Drive page)

### Step 1 - Connect Google

**VMOS on this machine (localhost):** click **Connect Google Drive** → Allow → return to the page.

**VMOS on a VPS:** pick **Mac** or **Windows** → **Start connect** → Mac: copy Terminal command / Windows: download `.bat` → Allow Google → return to the page.

### Step 2 - Create a library

Name the library → paste the Drive **folder** link → **Create and sync**.

### Step 3 - Daily use

Edit files on Drive → **Sync again** on this page → open `sources/drive/…` or the chat project. Click **Distill library** (or ask Javis to read/distill everything) to ingest into the wiki. Sync only pulls files - it does not mean the content is understood yet.

rclone config lives at `/data/state/rclone.conf` (Docker).
