#!/usr/bin/env python3
"""Tests for server/drive_projects.py (store, slug, mirror, rclone guard)."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))

# Isolate STATE_DIR before importing modules that read config.
_TMP = tempfile.mkdtemp(prefix="javis-drive-")
os.environ["JAVIS_STATE_DIR"] = _TMP

import config as cfgmod  # noqa: E402

cfgmod.STATE_DIR = Path(_TMP)

import drive_projects as dp  # noqa: E402

ok = 0
fail = 0


def check(name, cond):
    global ok, fail
    if cond:
        ok += 1
        print(f"  OK  {name}")
    else:
        fail += 1
        print(f"FAIL  {name}")


def main():
    brain = Path(_TMP) / "Brain Test"
    brain.mkdir(parents=True, exist_ok=True)

    class FakeStore:
        def __init__(self):
            self.projects = {}
            self.files = {}

        def create_project(self, name, *, icon="", brain="brain"):
            pid = "chat-" + name[:8].replace(" ", "")
            self.projects[pid] = {"id": pid, "name": name, "brain": brain, "icon": icon}
            return pid

        def get_project(self, pid):
            return self.projects.get(pid)

        def update_project(self, pid, **kw):
            if pid in self.projects:
                self.projects[pid].update({k: v for k, v in kw.items() if v is not None})

        def add_project_file(self, pid, path, name=""):
            fid = "f-" + path.replace("/", "_")[:20]
            self.files[fid] = {"project_id": pid, "path": path, "name": name}
            return fid

        def set_project_file_pinned(self, pid, fid, pinned):
            return True

    store = FakeStore()
    dp.configure(
        brain_root=lambda b: str(brain),
        get_sessions_store=lambda: store,
        sync_script=ROOT / "scripts" / "sync-drive-project.sh",
    )

    check("ascii_slug strips diacritics", dp._ascii_slug("Khoa học AI") == "khoa-hoc-ai")
    check("folder_id ok", dp._folder_id_ok("1NwpPUVxnGJfQER-5qKg0ejw7ry57pcGM"))
    check("folder_id reject short", not dp._folder_id_ok("abc"))

    try:
        dp.create_project(name="", brain=str(brain), drive_folder_id="1NwpPUVxnGJfQER-5qKg0ejw7ry57pcGM")
        check("reject empty name", False)
    except ValueError:
        check("reject empty name", True)

    item = dp.create_project(
        name="Giáo trình MKT",
        brain=str(brain),
        drive_folder_id="1NwpPUVxnGJfQER-5qKg0ejw7ry57pcGM",
        rclone_remote="gdrive",
    )
    check("create returns id", bool(item.get("id")))
    check("slug set", item.get("slug") == "giao-trinh-mkt")
    check("remote normalized", item.get("rclone_remote") == "gdrive:")
    check("chat project created", bool(item.get("chat_project_id")))
    check("readme scaffold", (brain / "sources/drive/giao-trinh-mkt/README.md").is_file())

    listed = dp.list_projects(str(brain))
    check("list one", len(listed) == 1)

    # Mirror without rclone: plant corpus files
    corpus = dp.corpus_dir(item)
    corpus.mkdir(parents=True, exist_ok=True)
    (corpus / "bai-1.txt").write_text("Nội dung bài 1 đầy đủ.\n", encoding="utf-8")
    (corpus / "sub").mkdir(exist_ok=True)
    (corpus / "sub" / "note.md").write_text("# Note\n\nChi tiết.\n", encoding="utf-8")
    stats = dp.mirror_corpus_to_sources(item)
    check("mirrored count", stats["mirrored"] >= 2)
    check("sources has md", (brain / "sources/drive/giao-trinh-mkt/sub/note.md").is_file())
    check("txt became md", (brain / "sources/drive/giao-trinh-mkt/bai-1.md").is_file())

    # Sync without rclone binary should fail cleanly
    # Temporarily pretend rclone missing by clearing PATH? Use run_rclone when no rclone.
    # If system has rclone, still ok to call with bad folder - we check error path via missing install mock:
    old_which = dp.shutil.which

    def no_rclone(cmd):
        if cmd == "rclone":
            return None
        return old_which(cmd)

    dp.shutil.which = no_rclone
    res = dp.sync_project(item["id"])
    dp.shutil.which = old_which
    check("sync without rclone fails", res.get("ok") is False)
    check("error mentions rclone", "rclone" in (res.get("error") or "").lower())

    got = dp.get_project(item["id"])
    check("last_sync_ok false stored", got.get("last_sync_ok") is False)

    dp.delete_project(item["id"])
    check("deleted", dp.get_project(item["id"]) is None)

    print(f"\n{ok} passed, {fail} failed")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
