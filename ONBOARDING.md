# Codebase Onboarding — Javis OS

**Version:** 0.35.1 · **Product:** Self-hosted agentic AI + Second Brain (JARVIS-inspired, spelled **Javis**)

## Quick Start

1. Open folder `javis/` (workspace root is `JAVIS OS/javis`)
2. Windows: run `setup.bat` (creates `.venv`, installs deps, starts server)
3. Optional: copy `env.example` → `.env`
4. Open **http://localhost:7777** → **Models** → pick an engine
5. Later: `start-javis.bat` / stop: `stop-javis.bat`

Docker: `docker compose up -d` (image `ghcr.io/blogminhquy/javis-os`). Native Linux: `./install.sh`.

## Architecture

Javis is a **Python FastAPI “AI OS”** with a **vanilla HTML/JS dashboard** — not Next.js, Electron, or a JS monorepo.

| Path | Role |
|------|------|
| `server/` | FastAPI core: chat, engines, MCP hub, auth, bots, kanban, learn |
| `dashboard/` | Primary UI (Alpine.js, force-graph, xterm) |
| `cli/` | Thin HTTP client (`javis` command) |
| `brains/` | Markdown Second Brain vaults |
| `system/plugins/` | Bundled Python plugins |
| `system/mcp-catalog.json` | Connector templates (~27) |
| `docs/` | User + contributor docs |

**End-to-end flow:** User (Dashboard / Telegram / Zalo / CLI) → FastAPI (`main.py`) → Auth → ChatRuntime → Engine (Claude/Codex/API) → MCP Hub + plugins + brain files → Markdown memory / SQLite state.

Default port: **7777**.

## Data Models

No Postgres/MySQL/ORM. Persistence is **SQLite + JSON + Markdown**:

| Store | Purpose |
|-------|---------|
| `conversations.db` | Chat sessions + messages (FTS) |
| `kanban.sqlite3` | Autonomous task queue |
| `usage_index.db` / `usage.json` | Token/cost analytics |
| `memory_index.db` | Search index over `brains/*/memory/` |
| `runtime.db` | Adaptive context runtime |
| `settings.json` | Config + encrypted secrets |
| `mcp_servers.json`, `chatbots.json` | Connections / bots |
| `brains/<name>/` | Wiki, memory, skills, agents, loops, reminders |

Authoritative knowledge lives in **Markdown vaults**; DBs are runtime/derived indexes.

## API Reference

**Style:** REST (FastAPI) + WebSocket + SSE + MCP JSON-RPC.

| Channel | Path | Role |
|---------|------|------|
| Chat WS | `/ws` | Primary streaming chat |
| Terminal WS | `/ws/terminal` | Interactive shell |
| Graph WS | `/ws/graph` | Live knowledge graph |
| MCP Hub | `POST /hub/mcp` | Tools for engines (Bearer hub token) |
| CLI chat | `POST /chat`, `/chat/stream` | Sync / SSE turns |

~241 routes (see `tests/python/route_table.json`). Dashboard uses same-origin `fetch` + cookie; CLI uses Bearer API tokens.

## Authentication

**Custom single-admin gate** (not Auth.js/Clerk/Supabase):

- Username + PBKDF2 password; optional TOTP 2FA
- Cookie `javis_session` (30 days)
- API tokens `jvs_*` with scopes `full` | `chat`
- Localhost can run without password; public bind forces login
- LLM/API keys encrypted at rest via Fernet (`.secret_key`)

## Deployment

| Method | Notes |
|--------|-------|
| Windows scripts | `setup.bat`, `start-javis.bat` |
| Docker / GHCR | `docker-compose.yml`, Hostinger Traefik, Caddy HTTPS |
| Native | `install.sh` + systemd |
| CI/CD | `.github/workflows/ci.yml` + `docker-publish.yml` |

**Gotchas:** Voice needs HTTPS (or localhost); user plugins need `JAVIS_ENABLE_USER_PLUGINS=true`; don’t lose `.secret_key` with `settings.json`; FastAPI pins are brittle.

## Where to change features safely

Prefer extension points over editing huge `server/main.py`:

| Goal | Place |
|------|-------|
| New tools | `system/plugins/<slug>/` or user plugins (env unlock) |
| New connectors | `system/mcp-catalog.json` |
| Know-how (no code) | Brain `skills/*/SKILL.md` |
| Agents / loops / workflows | Markdown under `brains/<name>/` |
| New API | Module + `APIRouter` + `register(app)` |
| UI page | `dashboard/` + i18n JSON |
| Models | In-app **Models** / `engine.py`, `claude_cli.py`, … |

## Key Files to Know

- `server/main.py` — FastAPI app, mounts, WebSockets
- `server/config.py` — Settings, auth, paths
- `server/chat_runtime.py` — Chat job lifecycle
- `server/engine.py` / `claude_cli.py` — Model engines
- `server/mcp_hub.py` — Shared tool hub
- `server/plugins_host.py` — Plugin loader
- `dashboard/index.html` + `console.js` — UI shell
- `docs/dev/01-kien-truc.md` — Contributor architecture

## Mental model

Javis is an **orchestration layer**: swappable models + MCP Hub + Second Brain. Capability should go through **plugins, MCP catalog, and skills** — not hard-wiring a single model.
