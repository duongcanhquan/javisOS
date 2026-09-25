# Chat folder attach — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Nút chọn folder cạnh đính kèm chat → upload cây file → Javis đọc hết hoặc làm theo lệnh.

**Architecture:** Client pick (Directory Picker / webkitdirectory) → `POST /upload/folder` → staging `folders/<id>/` → one folder chip → sendMessage context block.

**Tech Stack:** FastAPI multipart, dashboard `app.js` + `index.html`, i18n vi/en.

---

### Task 1: Server `/upload/folder`

**Files:**
- Modify: `server/main.py` (near `/upload`)
- Create/Modify: `server/chat_upload_limits.py` (folder caps)
- Test: `tests/python/test_chat_folder_upload.py`

**Step 1:** Caps: `FOLDER_MAX_FILES=50`, `FOLDER_MAX_TOTAL=100MB`, per-file reuse existing.
**Step 2:** Endpoint accepts `files[]` + `relpaths[]` + `brain` + optional `folder_name`.
**Step 3:** Write under `STAGING/folders/<uuid>/` preserving safe relative paths (no `..`).
**Step 4:** Return `{ok, folder_id, root, name, files:[{rel,staged,size,kind}], skipped:[{rel,reason}]}`.

### Task 2: Chat UI button + upload

**Files:**
- Modify: `dashboard/index.html` (button + hidden input)
- Modify: `dashboard/app.js` (pick, upload, chip, sendMessage context)
- Modify: `dashboard/i18n/vi.json`, `en.json`

**Step 1:** `#folderBtn` + `#folderInput` (webkitdirectory).
**Step 2:** `chonFolderChat()` → collect File list with `webkitRelativePath` or File System Access walk.
**Step 3:** Bypass 3-doc limit for folder batch; one chip `kind:"folder"`.
**Step 4:** `sendMessage` context for folder attachments.

### Task 3: Docs + CHANGELOG + version

**Files:** `CHANGELOG.md`, `VERSION`, short note in `docs/02-tro-chuyen-va-giong-noi.md` if attach section exists.

### Task 4: Commit, push, PR
