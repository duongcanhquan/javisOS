# Codebase Onboarding — Javis OS

**Version:** see `VERSION` · **Product:** Self-hosted agentic AI + Second Brain (**Javis**)

## Quick Start

1. Open this repo root (`JAVIS OS/` - not a nested `javis/` folder).
2. **Packaged / non-dev:** Windows `1-Cai-dat.bat` · Mac `1-Cai-dat.command` → http://localhost:7777  
   Full guide: [HUONG-DAN-CAI-DAT-VA-SU-DUNG.md](HUONG-DAN-CAI-DAT-VA-SU-DUNG.md)
3. **Dev:** `.venv` + `pip install -r requirements.txt` → run server (or `setup.bat` / `./install.sh`).
4. Open **http://localhost:7777** → create admin → **Models** → pick an engine.
5. Later: `2-Bat-Javis.bat` / `2-Bat-Javis.command` (or `start-javis.bat` / stop scripts).

Docker: `docker compose up -d` (image `ghcr.io/duongcanhquan/javisos`). Hostinger HTTPS: `docker-compose.hostinger.yml`. Native Linux: `./install.sh`.

## Architecture

Javis is a **Python FastAPI “AI OS”** with a **vanilla HTML/JS dashboard** - not Next.js, Electron, or a JS monorepo.

| Path | Role |
|------|------|
| `server/` | FastAPI core: chat, engines, MCP hub, auth, bots, kanban, learn |
| `dashboard/` | Primary UI (Alpine.js, force-graph, xterm) |
| `cli/` | Thin HTTP client (`javis` command) |
| `brains/` | Markdown Second Brain vaults (per-user; do not ship personal vaults) |
| `.claude/skills/` | System skills (synced into every brain) |
| `system/agents/` · `system/workflows/` | Shared agents/workflows (synced; see `EXCLUDE-AGENTS.md`) |
| `system/plugins/` | Bundled Python plugins |
| `system/mcp-catalog.json` | Connector templates |
| `docs/` | User + contributor docs |

**End-to-end flow:** User (Dashboard / Telegram / Zalo / CLI) → FastAPI (`main.py`) → Auth → ChatRuntime → Engine (Claude/Codex/API/…) → MCP Hub + plugins + brain files → Markdown memory / SQLite state.

**Packaging rules:** Projects are per-brain. Skills/agents/workflows that are *shared* live under `.claude/skills` + `system/` and sync via `system_sync`. Connections and personal knowledge are never in the image.
