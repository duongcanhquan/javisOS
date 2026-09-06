# Personal legal counsel on Javis

***English** · [Tiếng Việt](../28-phap-che-ca-nhan.md)*

Goal: Javis acts as **in-house legal counsel** — citing decrees, circulars, and laws you
already keep in your vault when you ask or when a project runs. **Not** a substitute for a lawyer.

## Three layers

| Layer | Role |
|---|---|
| **Google Drive** `Phap-che/{Area}/{Doc}/` | Original PDF/DOCX, versions, sharing |
| **Brain** `sources/phap-che/` → **wiki** | Extracted text + distilled knowledge, stable cites |
| **RAG sidecar** (optional) | Index a large PDF folder; tool `phap_che_search` also calls it |

Do **not** dump full statutes into `memory/MEMORY.md`.

## Phase A — usable without RAG

1. Create Drive folders under `Phap-che/...`.
2. Extract important texts → `sources/phap-che/<area>/YYYY-id-name.md` (README is seeded on brain scaffold).
3. Chat: ingest with **ingest-source**.
4. Enable skill **phap-che** or create the agent via **Workflows** → **Bộ Pháp chế** / `POST /studio/seed-phap-che`.
5. Projects: pin brief + related `.md` (pins do not accept PDF).

## Phase B — RAG sidecar

1. Install rclone; sync with `./scripts/sync-phap-che-drive.sh`.
2. Index the sync folder with RAG-Anything / LightRAG, or try the stub `scripts/phap_che_rag_sidecar_example.py`.
3. Expose `POST /retrieve` → set `JAVIS_PHAP_CHE_RAG_URL`.
4. Bundled plugin **phap-che**: tools `phap_che_search`, `phap_che_status`.

## Phase C — compare & web snapshot

- Skill **so-sanh-van-ban-phap-ly**: article matrix A vs B.
- Skill **snapshot-van-ban-web**: dated copy into `sources/phap-che`, then ingest.

See also: [13 - Second Brain](13-second-brain.md), [16 - .env](16-env-configuration.md).
