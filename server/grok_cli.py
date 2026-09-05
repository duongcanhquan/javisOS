"""Bß╗Ö n├úo thß╗⌐ 11: xAI Grok Build CLI (binary `grok`), chß║íy bß║▒ng G├ôI SuperGrok / X Premium+.

─Éß╗æi xß╗⌐ng vß╗¢i `GeminiCLI` v├á `CodexCLI`: Javis kh├┤ng giß╗» token cß╗ºa ai cß║ú, n├│ gß╗ìi ─æ├║ng binary
`grok` cß╗ºa m├íy v├á m╞░ß╗ún phi├¬n ─æ─âng nhß║¡p m├á ch├¡nh CLI ─æ├│ giß╗» trong `~/.grok/auth.json`.

**V├¼ sao module n├áy KH├öNG ch├⌐p khu├┤n `antigravity_cli.py`** - hai chß╗ù ─æau nhß║Ñt cß╗ºa `agy` ─æß╗üu
kh├┤ng c├│ ß╗ƒ ─æ├óy:

- Trß║íng th├íi ─æ─âng nhß║¡p nß║▒m trong FILE ─Éß╗îC ─É╞»ß╗óC (`~/.grok/auth.json`, quyß╗ün 0600), kh├┤ng phß║úi
  keyring cß╗ºa hß╗ç ─æiß╗üu h├ánh. N├¬n `auth_status()` ─æß╗ìc ─æ─⌐a, kh├┤ng phß║úi ─æß║╗ mß╗Öt tiß║┐n tr├¼nh mß╗ùi lß║ºn
  mß╗ƒ trang Models, v├á trang Models n├│i ─æ╞░ß╗úc sß╗▒ thß║¡t thay v├¼ "h├úy tß╗▒ g├╡ lß╗çnh rß╗ôi bß║Ñm kiß╗âm tra".
- Cß║Ñu h├¼nh MCP ─æß╗ìc theo TH╞» Mß╗ñC L├ÇM VIß╗åC (`<cwd>/.grok/config.toml`), n├¬n ghi v├áo trong brain
  l├á mß╗ùi brain mß╗Öt hub ri├¬ng, kh├┤ng giß║½m l├¬n cß║Ñu h├¼nh c├í nh├ón ß╗ƒ `~/.grok/config.toml` v├á kh├┤ng
  brain nß╗ì ─æß╗ìc header brain kia. Giß╗æng hß╗çt `<brain>/.gemini/settings.json` b├¬n Gemini CLI.

V├á n├│ c├│ th├¬m mß╗Öt thß╗⌐ Antigravity kh├┤ng c├│: `grok login --device-auth` in ra URL + m├ú, tß╗⌐c
─É─éNG NHß║¼P ─É╞»ß╗óC Tß╗¬ VPS qua n├║t bß║Ñm tr├¬n dashboard, kh├┤ng bß║»t ng╞░ß╗¥i d├╣ng mß╗ƒ terminal.

**GIß╗« cß╗ºa `antigravity_cli.py`: `co_co()` - d├▓ cß╗¥ tr╞░ß╗¢c khi truyß╗ün.** Bß║ún CLI n├áy c├▓n rß║Ñt mß╗¢i
v├á ─æß╗òi cß╗¥ li├¬n tß╗Ñc; truyß╗ün mß╗Öt cß╗¥ n├│ ch╞░a c├│ l├á n├│ tho├ít ngay vß╗¢i "unknown flag", hß╗Ång cß║ú l╞░ß╗út
chat chß╗ë v├¼ mß╗Öt tuß╗│ chß╗ìn phß╗Ñ. Hß╗Åi `--help` tr╞░ß╗¢c rß╗ôi mß╗¢i truyß╗ün th├¼ bß║ún c┼⌐ vß║½n chß║íy, chß╗ë mß║Ñt
t├¡nh n─âng. Mß╗îI cß╗¥ d╞░ß╗¢i ─æ├óy ─æß╗üu ─æi qua `co_co()`, kh├┤ng c├│ ngoß║íi lß╗ç.

**S╞á ─Éß╗Æ Sß╗░ KIß╗åN ─É├â ─ÉO THß║¼T (29/08/2026), ─æß╗½ng ─æo├ín lß║íi.** Bß╗æn bß║ún v├í 0.50.2 tß╗¢i 0.50.5 ─æi
v├▓ng quanh ─æ├║ng chß╗ù n├áy chß╗ë v├¼ n├│ ─æ╞░ß╗úc ─ÉO├üN tß╗½ t├ái liß╗çu chß╗⌐ ch╞░a ai chß║íy mß╗Öt l╞░ß╗út. Nguy├¬n v─ân
`grok -p "ch├áo" --output-format streaming-json | tail -5` tr├¬n m├íy ng╞░ß╗¥i d├╣ng:

    {"type":"text","data":" nay"}
    {"type":"text","data":"?"}
    {"type":"available_commands","tools":[...],"commands":[...]}
    {"type":"usage","usage":{"input_tokens":9028,"output_tokens":54,
                             "cache_read_input_tokens":4352,"reasoning_tokens":32},
                    "signature":"..."}
    {"type":"end","stopReason":"end_turn","sessionId":"01a04b69-...","usage":{...,
                  "total_tokens":13434},"num_turns":1,"total_cost_usd":0.020556}

Ba chß╗ù lß╗çch so vß╗¢i bß║úng ─æo├ín, ghi lß║íi ─æß╗â kh├┤ng ai mß║»c lß║íi:

- Chß╗» nß║▒m ß╗ƒ kho├í **`data`**, kh├┤ng phß║úi `text`. ─É├óy l├á gß╗æc rß╗à cß╗ºa "kh├┤ng trß║ú vß╗ü nß╗Öi dung n├áo":
  l╞░ß╗út chß║íy ─æ├║ng, model trß║ú lß╗¥i ─æ├║ng, m├á Javis gom ─æ╞░ß╗úc to├án chuß╗ùi rß╗ùng.
- Sß╗▒ kiß╗çn `usage` **bß╗ìc** sß╗æ liß╗çu trong kho├í `usage`, v├á t├¬n kho├í l├á `input_tokens` /
  `output_tokens` / `cache_read_input_tokens`.
- C├│ loß║íi `available_commands` (bß║úng khai b├ío tool, xuß║Ñt hiß╗çn ß╗ƒ Cß║ó ─æß║ºu lß║½n cuß╗æi luß╗ông) kh├┤ng
  hß╗ü nß║▒m trong t├ái liß╗çu. N├│ KH├öNG phß║úi c├óu trß║ú lß╗¥i - xem `_LOAI_KHONG_PHAI_TRA_LOI`.

Mß║½u v├áng n├áy nß║▒m trong `tests/python/test_grok_cli.py` mß╗Ñc 12; sß╗¡a phß║ºn dß╗ïch sß╗▒ kiß╗çn th├¼ chß║íy
n├│ tr╞░ß╗¢c.

Nhß╗»ng g├¼ c├▓n lß║íi ─æß╗ìc tß╗½ t├ái liß╗çu ch├¡nh chß╗º (`xai-org/grok-build`, user-guide) v├á Vß║¬N PHß║óI ─ÉO
tr├¬n m├íy thß║¡t tr╞░ß╗¢c khi tin - xem `docs/dev/2026-08-grok-cli.md`:

- `-p/--single <PROMPT>` chß║íy headless, `--prompt-file <PATH>` ─æß╗ìc prompt tß╗½ file.
- `--output-format json` trß║ú mß╗Öt cß╗Ñc c├│ `text`/`sessionId`/`usage`.
- Phi├¬n: `-s/--session-id <ID>` mß╗ƒ mß╗¢i vß╗¢i id tß╗▒ cß║Ñp, `-r/--resume <ID>` nß╗æi lß║íi,
  `-c/--continue` nß╗æi phi├¬n gß║ºn nhß║Ñt cß╗ºa th╞░ mß╗Ñc.
- Quyß╗ün: `--permission-mode bypassPermissions|defaultMode`, `--allow`/`--deny` theo luß║¡t
  `Bash(...)`, `Write(...)`, `Edit(...)`, `MCPTool(...)`; `--max-turns N`.
- MCP: `[mcp_servers.<ten>]` trong `config.toml`, entry HTTP d├╣ng kho├í `url` + `headers`.
"""
from __future__ import annotations

import asyncio
import errno
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from pathlib import Path
from typing import AsyncIterator, Optional

from claude_cli import _home_dir, _no_window, tim_binary

try:                       # Python 3.11+ c├│ sß║╡n; ─æß╗ìc TOML, KH├öNG ghi ─æ╞░ß╗úc.
    import tomllib
except ModuleNotFoundError:   # pragma: no cover - Javis y├¬u cß║ºu 3.11, ─æ├óy chß╗ë l├á l╞░ß╗¢i ─æß╗í
    tomllib = None            # type: ignore[assignment]

# Model Dß╗░ PH├ÆNG, chß╗ë d├╣ng khi ch╞░a hß╗Åi ─æ╞░ß╗úc danh s├ích live tß╗½ CLI. Cß╗æ ├╜ ─æß╗â ngß║»n v├á cß╗æ ├╜ KH├öNG
# ─æ╞░a v├áo `PROVIDER_DEFS`: b├ái hß╗ìc cß╗ºa `agy` l├á bß║úng model ch├⌐p tay th├¼ sai lß║╖ng lß║╜, m├á t├¬n
# model cß╗ºa xAI ─æß╗òi li├¬n tß╗Ñc.
MODELS_DU_PHONG = ["grok-4.6", "grok-4.5"]

LENH_CAI = "curl -fsSL https://x.ai/cli/install.sh | bash"
LENH_CAI_WIN = "irm https://x.ai/cli/install.ps1 | iex"

# Mß╗⌐c quyß╗ün Javis -> luß║¡t chß║╖n cß╗ºa Grok. Xem `permission_cho_mode`.
#
# T├èN TOOL ß╗₧ ─É├éY PHß║óI L├Ç TOOL Cß╗ªA GROK, KH├öNG PHß║óI Cß╗ªA CLAUDE CODE. Bß║ún tr╞░ß╗¢c ch├⌐p nguy├¬n
# danh s├ích cß╗ºa Claude v├áo ─æ├óy, k├¿m `NotebookEdit(*)` - mß╗Öt tool Grok kh├┤ng c├│. Grok CLI kh├┤ng
# bß╗Å qua t├¬n lß║í m├á Tß╗¬ CHß╗ÉI cß║ú l╞░ß╗út gß╗ìi: "unsupported tool prefix: NotebookEdit".
#
# Hß║¡u quß║ú lß║»t l├⌐o ─æ├║ng kiß╗âu kh├│ truy: chat THß║¼T cß╗ºa ng╞░ß╗¥i d├╣ng chß║íy ß╗ƒ mß╗⌐c full, m├á mß╗⌐c full
# kh├┤ng truyß╗ün cß╗¥ --deny n├áo, n├¬n chat vß║½n chß║íy ngon. Chß╗ë l╞░ß╗út chat thß╗¡ cß╗ºa thß║╗ Models l├á
# chß║íy ß╗ƒ mß╗⌐c suggest - tß╗⌐c l╞░ß╗út DUY NHß║ñT ─æß╗Ñng v├áo danh s├ích n├áy - n├¬n thß║╗ ─æß╗Å l├¿ trong khi mß╗ìi
# thß╗⌐ kh├íc b├¼nh th╞░ß╗¥ng. Ng╞░ß╗¥i d├╣ng b├ío 02/09: "vß║½n chß║íy ├áo ├áo m├á tß║íi hiß╗çn lß╗ùi ─æ├│ t├¡".
#
# Bß╗Å NotebookEdit KH├öNG nß╗¢i lß╗Ång g├¼: Grok kh├┤ng c├│ tool sß╗¡a notebook th├¼ c┼⌐ng chß║│ng c├│ g├¼ ─æß╗â
# chß║╖n. Th├¬m t├¬n mß╗¢i v├áo ─æ├óy phß║úi kiß╗âm l├á Grok thß║¡t sß╗▒ c├│ tool ─æ├│ (test_grok_cli canh).
_LUAT_CHAN = {
    # suggest: CHß╗ê ─Éß╗îC. Chß║╖n cß║ú ghi file lß║½n lß╗çnh m├íy.
    "suggest": ("Write(*)", "Edit(*)", "Bash(*)"),
    # auto: ghi file nh├íp ─æ╞░ß╗úc, KH├öNG chß║íy lß╗çnh m├íy.
    "auto": ("Bash(*)",),
    # full: kh├┤ng chß║╖n g├¼ ß╗ƒ tß║ºng CLI.
    "full": (),
}


def _grok_home() -> Path:
    """Th╞░ mß╗Ñc cß║Ñu h├¼nh cß╗ºa `grok`. GROK_HOME thß║»ng, ─æ├║ng nh╞░ CLI xß╗¡ l├╜."""
    env = (os.environ.get("GROK_HOME") or "").strip()
    if env:
        return Path(env).expanduser()
    return _home_dir() / ".grok"


def _doc_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def find_grok_cli() -> Optional[str]:
    """T├¼m binary `grok`. Cß╗¡a tho├ít JAVIS_GROK_BIN cho m├íy c├ái chß╗ù lß║í."""
    envp = (os.environ.get("JAVIS_GROK_BIN") or "").strip()
    if envp:
        try:
            if Path(envp).exists():
                return envp
        except Exception:
            pass
    cli = tim_binary("grok")
    if cli:
        return cli
    home = _home_dir()
    # Installer ch├¡nh chß╗º thß║ú binary v├áo ~/.local/bin (Unix) hoß║╖c %LOCALAPPDATA% (Windows).
    for p in (home / ".local" / "bin" / "grok",
              home / ".grok" / "bin" / "grok",
              Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "grok" / "grok.exe"):
        try:
            if p.exists():
                return str(p)
        except Exception:
            pass
    return None


def lenh_cai() -> str:
    return LENH_CAI_WIN if os.name == "nt" else LENH_CAI


def _moi_truong() -> dict:
    """M├┤i tr╞░ß╗¥ng cho mß╗Öt l╞░ß╗út chß║íy `grok`: kß║┐ thß╗½a cß╗ºa server, tß║»t bß╗Ö tß╗▒ cß║¡p nhß║¡t.

    V├¼ sao phß║úi tß║»t: Javis chß║íy `grok` headless tr├¬n VPS v├á trong container. Bß╗Ö tß╗▒ cß║¡p nhß║¡t cß╗ºa
    CLI c├│ thß╗â xen v├áo giß╗»a l╞░ß╗út - tß║úi bß║ún mß╗¢i, ghi v├áo chß╗ù chß╗ë ─æß╗ìc, hoß║╖c in th├¬m chß╗» v├áo
    stdout l├ám hß╗Ång d├▓ng NDJSON ─æang ─æß╗ìc. T├ái liß╗çu ch├¡nh chß╗º khuy├¬n ─æ├║ng ─æiß╗üu n├áy cho container.

    ─Éß║╖t Cß║ó biß║┐n m├┤i tr╞░ß╗¥ng lß║½n cß╗¥ `--no-auto-update` (xem `_build_args`) l├á c├│ chß╗º ├╜, kh├┤ng
    phß║úi thß╗½a: cß╗¥ ─æi qua `co_co()` n├¬n bß║ún CLI ch╞░a khai n├│ th├¼ kh├┤ng ─æ╞░ß╗úc truyß╗ün, c├▓n biß║┐n m├┤i
    tr╞░ß╗¥ng th├¼ bß║ún n├áo c┼⌐ng nhß║¡n hoß║╖c lß║╖ng lß║╜ bß╗Å qua - kh├┤ng bao giß╗¥ l├ám CLI tho├ít lß╗ùi. Hai lß╗¢p
    phß╗º cho nhau.
    """
    env = dict(os.environ)
    env.setdefault("GROK_DISABLE_AUTOUPDATER", "1")
    return env


# ---------------------------------------------------------------------------
# D├▓ cß╗¥: hß╗Åi `--help` tr╞░ß╗¢c, ─æß╗½ng ─æo├ín
# ---------------------------------------------------------------------------
_HELP_CACHE: dict = {"path": None, "text": "", "ts": 0.0}
_HELP_TTL = 300.0     # 5 ph├║t: mß╗Öt phi├¬n chat kh├┤ng ─æß║╗ tiß║┐n tr├¼nh mß╗ùi l╞░ß╗út, m├á n├óng cß║Ñp bß║ún
                      # CLI xong c┼⌐ng kh├┤ng phß║úi khß╗ƒi ─æß╗Öng lß║íi Javis mß╗¢i nhß║¡n cß╗¥ mß╗¢i.
_HELP_TTL_LOI = 120.0  # kß║┐t quß║ú Rß╗ûNG c┼⌐ng nhß╗¢ (TTL ngß║»n h╞ín): binary hß╗Ång m├á chß║íy lß║íi `--help`
                       # 20s mß╗ùi l╞░ß╗út l├á biß║┐n mß╗Öt CLI hß╗Ång th├ánh cß║ú app chß║¡m theo.


def _help_text() -> str:
    """Nß╗Öi dung `grok --help`, nhß╗¢ trong RAM. Rß╗ùng nß║┐u kh├┤ng chß║íy ─æ╞░ß╗úc."""
    cli = find_grok_cli()
    if not cli:
        return ""
    now = time.time()
    if _HELP_CACHE["path"] == cli and now - _HELP_CACHE["ts"] < (
            _HELP_TTL if _HELP_CACHE["text"] else _HELP_TTL_LOI):
        return _HELP_CACHE["text"]
    try:
        # stdin=DEVNULL: CLI n├áo r╞íi v├áo m├án hß╗Åi t╞░╞íng t├íc c┼⌐ng tho├ít ngay thay v├¼ ngß╗ôi chß╗¥
        # b├án ph├¡m v├┤ h├¼nh ─ân trß╗ìn timeout (c├╣ng b├ái hß╗ìc vß╗¢i `agy`, 2026-08-30).
        r = subprocess.run([cli, "--help"], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=20, creationflags=_no_window(),
                           env=_moi_truong(), stdin=subprocess.DEVNULL)
        txt = (r.stdout or "") + "\n" + (r.stderr or "")
    except Exception:
        txt = ""
    _HELP_CACHE.update(path=cli, text=txt, ts=now)
    return txt


def co_co(*ten_co: str) -> bool:
    """Binary tr├¬n m├íy C├ô khai cß╗¥ n├áy kh├┤ng (`--help` nhß║»c tß╗¢i n├│).

    Fail-closed: kh├┤ng ─æß╗ìc ─æ╞░ß╗úc `--help` th├¼ coi nh╞░ KH├öNG c├│ cß╗¥. Chß║íy thiß║┐u mß╗Öt tuß╗│ chß╗ìn phß╗Ñ
    c├▓n h╞ín tho├ít ngay v├¼ "unknown flag".
    """
    txt = _help_text()
    if not txt:
        return False
    return any(c in txt for c in ten_co)


# ---- Mß╗⌐c effort: chß╗ë truyß╗ün khi CH├ìNH `--help` khai cß║ú cß╗¥ Lß║¬N gi├í trß╗ï ----
#
# C├╣ng tinh thß║ºn `co_co` nh╞░ng chß║╖t h╞ín mß╗Öt nß║Ñc, v├¼ ß╗ƒ ─æ├óy sai kh├┤ng chß╗ë mß║Ñt mß╗Öt tuß╗│ chß╗ìn: mß╗Öt
# cß╗¥ `--effort` c├│ thß║¡t m├á chß╗ë nhß║¡n `low|high` th├¼ gß╗¡i "medium" l├á CLI tho├ít ngay, hß╗Ång trß╗ìn
# l╞░ß╗út chat. N├¬n phß║úi thß║Ñy T├èN Cß╗£ trong help, v├á thß║Ñy Cß║ó GI├ü TRß╗è ─æß╗ïnh gß╗¡i, mß╗¢i truyß╗ün.
#
# Hß╗ç quß║ú th├ánh thß║¡t: bß║ún CLI n├áo kh├┤ng liß╗çt k├¬ gi├í trß╗ï trong help th├¼ Javis kh├┤ng truyß╗ün g├¼
# cß║ú, v├á ─æß╗Ö s├óu suy ngh─⌐ r╞íi vß╗ü c├óu nhß║»c trong prompt. ─É├│ l├á chß╗º ├╜ - th├á mß║Ñt mß╗Öt tuß╗│ chß╗ìn c├▓n
# h╞ín ─æo├ín mß╗Öt gi├í trß╗ï rß╗ôi l├ám hß╗Ång l╞░ß╗út chat cß╗ºa ng╞░ß╗¥i d├╣ng. Khi CLI khai r├╡ ra th├¼ phß║ºn n├áy
# tß╗▒ chß║íy, khß╗Åi sß╗¡a code.
_CO_EFFORT = ("--effort", "--reasoning-effort")


def co_effort(muc: Optional[str]) -> list:
    """['--effort', '<muc>'] nß║┐u bß║ún CLI n├áy khai ─æß╗º cß║ú hai, kh├┤ng th├¼ [] (kh├┤ng truyß╗ün g├¼)."""
    if not muc:
        return []
    txt = _help_text()
    if not txt or not re.search(r"\b" + re.escape(str(muc)) + r"\b", txt):
        return []
    for co in _CO_EFFORT:
        if co in txt:
            return [co, str(muc)]
    return []


def phien_moi() -> str:
    return str(uuid.uuid4())


def permission_cho_mode(mode: Optional[str]) -> list:
    """Mß╗⌐c quyß╗ün cß╗ºa Javis -> cß╗¥ quyß╗ün cß╗ºa Grok. Gi├í trß╗ï lß║í vß╗ü nß║Ñc CHß║╢T NHß║ñT.

    Fail-closed cß╗æ ├╜: mß╗Öt chuß╗ùi mode g├╡ sai kh├┤ng ─æ╞░ß╗úc
    ph├⌐p biß║┐n th├ánh to├án quyß╗ün ghi file v├á chß║íy lß╗çnh m├íy.

    H├ÇNG R├ÇO THß║¼T nß║▒m ß╗ƒ header `X-Javis-Mode` m├á MCP hub ├íp cho mß╗ìi tool ─æi qua n├│ - c├íi ─æ├│
    chß║╖n ─æ╞░ß╗úc cß║ú tool cß╗ºa MCP ─æ├ú ─æß║Ñu. Cß╗¥ ß╗ƒ ─æ├óy chß╗ë l├á lß╗¢p thß╗⌐ hai, chß║╖n tool NATIVE cß╗ºa ch├¡nh
    Grok (Bash/Write/Edit), thß╗⌐ hub kh├┤ng nh├¼n thß║Ñy.
    """
    m = str(mode or "").strip().lower()
    luat = _LUAT_CHAN.get(m)
    if luat is None:            # mode lß║í -> nß║Ñc chß║╖t nhß║Ñt
        luat = _LUAT_CHAN["suggest"]
        m = "suggest"
    args: list = []
    if co_co("--permission-mode"):
        # headless m├á ─æß╗â CLI dß╗½ng lß║íi hß╗Åi duyß╗çt l├á treo tß╗¢i hß║┐t giß╗¥, n├¬n lu├┤n ─æß║╖t t╞░ß╗¥ng minh.
        args += ["--permission-mode", "bypassPermissions"]
    if co_co("--deny"):
        for r in luat:
            args += ["--deny", r]
    return args


# ---------------------------------------------------------------------------
# TOML tß╗æi thiß╗âu: ─æß╗º ─æß╗â round-trip `config.toml` cß╗ºa Grok
# ---------------------------------------------------------------------------
def _toml_gia_tri(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return json.dumps(v)
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(_toml_gia_tri(x) for x in v) + "]"
    return json.dumps(str(v), ensure_ascii=False)   # JSON string escape == TOML basic string


def _toml_khoa(k: str) -> str:
    """Kho├í TOML: ─æß╗â trß║ºn nß║┐u hß╗úp lß╗ç, quote nß║┐u kh├┤ng.

    Bare key cß╗ºa TOML nhß║¡n A-Za-z0-9_- n├¬n `mcp_servers`, `javis` lß║½n `X-Javis-Mode` ─æß╗üu ─æß╗â
    trß║ºn ─æ╞░ß╗úc. Quote hß║┐t th├¼ vß║½n ─É├ÜNG nh╞░ng ra mß╗Öt file ─æß║ºy dß║Ñu nh├íy m├á ng╞░ß╗¥i mß╗ƒ l├¬n ─æß╗ìc phß║úi
    dß╗Ñi mß║»t - file n├áy nß║▒m trong brain, ng╞░ß╗¥i d├╣ng c├│ mß╗ƒ ra xem.
    """
    k = str(k)
    if k and all(c.isascii() and (c.isalnum() or c in "_-") for c in k):
        return k
    return json.dumps(k, ensure_ascii=False)


def _toml_dump(d: dict, duong: tuple = ()) -> str:
    """Serializer TOML tß╗æi thiß╗âu: str/bool/sß╗æ/list/dict lß╗ông nhau.

    V├¼ sao tß╗▒ viß║┐t thay v├¼ th├¬m `tomli-w` v├áo requirements: repo cß╗æ ├╜ giß╗» danh s├ích phß╗Ñ thuß╗Öc
    gß╗ìn (xem l├╜ do chß╗ìn `segno` trong requirements.txt), m├á thß╗⌐ cß║ºn ghi ß╗ƒ ─æ├óy l├á ─æ├║ng mß╗Öt bß║úng
    hai tß║ºng. `tomllib` cß╗ºa stdlib chß╗ë ─Éß╗îC ─æ╞░ß╗úc, n├¬n phß║ºn ghi phß║úi tß╗▒ lo.

    Hß║áN CHß║╛ ─É├â BIß║╛T: round-trip qua ─æ├óy l├ám Mß║ñT CH├Ü TH├ìCH trong file. Chß║Ñp nhß║¡n ─æ╞░ß╗úc v├¼ file
    n├áy nß║▒m trong `<brain>/.grok/` - th╞░ mß╗Ñc do ch├¡nh Javis dß╗▒ng trong brain, kh├┤ng phß║úi
    `~/.grok/config.toml` c├í nh├ón cß╗ºa ng╞░ß╗¥i d├╣ng.
    """
    dong: list = []
    bang_con: list = []
    for k, v in d.items():
        if isinstance(v, dict):
            bang_con.append((k, v))
        else:
            dong.append(f"{_toml_khoa(k)} = {_toml_gia_tri(v)}")
    ra = ""
    if duong and dong:
        ra += "[" + ".".join(_toml_khoa(x) for x in duong) + "]\n"
    ra += "\n".join(dong)
    if dong:
        ra += "\n"
    for k, v in bang_con:
        con = _toml_dump(v, duong + (k,))
        if con.strip():
            ra += ("\n" if ra.strip() else "") + con
        else:
            ra += ("\n" if ra.strip() else "") + "[" + ".".join(
                _toml_khoa(x) for x in duong + (k,)) + "]\n"
    return ra


def _doc_toml(p: Path) -> dict:
    """─Éß╗ìc TOML, KH├öNG ph├ón biß╗çt ─æ╞░ß╗úc 'kh├┤ng c├│ file' vß╗¢i 'file hß╗Ång'. Chß╗ë d├╣ng khi ─æß╗ìc hß╗Ång
    c┼⌐ng kh├┤ng sao (liß╗çt k├¬ model, soi trß║íng th├íi). Chß╗ù n├áo sß║»p GHI ─É├ê th├¼ d├╣ng `_doc_toml_ky`."""
    ok, d = _doc_toml_ky(p)
    return d if ok else {}


def _doc_toml_ky(p: Path) -> tuple:
    """(─æß╗ìc_─æ╞░ß╗úc, dict). Ph├ón biß╗çt ba ca, v├á sß╗▒ ph├ón biß╗çt n├áy KH├öNG phß║úi chuyß╗çn l├ám m├áu.

    File ch╞░a c├│ ΓåÆ (True, {}): ghi mß╗¢i l├á ─æ├║ng.
    File c├│ v├á parse ─æ╞░ß╗úc ΓåÆ (True, nß╗Öi dung): ghi ─æ├¿ phß║ºn cß╗ºa m├¼nh, giß╗» phß║ºn c├▓n lß║íi.
    File c├│ m├á parse KH├öNG ─æ╞░ß╗úc ΓåÆ (False, {}): tuyß╗çt ─æß╗æi KH├öNG ─æ╞░ß╗úc ghi ─æ├¿.

    Ca thß╗⌐ ba l├á chß╗ù su├╜t mß║Ñt dß╗» liß╗çu: gß╗Öp n├│ v├áo ca ─æß║ºu (trß║ú `{}` rß╗ôi ghi tiß║┐p) l├á mß╗ùi lß║ºn
    Javis chß║ím v├áo mß╗Öt `config.toml` g├╡ sai mß╗Öt dß║Ñu ngoß║╖c - hoß║╖c d├╣ng c├║ ph├íp m├á `tomllib` cß╗ºa
    Python ch╞░a biß║┐t - th├¼ to├án bß╗Ö cß║Ñu h├¼nh Grok cß╗ºa ng╞░ß╗¥i d├╣ng trong brain ─æ├│ bß╗ï xo├í sß║ích,
    kh├┤ng mß╗Öt c├óu lß╗ùi. ─É├óy ─æ├║ng l├á hß║íng lß╗ùi im lß║╖ng m├á module n├áy viß║┐t ra ─æß╗â tr├ính.
    """
    try:
        if not p.exists():
            return True, {}
    except Exception:
        return False, {}
    if tomllib is None:      # pragma: no cover - Javis y├¬u cß║ºu Python 3.11
        return False, {}
    try:
        with open(p, "rb") as f:
            d = tomllib.load(f)
        return True, (d if isinstance(d, dict) else {})
    except Exception as e:
        print(f"[grok mcp settings] `{p}` kh├┤ng ─æß╗ìc ─æ╞░ß╗úc, KH├öNG ghi ─æ├¿: {e}", file=sys.stderr)
        return False, {}


# ---------------------------------------------------------------------------
# MCP: ghi hub cß╗ºa Javis v├áo `<brain>/.grok/config.toml`
# ---------------------------------------------------------------------------
def hub_entry(url: str, headers: Optional[dict] = None) -> dict:
    """H├¼nh dß║íng entry MCP HTTP cß╗ºa Grok.

    ─Éß╗â h├¼nh dß║íng entry TRONG module engine chß╗⌐ kh├┤ng viß║┐t tay ß╗ƒ `main.py` l├á b├ái hß╗ìc ─æß║»t cß╗ºa
    `agy`: n├│ ─æß╗ìc kho├í `serverUrl`, c├▓n `httpUrl` (kho├í cß╗ºa Gemini CLI) bß╗ï bß╗Å qua kh├┤ng mß╗Öt
    tiß║┐ng ─æß╗Öng, v├á ─æ├│ l├á thß╗⌐ l├ám bß╗Ö n├úo ─æ├│ chß║íy mß║Ñy bß║ún m├á kh├┤ng c├│ lß║Ñy mß╗Öt tool n├áo cß╗ºa Javis.
    Grok d├╣ng kho├í `url`, kh├íc cß║ú hai. Giß╗» ß╗ƒ ─æ├óy ─æß╗â n├│ kh├┤ng tr├┤i theo file n├áo kh├íc.
    """
    e: dict = {"url": url}
    if headers:
        e["headers"] = dict(headers)
    return e


def mcp_config_path(vault_root) -> Path:
    return Path(vault_root).expanduser() / ".grok" / "config.toml"


def ghi_mcp_settings(vault_root, hub: Optional[dict]) -> Optional[str]:
    """Ghi `<vault>/.grok/config.toml` vß╗¢i ─æ├║ng mß╗Öt entry MCP trß╗Å vß╗ü hub Javis.

    V├¼ sao ghi v├áo brain chß╗⌐ kh├┤ng v├áo `~/.grok`: file HOME l├á cß╗ºa ng╞░ß╗¥i d├╣ng v├á d├╣ng chung cho
    mß╗ìi thß╗⌐ hß╗ì chß║íy bß║▒ng `grok`; ─æ├¿ l├¬n ─æ├│ l├á Javis giß║½m v├áo cß║Ñu h├¼nh c├í nh├ón, v├á nhiß╗üu brain
    th├¼ brain nß╗ì ─æß╗ìc header brain kia. Grok ─æß╗ìc cß║Ñu h├¼nh theo th╞░ mß╗Ñc l├ám viß╗çc, m├á Javis lu├┤n
    chß║íy n├│ vß╗¢i cwd = gß╗æc brain, n├¬n ─æ├óy vß╗½a ─æ├║ng chß╗ù vß╗½a c├┤ lß║¡p sß║╡n tß╗½ng brain.

    `hub=None` (ch╞░a bß║¡t hub) ΓåÆ Gß╗á entry javis nß║┐u c├│, giß╗» nguy├¬n phß║ºn c├▓n lß║íi cß╗ºa file.
    Trß║ú ─æ╞░ß╗¥ng dß║½n file ─æ├ú ghi, hoß║╖c None nß║┐u kh├┤ng ghi ─æ╞░ß╗úc.
    """
    try:
        p = mcp_config_path(vault_root)
        doc_duoc, cu = _doc_toml_ky(p)
        if not doc_duoc:
            # Th├á chß║íy KH├öNG c├│ tool cß╗ºa Javis c├▓n h╞ín xo├í cß║Ñu h├¼nh cß╗ºa ng╞░ß╗¥i d├╣ng. Lß╗ùi ─æ├ú in
            # ra stderr ß╗ƒ `_doc_toml_ky`; `trang_thai_mcp` sß║╜ b├ío `co_javis=False` n├¬n n├║t
            # "Kiß╗âm tra lß║íi" tr├¬n trang Models n├│i ─æ╞░ß╗úc l├á hub ch╞░a v├áo.
            return None
        servers = cu.get("mcp_servers")
        if not isinstance(servers, dict):
            servers = {}
        if hub:
            servers["javis"] = hub
        else:
            servers.pop("javis", None)
        if servers:
            cu["mcp_servers"] = servers
        else:
            cu.pop("mcp_servers", None)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(_toml_dump(cu), encoding="utf-8")
        try:
            os.chmod(p, 0o600)   # chß╗⌐a hub token
        except Exception:
            pass
        return str(p)
    except Exception as e:
        print(f"[grok mcp settings] {e}", file=sys.stderr)
        return None


def trang_thai_mcp(vault_root) -> dict:
    """─Éß╗îC Lß║áI ch├¡nh file vß╗½a ghi ─æß╗â trang Models n├│i ─æ╞░ß╗úc sß╗▒ thß║¡t.

    B├ái hß╗ìc cß╗ºa `agy` (0.43.0): cß║Ñu h├¼nh ghi th├ánh c├┤ng nh╞░ng SAI CHß╗û hoß║╖c SAI KHO├ü th├¼ CLI
    chß║íy tr╞ín tru m├á kh├┤ng c├│ lß║Ñy mß╗Öt tool n├áo cß╗ºa Javis, v├á kh├┤ng ß╗ƒ ─æ├óu c├│ mß╗Öt c├óu lß╗ùi ─æß╗â lß║ºn
    ra. "─É├ú ghi xong" kh├┤ng phß║úi bß║▒ng chß╗⌐ng; ─æß╗ìc lß║íi mß╗¢i l├á.
    """
    p = mcp_config_path(vault_root)
    ra = {"file": str(p), "ton_tai": False, "co_javis": False, "url": "", "so_header": 0}
    try:
        ra["ton_tai"] = p.exists()
    except Exception:
        return ra
    if not ra["ton_tai"]:
        return ra
    d = _doc_toml(p)
    e = ((d.get("mcp_servers") or {}) or {}).get("javis")
    if isinstance(e, dict):
        ra["co_javis"] = True
        ra["url"] = str(e.get("url") or "")
        h = e.get("headers")
        ra["so_header"] = len(h) if isinstance(h, dict) else 0
    return ra


# ---------------------------------------------------------------------------
# ─É─âng nhß║¡p
# ---------------------------------------------------------------------------
# T├¬n tr╞░ß╗¥ng b├¬n trong `auth.json` KH├öNG ─æ╞░ß╗úc xAI t├ái liß╗çu ho├í, v├á bß║ún 0.50.0 ─æ├ú ─æo├ín sai mß╗Öt
# lß║ºn: n├│ ─æ├▓i `access_token` hoß║╖c `refresh_token` nß║▒m ngay Tß║ªNG CAO NHß║ñT. File thß║¡t lß╗ông token
# s├óu h╞ín (hoß║╖c gß╗ìi t├¬n kh├íc) l├á Javis b├ío "ch╞░a ─æ─âng nhß║¡p" v─⌐nh viß╗àn d├╣ ng╞░ß╗¥i d├╣ng ─æ├ú bß║Ñm
# x├íc nhß║¡n xong xu├┤i tr├¬n accounts.x.ai - ─æ├║ng lß╗ùi ng╞░ß╗¥i d├╣ng b├ío ng├áy 28/08/2026.
#
# N├¬n ─æß╗ìc theo H├îNH Dß║áNG, kh├┤ng theo mß╗Öt s╞í ─æß╗ô ─æo├ín tr╞░ß╗¢c: ─æi khß║»p c├óy JSON t├¼m mß╗Öt kho├í n├áo
# ─æ├│ nghe nh╞░ token, c├│ gi├í trß╗ï chuß╗ùi ─æß╗º d├ái. Sai h╞░ß╗¢ng n├áy chß╗ë l├ám Javis dß╗à t├¡nh h╞ín vß╗¢i mß╗Öt
# file r├íc; sai h╞░ß╗¢ng kia l├ám ng╞░ß╗¥i d├╣ng kh├┤ng ─æ─âng nhß║¡p ─æ╞░ß╗úc v├á kh├┤ng hiß╗âu v├¼ sao.
_KHOA_TOKEN = ("access_token", "accesstoken", "refresh_token", "refreshtoken", "id_token",
               "idtoken", "session_token", "sessiontoken", "token", "api_key", "apikey",
               "credential", "credentials", "bearer", "jwt")
# Ng╞░ß╗íng ─æß╗Ö d├ái chß╗ë ─æß╗â loß║íi R├üC HIß╗éN NHI├èN (tr╞░ß╗¥ng rß╗ùng, "none", "Bearer"), kh├┤ng phß║úi ─æß╗â
# ─æo├ín token thß║¡t d├ái bao nhi├¬u. Cß╗æ ├╜ ─æß╗â THß║ñP: hai chiß╗üu sai ß╗ƒ ─æ├óy kh├┤ng ngang gi├í nhau - qu├í
# lß╗Ång th├¼ thß║╗ xanh m├á l╞░ß╗út chat ─æß╗Å, v├á n├║t "Kiß╗âm tra lß║íi" chß║íy mß╗Öt l╞░ß╗út thß║¡t sß║╜ bß║»t ─æ╞░ß╗úc;
# qu├í chß║╖t th├¼ ng╞░ß╗¥i d├╣ng ─æ─âng nhß║¡p xong vß║½n kh├┤ng v├áo ─æ╞░ß╗úc v├á chß║│ng c├│ g├¼ chß╗ë ra v├¼ sao,
# ─æ├║ng lß╗ùi ─æ├ú xß║úy ra ß╗ƒ 0.50.0.
_TOKEN_DAI_TOI_THIEU = 8

# T├¬n file phi├¬n, thß╗¡ theo thß╗⌐ tß╗▒. `auth.json` l├á c├íi t├ái liß╗çu nhß║»c tß╗¢i; sß╗æ c├▓n lß║íi l├á nhß╗»ng
# t├¬n m├á CLI c├╣ng loß║íi hay d├╣ng - rß║╗ ─æß╗â thß╗¡, v├á thß╗¡ hß╗Ñt th├¼ kh├┤ng mß║Ñt g├¼.
_FILE_PHIEN = ("auth.json", "credentials.json", "session.json", "tokens.json", "oauth.json")


def _tim_token(o, sau: int = 0):
    """Trong c├óy JSON n├áy c├│ token n├áo kh├┤ng. Trß║ú t├¬n kho├í t├¼m thß║Ñy, hoß║╖c "".

    Chß╗ë trß║ú T├èN kho├í, kh├┤ng bao giß╗¥ trß║ú gi├í trß╗ï: h├ám n├áy phß╗Ñc vß╗Ñ cß║ú phß║ºn chß║⌐n ─æo├ín hiß╗çn ra
    m├án h├¼nh, m├á gi├í trß╗ï ß╗ƒ ─æ├óy ─æ├║ng l├á thß╗⌐ ─æ─âng nhß║¡p ─æ╞░ß╗úc v├áo t├ái khoß║ún ng╞░ß╗¥i d├╣ng.
    """
    if sau > 6:
        return ""
    if isinstance(o, dict):
        for k, v in o.items():
            kl = str(k).lower().replace("-", "_")
            if (kl in _KHOA_TOKEN and isinstance(v, str)
                    and len(v.strip()) >= _TOKEN_DAI_TOI_THIEU):
                return str(k)
            trong = _tim_token(v, sau + 1)
            if trong:
                return trong
    elif isinstance(o, list):
        for v in o[:20]:
            trong = _tim_token(v, sau + 1)
            if trong:
                return trong
    return ""


def _tim_chuoi(o, ten, sau: int = 0) -> str:
    """Gi├í trß╗ï chuß╗ùi ─æß║ºu ti├¬n cß╗ºa mß╗Öt trong c├íc kho├í `ten`, t├¼m ß╗ƒ mß╗ìi tß║ºng. "" nß║┐u kh├┤ng c├│."""
    if sau > 6:
        return ""
    if isinstance(o, dict):
        for k, v in o.items():
            if str(k).lower() in ten and isinstance(v, str) and v.strip():
                return v.strip()
        for v in o.values():
            trong = _tim_chuoi(v, ten, sau + 1)
            if trong:
                return trong
    elif isinstance(o, list):
        for v in o[:20]:
            trong = _tim_chuoi(v, ten, sau + 1)
            if trong:
                return trong
    return ""


def _doc_phien() -> tuple:
    """T├¼m file phi├¬n ─æ─âng nhß║¡p trong th╞░ mß╗Ñc cß╗ºa `grok`. Trß║ú (path|None, dict|None).

    Qu├⌐t `_FILE_PHIEN` tr╞░ß╗¢c, rß╗ôi mß╗¢i tß╗¢i mß╗ìi `*.json` c├▓n lß║íi trong th╞░ mß╗Ñc - CLI ─æß╗òi t├¬n file
    l├á chuyß╗çn xß║úy ra, v├á Javis kh├┤ng n├¬n chß║┐t v├¼ mß╗Öt c├íi t├¬n.
    """
    home = _grok_home()
    ten_da_thu = set()
    ds = []
    for ten in _FILE_PHIEN:
        ten_da_thu.add(ten)
        ds.append(home / ten)
    try:
        for f in sorted(home.glob("*.json"))[:20]:
            if f.name not in ten_da_thu:
                ds.append(f)
    except Exception:
        pass
    for f in ds:
        try:
            if not f.is_file() or f.stat().st_size > 4_000_000:
                continue
        except Exception:
            continue
        d = _doc_json(f)
        if isinstance(d, (dict, list)) and _tim_token(d):
            return f, d
    return None, None


def auth_status() -> dict:
    """─É├ú ─æ─âng nhß║¡p ch╞░a: {connected, method, account, plan, error}.

    ─Éß╗îC FILE, kh├┤ng gß╗ìi CLI - mß╗ùi lß║ºn mß╗ƒ trang Models m├á ─æß║╗ mß╗Öt tiß║┐n tr├¼nh l├á v├ái tr─âm ms cho
    mß╗Öt c├óu trß║ú lß╗¥i nß║▒m sß║╡n tr├¬n ─æ─⌐a.

    Thß╗⌐ tß╗▒ x├⌐t b├ím ─æ├║ng "Auth Precedence" trong t├ái liß╗çu ch├¡nh chß╗º: phi├¬n ─æ─âng nhß║¡p trong
    th╞░ mß╗Ñc `~/.grok` thß║»ng, `XAI_API_KEY` l├á ─æ╞░ß╗¥ng l├╣i khi kh├┤ng c├│ phi├¬n n├áo.
    """
    cli = find_grok_cli()
    if not cli:
        return {"connected": False, "method": "", "account": "", "plan": "",
                "error": f"Ch╞░a c├ái Grok CLI ({lenh_cai()})."}
    f, auth = _doc_phien()
    if auth is not None:
        acc = _tim_chuoi(auth, ("email", "account", "username", "handle", "user", "name"))
        plan = _tim_chuoi(auth, ("plan", "subscription", "tier"))
        pt = _tim_chuoi(auth, ("issuer", "method", "provider")) or "oauth"
        return {"connected": True, "method": pt, "account": acc, "plan": plan,
                "error": "", "file": str(f)}
    if (os.environ.get("XAI_API_KEY") or "").strip():
        return {"connected": True, "method": "xai-api-key", "account": "", "plan": "",
                "error": ""}
    # C├│ file m├á kh├┤ng nhß║¡n ra token th├¼ phß║úi N├ôI RA, ─æß╗½ng gß╗Öp chung vß╗¢i "ch╞░a ─æ─âng nhß║¡p bao
    # giß╗¥": hai ca n├áy cß║ºn hai h├ánh ─æß╗Öng kh├íc hß║│n nhau, v├á gß╗Öp lß║íi ch├¡nh l├á c├íi ─æ├ú l├ám ng╞░ß╗¥i
    # d├╣ng ngß╗ôi bß║Ñm ─É─âng nhß║¡p lß║íi nhiß╗üu lß║ºn v├┤ ├¡ch.
    co_file = [x["ten"] for x in _liet_ke_home()]
    if co_file:
        return {"connected": False, "method": "", "account": "", "plan": "",
                "error": ("Th╞░ mß╗Ñc " + str(_grok_home()) + " ─æ├ú c├│ file (" + ", ".join(co_file[:6])
                          + ") nh╞░ng Javis kh├┤ng nhß║¡n ra token ─æ─âng nhß║¡p trong ─æ├│. "
                            "Bß║Ñm \"Kiß╗âm tra lß║íi\" ─æß╗â xem chi tiß║┐t.")}
    return {"connected": False, "method": "", "account": "", "plan": "",
            "error": "─É├ú c├ái Grok CLI nh╞░ng ch╞░a ─æ─âng nhß║¡p. Bß║Ñm \"─É─âng nhß║¡p\" ngay tr├¬n thß║╗ n├áy."}


def _liet_ke_home() -> list:
    """T├¬n + cß╗í c├íc file trong th╞░ mß╗Ñc cß║Ñu h├¼nh cß╗ºa `grok`. Kh├┤ng ─æß╗ìc nß╗Öi dung."""
    ra = []
    try:
        for f in sorted(_grok_home().iterdir())[:40]:
            try:
                ra.append({"ten": f.name, "bytes": f.stat().st_size if f.is_file() else -1})
            except Exception:
                ra.append({"ten": f.name, "bytes": -1})
    except Exception:
        pass
    return ra


def chan_doan() -> dict:
    """Mß╗ìi thß╗⌐ cß║ºn ─æß╗â trß║ú lß╗¥i "v├¼ sao thß║╗ Grok vß║½n b├ío ch╞░a ─æ─âng nhß║¡p", KH├öNG lß╗Ö token.

    Bß║ún 0.50.0 vß╗⌐t sß║ích nhß╗»ng g├¼ `grok login` in ra, n├¬n khi ng╞░ß╗¥i d├╣ng b├ío "─æ├ú bß║Ñm x├íc nhß║¡n
    tr├¬n tr├¼nh duyß╗çt m├á thß║╗ vß║½n quay" th├¼ kh├┤ng c├▓n mß╗Öt mß║⌐u bß║▒ng chß╗⌐ng n├áo ─æß╗â lß║ºn. ─É├óy l├á chß╗ù
    giß╗» lß║íi: ─æ╞░ß╗¥ng dß║½n binary, th╞░ mß╗Ñc cß║Ñu h├¼nh, T├èN c├íc file trong ─æ├│, T├èN c├íc kho├í cß║Ñp cao
    cß╗ºa file phi├¬n, v├á nhß╗»ng d├▓ng CLI vß╗½a in ra.

    Chß╗ë t├¬n kho├í, kh├┤ng bao giß╗¥ c├│ gi├í trß╗ï - gi├í trß╗ï ß╗ƒ ─æ├óy ch├¡nh l├á token ─æ─âng nhß║¡p.
    """
    home = _grok_home()
    ra = {"cli_path": find_grok_cli() or "", "home": str(home), "home_ton_tai": False,
          "files": [], "file_phien": "", "khoa_cap_cao": [], "co_token": False,
          "khoa_token": "", "xai_api_key": bool((os.environ.get("XAI_API_KEY") or "").strip()),
          "nhat_ky": nhat_ky_dang_nhap()}
    try:
        ra["home_ton_tai"] = home.is_dir()
    except Exception:
        pass
    ra["files"] = _liet_ke_home()
    f, d = _doc_phien()
    if f is not None:
        ra["file_phien"] = str(f)
        ra["co_token"] = True
        ra["khoa_token"] = _tim_token(d)
        if isinstance(d, dict):
            ra["khoa_cap_cao"] = [str(k) for k in list(d.keys())[:40]]
        return ra
    # Kh├┤ng t├¼m ra token: vß║½n kß╗â t├¬n kho├í cß║Ñp cao cß╗ºa tß╗½ng file json ─æß╗â biß║┐t CLI ghi kiß╗âu g├¼.
    for x in ra["files"]:
        if not x["ten"].endswith(".json"):
            continue
        d2 = _doc_json(home / x["ten"])
        if isinstance(d2, dict):
            ra["khoa_cap_cao"] += [x["ten"] + ":" + str(k) for k in list(d2.keys())[:20]]
    return ra


def login_huong_dan() -> dict:
    return {
        "cai": lenh_cai(),
        "dang_nhap": "grok login --device-auth",
        "ghi_chu": ("C├ích kh├íc: chß║íy `grok login` trong terminal. Qua SSH th├¼ th├¬m "
                    "`--device-auth`, n├│ in ra mß╗Öt link v├á mß╗Öt m├ú ─æß╗â mß╗ƒ tr├¬n m├íy bß║ín. "
                    "Javis nhß║¡n ra cß║ú t├ái khoß║ún ─æ─âng nhß║¡p kiß╗âu ─æ├│."),
    }


# ---------------------------------------------------------------------------
# ─É─âng nhß║¡p bß║▒ng device code, ─æiß╗üu khiß╗ân tß╗½ dashboard
# ---------------------------------------------------------------------------
# `grok login --device-auth` KH├öNG phß║úi mß╗Öt v├▓ng trao ─æß╗òi hai b╞░ß╗¢c nh╞░ OAuth cß╗ºa Gemini: n├│ in
# ra mß╗Öt link v├á mß╗Öt m├ú, rß╗ôi Tß╗░ ─Éß╗¿NG ─É├ô Hß╗ÄI m├íy chß╗º cho tß╗¢i khi ng╞░ß╗¥i d├╣ng bß║Ñm xong tr├¬n web.
# N├¬n Javis kh├┤ng c├│ "m├ú" n├áo ─æß╗â nhß║¡n lß║íi v├á gß╗¡i ─æi - viß╗çc cß╗ºa n├│ l├á: mß╗ƒ tiß║┐n tr├¼nh, b├│c lß║Ñy
# link + m├ú, trß║ú cho giao diß╗çn, rß╗ôi ─æß╗â tiß║┐n tr├¼nh chß║íy tiß║┐p v├á theo d├╡i `auth.json` xuß║Ñt hiß╗çn.
#
# ─É├óy l├á chß╗ù Grok l├ám ─æ╞░ß╗úc thß╗⌐ Antigravity kh├┤ng l├ám ─æ╞░ß╗úc: ─æ─âng nhß║¡p ngay tr├¬n dashboard, kß╗â cß║ú
# khi Javis ─æang chß║íy tr├¬n VPS kh├┤ng c├│ tr├¼nh duyß╗çt.
_LOGIN: dict = {"proc": None, "url": "", "code": "", "loi": "", "bat_dau": 0.0,
                "log": None, "ma_thoat": None}
_URL_RE = None
_BIMAT_RE = None
NHAT_KY_TOI_DA = 60      # sß╗æ d├▓ng CLI giß╗» lß║íi; ─æß╗º ─æß╗â ─æß╗ìc hiß╗âu, kh├┤ng th├ánh b├úi r├íc trong RAM


def _che_bi_mat(dong: str) -> str:
    """Che nhß╗»ng chuß╗ùi d├ái tr├┤ng nh╞░ token tr╞░ß╗¢c khi cho v├áo nhß║¡t k├╜.

    Nhß║¡t k├╜ n├áy HIß╗åN RA M├ÇN H├îNH v├á ─æi v├áo ß║únh chß╗Ñp ng╞░ß╗¥i d├╣ng gß╗¡i ─æi. `grok login` in ra link
    device code (phß║úi giß╗» nguy├¬n, ng╞░ß╗¥i d├╣ng cß║ºn bß║Ñm) nh╞░ng c┼⌐ng c├│ thß╗â in ra token sau khi
    ─æß╗òi xong - c├íi ─æ├│ lß╗Ö l├á mß║Ñt t├ái khoß║ún.
    """
    global _BIMAT_RE
    if _BIMAT_RE is None:
        import re
        # Chuß╗ùi d├ái kh├┤ng khoß║úng trß║»ng, kh├┤ng phß║úi URL, kh├┤ng phß║úi m├ú device (c├│ gß║ích nß╗æi ngß║»n).
        _BIMAT_RE = re.compile(r"\b(?![A-Z0-9]{4,}-)[A-Za-z0-9_\-]{32,}\b")
    if "://" in dong:
        return dong          # link ─æ─âng nhß║¡p: ng╞░ß╗¥i d├╣ng cß║ºn nguy├¬n vß║╣n ─æß╗â bß║Ñm
    return _BIMAT_RE.sub("[─æ├ú che]", dong)


def _ghi_nhat_ky(dong: str) -> None:
    if _LOGIN.get("log") is None:
        return
    d = _che_bi_mat(dong.strip())
    if d:
        _LOGIN["log"].append(d)


def nhat_ky_dang_nhap() -> list:
    """Nhß╗»ng d├▓ng `grok login` vß╗½a in ra, ─æ├ú che token. [] nß║┐u ch╞░a chß║íy lß║ºn n├áo.

    Bß║ún 0.50.0 ─æß╗ìc xong l├á Vß╗¿T: chß╗ë moi link vß╗¢i m├ú rß╗ôi bß╗Å phß║ºn c├▓n lß║íi. N├¬n khi ng╞░ß╗¥i d├╣ng
    b├ío "─æ├ú bß║Ñm x├íc nhß║¡n tr├¬n accounts.x.ai m├á thß║╗ vß║½n quay m├úi" (28/08/2026) th├¼ kh├┤ng c├▓n
    mß╗Öt mß║⌐u bß║▒ng chß╗⌐ng n├áo ─æß╗â biß║┐t CLI ─æang kß║╣t ß╗ƒ ─æ├óu. Giß╗» lß║íi l├á rß║╗, v├á l├á thß╗⌐ duy nhß║Ñt trß║ú
    lß╗¥i ─æ╞░ß╗úc c├óu hß╗Åi ─æ├│.
    """
    log = _LOGIN.get("log")
    return list(log) if log else []


def _bat_url_code(dong: str) -> None:
    """B├│c link v├á m├ú tß╗½ mß╗Öt d├▓ng CLI in ra. Cß║ú hai ─æß╗üu 'thß║Ñy th├¼ lß║Ñy', kh├┤ng ─æo├ín vß╗ï tr├¡."""
    global _URL_RE
    if _URL_RE is None:
        import re
        _URL_RE = re.compile(r"https?://[^\s\"'<>]+")
    if not _LOGIN["url"]:
        m = _URL_RE.search(dong)
        if m:
            _LOGIN["url"] = m.group(0).rstrip(".,);")
    if not _LOGIN["code"]:
        # M├ú device code th╞░ß╗¥ng l├á chß╗»-sß╗æ viß║┐t hoa c├│ gß║ích nß╗æi (ABCD-EFGH). T├¼m token dß║íng ─æ├│,
        # kß╗â cß║ú khi n├│ nß║▒m TRONG link (`...?user_code=N3FJ-B2J7`) - link ─æ├ú mang sß║╡n m├ú th├¼
        # ng╞░ß╗¥i d├╣ng kh├┤ng phß║úi g├╡, nh╞░ng hiß╗çn ra vß║½n h╞ín: c├│ bß║ún CLI hß╗Åi lß║íi m├ú tr├¬n web.
        import re
        for tok in re.findall(r"\b[A-Z0-9]{4,}(?:-[A-Z0-9]{4,})+\b", dong):
            _LOGIN["code"] = tok
            break


def _doc_luong(proc) -> None:
    """─Éß╗ìc stdout cß╗ºa tiß║┐n tr├¼nh login, cß║»t d├▓ng theo Cß║ó `\n` Lß║¬N `\r`.

    ─Éß╗ìc tß╗½ng k├╜ tß╗▒ chß╗⌐ kh├┤ng `readline`: CLI loß║íi n├áy hay vß║╜ spinner bß║▒ng `\r` kh├┤ng xuß╗æng
    d├▓ng, m├á `readline` th├¼ ─æß╗⌐ng chß╗¥ `\n` - d├▓ng chß╗⌐a link c├│ thß╗â nß║▒m kß║╣t trong bß╗Ö ─æß╗çm tß╗¢i
    khi hß║┐t giß╗¥. L╞░ß╗úng chß╗» cß╗ºa mß╗Öt l╞░ß╗út ─æ─âng nhß║¡p nhß╗Å x├¡u n├¬n ─æß╗ìc tß╗½ng k├╜ tß╗▒ kh├┤ng tß╗æn g├¼.
    """
    buf = ""
    try:
        while True:
            ch = proc.stdout.read(1)
            if not ch:
                break
            if ch in "\r\n":
                if buf.strip():
                    _bat_url_code(buf)
                    _ghi_nhat_ky(buf)
                buf = ""
            else:
                buf += ch
                if len(buf) > 4000:      # d├▓ng kh├┤ng xuß╗æng d├▓ng bao giß╗¥: cß║»t, ─æß╗½ng ph├¼nh RAM
                    _bat_url_code(buf)
                    _ghi_nhat_ky(buf)
                    buf = ""
    except Exception as e:
        _ghi_nhat_ky(f"[Javis ─æß╗ìc output lß╗ùi] {type(e).__name__}: {e}")
    if buf.strip():
        _bat_url_code(buf)
        _ghi_nhat_ky(buf)
    try:
        _LOGIN["ma_thoat"] = proc.wait(timeout=5)
        _ghi_nhat_ky(f"[grok login kß║┐t th├║c, m├ú tho├ít {_LOGIN['ma_thoat']}]")
    except Exception:
        pass


def login_start(cho_giay: float = 30.0) -> dict:
    """Mß╗ƒ `grok login --device-auth`, trß║ú {ok, url, code} ─æß╗â giao diß╗çn hiß╗çn ra cho ng╞░ß╗¥i d├╣ng.

    Tiß║┐n tr├¼nh ─æ╞░ß╗úc GIß╗« Lß║áI chß║íy tiß║┐p sau khi h├ám n├áy trß║ú vß╗ü: n├│ c├▓n phß║úi hß╗Åi m├íy chß╗º tß╗¢i khi
    ng╞░ß╗¥i d├╣ng bß║Ñm x├íc nhß║¡n tr├¬n web. Giao diß╗çn theo d├╡i tiß║┐p bß║▒ng `login_trang_thai()`.
    """
    cli = find_grok_cli()
    if not cli:
        return {"ok": False, "error": f"Ch╞░a c├ái Grok CLI ({lenh_cai()})."}
    logout_huy_tien_trinh()
    args = [cli, "login"]
    if co_co("--device-auth", "--device-code"):
        args.append("--device-auth")
    try:
        proc = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                                errors="replace", bufsize=1, creationflags=_no_window(),
                                env=_moi_truong(), start_new_session=(os.name != "nt"))
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}
    from collections import deque
    _LOGIN.update(proc=proc, url="", code="", loi="", bat_dau=time.time(),
                  log=deque(maxlen=NHAT_KY_TOI_DA), ma_thoat=None)
    # Ghi lu├┤n lß╗çnh ─æ├ú chß║íy: bß║ún CLI kh├┤ng khai `--device-auth` th├¼ Javis chß║íy `grok login`
    # trß║ºn, v├á hai ─æ╞░ß╗¥ng ─æ├│ hß╗Ång theo hai kiß╗âu kh├íc nhau. Kh├┤ng ghi lß║íi th├¼ ─æo├ín m├▓.
    _ghi_nhat_ky("[Javis chß║íy] " + " ".join(args[1:]))
    threading.Thread(target=_doc_luong, args=(proc,), name="javis-grok-login",
                     daemon=True).start()
    han = time.time() + cho_giay
    while time.time() < han:
        if _LOGIN["url"]:
            break
        if proc.poll() is not None:
            break
        time.sleep(0.2)
    if not _LOGIN["url"]:
        if proc.poll() is not None and auth_status().get("connected"):
            return {"ok": True, "xong": True, "url": "", "code": ""}
        return {"ok": False,
                "error": ("Grok CLI kh├┤ng in ra link ─æ─âng nhß║¡p trong " f"{int(cho_giay)}s. "
                          "Thß╗¡ chß║íy `grok login --device-auth` trong terminal cß╗ºa m├íy chß╗º."),
                "nhat_ky": nhat_ky_dang_nhap()}
    return {"ok": True, "xong": False, "url": _LOGIN["url"], "code": _LOGIN["code"],
            "nhat_ky": nhat_ky_dang_nhap()}


def login_trang_thai() -> dict:
    """V├▓ng ─æ─âng nhß║¡p ─æang tß╗¢i ─æ├óu. Giao diß╗çn gß╗ìi lß║╖p lß║íi c├íi n├áy sau `login_start`.

    K├¿m `nhat_ky` - nhß╗»ng d├▓ng CLI vß╗½a in ra. ─É├óy l├á ─æiß╗âm kh├íc bß║ún 0.50.0 v├á l├á l├╜ do bß║ún ─æ├│
    kh├┤ng chß║⌐n ─æ╞░ß╗úc lß╗ùi ng╞░ß╗¥i d├╣ng gß║╖p: v├▓ng quay chß╗ë biß║┐t "xong / ch╞░a xong", n├¬n khi CLI
    ─æß╗⌐ng im hay chß║┐t lß║╖ng th├¼ m├án h├¼nh chß╗ë c├│ mß╗Öt d├▓ng "─æang chß╗¥" quay m├úi.
    """
    proc = _LOGIN.get("proc")
    d = auth_status()
    dang_chay = bool(proc and proc.poll() is None)
    if not d.get("connected") and proc is not None and not dang_chay:
        # Tiß║┐n tr├¼nh vß╗½a tho├ít. File phi├¬n c├│ thß╗â c├▓n ─æang ─æ╞░ß╗úc ghi - hß╗Åi lß║íi mß╗Öt nhß╗ïp tr╞░ß╗¢c
        # khi kß║┐t luß║¡n l├á hß╗Ång, kß║╗o b├ío lß╗ùi ngay l├║c n├│ sß║»p th├ánh c├┤ng.
        time.sleep(0.6)
        d = auth_status()
    loi = ""
    if not d.get("connected") and not dang_chay:
        ma = _LOGIN.get("ma_thoat")
        cuoi = [x for x in nhat_ky_dang_nhap() if not x.startswith("[")]
        loi = (d.get("error") or "─É─âng nhß║¡p ch╞░a xong.")
        if ma not in (None, 0):
            loi = f"`grok login` tho├ít vß╗¢i m├ú {ma}. " + loi
        if cuoi:
            loi += " CLI n├│i: " + cuoi[-1][:200]
    return {"connected": bool(d.get("connected")), "dang_cho": dang_chay,
            "url": _LOGIN.get("url", ""), "code": _LOGIN.get("code", ""),
            "account": d.get("account", ""), "plan": d.get("plan", ""),
            "ma_thoat": _LOGIN.get("ma_thoat"), "nhat_ky": nhat_ky_dang_nhap(),
            "error": loi}


def logout_huy_tien_trinh() -> None:
    proc = _LOGIN.get("proc")
    if proc and proc.poll() is None:
        try:
            proc.kill()
        except Exception:
            pass
    _LOGIN.update(proc=None, url="", code="", loi="", bat_dau=0.0)


def logout() -> dict:
    """`grok logout` - xo├í phi├¬n CLI ─æang giß╗».

    Kh├íc `agy` (kh├┤ng c├│ n├║t Ngß║»t v├¼ token nß║▒m trong keyring kh├┤ng ─æß╗Ñng ─æ╞░ß╗úc): ß╗ƒ ─æ├óy CLI c├│
    lß╗çnh ─æ─âng xuß║Ñt ch├¡nh chß╗º, n├¬n n├║t Ngß║»t l├ám ─æ├║ng viß╗çc n├│ hß╗⌐a.
    """
    logout_huy_tien_trinh()
    cli = find_grok_cli()
    if not cli:
        return {"ok": False, "error": "Ch╞░a c├ái Grok CLI."}
    try:
        r = subprocess.run([cli, "logout"], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=30, creationflags=_no_window(),
                           env=_moi_truong(), stdin=subprocess.DEVNULL)
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}
    if r.returncode != 0:
        return {"ok": False, "error": ((r.stderr or r.stdout or "").strip()[:300]
                                       or f"Tho├ít m├ú {r.returncode}")}
    return {"ok": True}


def list_models() -> Optional[list]:
    """Danh s├ích model cho picker.

    Hß╗Åi CLI tr╞░ß╗¢c (nß║┐u bß║ún n├áy c├│ lß╗çnh liß╗çt k├¬), rß╗ôi mß╗¢i tß╗¢i bß║úng dß╗▒ ph├▓ng cß╗Öng model ─æang ─æß║╖t
    mß║╖c ─æß╗ïnh trong `~/.grok/config.toml` - m├íy ─æ╞░ß╗úc cß║Ñp bß║ún preview ri├¬ng vß║½n thß║Ñy ─æ├║ng t├¬n
    m├¼nh ─æang d├╣ng.
    """
    cli = find_grok_cli()
    if not cli:
        return None
    ids: list = []
    if co_co("models"):
        try:
            r = subprocess.run([cli, "models", "--json"], capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=20,
                               creationflags=_no_window(), env=_moi_truong(),
                               stdin=subprocess.DEVNULL)
            if r.returncode == 0:
                d = json.loads((r.stdout or "").strip() or "[]")
                if isinstance(d, dict):
                    d = d.get("models") or d.get("data") or []
                for m in d if isinstance(d, list) else []:
                    mid = m.get("id") or m.get("name") if isinstance(m, dict) else m
                    if isinstance(mid, str) and mid.strip() and mid not in ids:
                        ids.append(mid.strip())
        except Exception:
            pass                          # kh├┤ng hß╗Åi ─æ╞░ß╗úc th├¼ r╞íi xuß╗æng bß║úng dß╗▒ ph├▓ng
    if not ids:
        ids = list(MODELS_DU_PHONG)
    cfg = _doc_toml(_grok_home() / "config.toml")
    ten = str(((cfg.get("models") or {}) or {}).get("default") or "").strip()
    if ten and ten not in ids:
        ids.insert(0, ten)
    return ids


# Sß╗æ d├▓ng stdout giß╗» lß║íi ─æß╗â chß║⌐n ─æo├ín mß╗Öt l╞░ß╗út, chia ─É├öI: nß╗¡a ─Éß║ªU v├á nß╗¡a ─ÉU├öI.
#
# Bß║ún 0.50.3 chß╗ë giß╗» 40 d├▓ng ─Éß║ªU, v├á ─æ├│ l├á khiß║┐m khuyß║┐t cß╗ºa ch├¡nh phß║ºn chß║⌐n ─æo├ín: c├óu trß║ú lß╗¥i
# cß╗ºa model bao giß╗¥ c┼⌐ng nß║▒m ß╗ƒ CUß╗ÉI luß╗ông, sau phß║ºn khai b├ío tool v├á mß╗Öt tr├áng `thought`.
# Ng╞░ß╗¥i d├╣ng gß╗¡i ß║únh chß╗Ñp 29/08 - "in ra 40 d├▓ng, thß║Ñy: available_commands, thought" - tß╗⌐c
# Javis ─æ├ú dß╗½ng ghi ─æ├║ng tr╞░ß╗¢c ─æoß║ín cß║ºn nh├¼n. Trß║ºn kiß╗âu ─æ├│ chß║⌐n ─æ╞░ß╗úc phß║ºn mß╗ƒ ─æß║ºu v├á m├╣ ─æ├║ng
# phß║ºn quan trß╗ìng.
_CHAN_DAU_TOI_DA = 20
_CHAN_DUOI_TOI_DA = 20
_CHAN_LOAI_TOI_DA = 40     # sß╗æ loß║íi sß╗▒ kiß╗çn KH├üC NHAU, kh├┤ng phß║úi sß╗æ sß╗▒ kiß╗çn
_CHAN_VOT_TOI_DA = 60      # sß╗æ mß║⌐u chß╗» vß╗¢t ─æ╞░ß╗úc tß╗½ sß╗▒ kiß╗çn lß║í


# Cß╗¥ m├á gi├í trß╗ï ─æi sau n├│ l├á Nß╗ÿI DUNG NG╞»ß╗£I D├ÖNG, kh├┤ng bao giß╗¥ ─æ╞░ß╗úc hiß╗çn ra.
_CO_MANG_PROMPT = ("-p", "--single", "--prompt", "--prompt-file")


def _cat_args(args: list) -> list:
    """Danh s├ích Cß╗£ ─æ├ú truyß╗ün, ─æß╗â hiß╗çn l├¬n khi l╞░ß╗út chß║íy hß╗Ñt. KH├öNG k├¿m nß╗Öi dung prompt.

    Prompt cß╗ºa Javis l├á cß║ú system prompt cß╗Öng ngß╗» cß║únh brain - v├ái chß╗Ñc ngh├¼n k├╜ tß╗▒, v├á l├á
    nß╗Öi dung ri├¬ng cß╗ºa ng╞░ß╗¥i d├╣ng. N├│ tuyß╗çt ─æß╗æi kh├┤ng ─æ╞░ß╗úc lß╗ìt v├áo mß╗Öt c├óu b├ío lß╗ùi. N├¬n chß╗ë
    giß╗» token bß║»t ─æß║ºu bß║▒ng `-`, cß╗Öng gi├í trß╗ï NGß║«N ─æi ngay sau mß╗Öt cß╗¥.
    """
    ra = []
    truoc = ""
    for a in [str(x) for x in args[1:]]:
        if a.startswith("-"):
            ra.append(a)
            truoc = a
            continue
        # Gi├í trß╗ï ─æi sau mß╗Öt cß╗¥ MANG PROMPT th├¼ bß╗Å hß║│n, kh├┤ng x├⌐t ─æß╗Ö d├ái: prompt ngß║»n vß║½n l├á
        # prompt. (Test bß║»t ─æ╞░ß╗úc ─æ├║ng chß╗ù n├áy - mß╗Öt c├óu 33 k├╜ tß╗▒ ─æ├ú lß╗ìt qua ng╞░ß╗íng ─æß╗Ö d├ái.)
        if truoc in _CO_MANG_PROMPT:
            ra.append("<prompt>")
        elif truoc and len(a) <= 40 and "\n" not in a and not a.startswith(("/", "\\")):
            ra.append(a)
        truoc = ""
    return ra[:16]


def _chan_moi() -> dict:
    from collections import deque
    return {"raw": [], "duoi": deque(maxlen=_CHAN_DUOI_TOI_DA), "loai": set(),
            "vot": [], "ma_thoat": None, "stderr": "", "args": [],
            "qua_file": False, "lan_hai": False, "so_dong": 0}


# Kho├í mang chß╗» ng╞░ß╗¥i ─æß╗ìc ─æ╞░ß╗úc. `message` v├á `content` nß║▒m ─æ├óy v├¼ nhiß╗üu CLI bß╗ìc c├óu trß║ú lß╗¥i
# trong ─æ├│; `tools`, `commands`, `name` th├¼ KH├öNG - ─æ├│ l├á khai b├ío tool, kh├┤ng phß║úi c├óu trß║ú lß╗¥i.
_KHOA_CHU = ("data", "text", "content", "delta", "response", "output", "answer", "message",
             "reply", "result", "completion")

# Loß║íi sß╗▒ kiß╗çn KH├öNG BAO GIß╗£ l├á c├óu trß║ú lß╗¥i, kß╗â cß║ú khi ─æi vß╗¢t. `thought` l├á lß║¡p luß║¡n nß╗Öi bß╗Ö;
# `available_commands` l├á bß║úng khai b├ío tool (thß║Ñy trong luß╗ông thß║¡t ng├áy 29/08) - vß╗¢t n├│ ra l├á
# d├ín mß╗Öt danh s├ích t├¬n tool v├áo chß╗ù c├óu trß║ú lß╗¥i.
_LOAI_KHONG_PHAI_TRA_LOI = ("thought", "usage", "available_commands", "tool_call",
                            "tool_call_update", "ping", "heartbeat", "init", "system")


def _vot_tu_su_kien(ev) -> list:
    """Mß╗ìi mß║⌐u chß╗» ng╞░ß╗¥i ─æß╗ìc ─æ╞░ß╗úc trong Mß╗ÿT sß╗▒ kiß╗çn, bß║Ñt kß╗â s╞í ─æß╗ô. [] nß║┐u kh├┤ng c├│ g├¼.

    D├╣ng khi `_doi_su_kien` kh├┤ng nhß║¡n ra loß║íi. S╞í ─æß╗ô `streaming-json` cß╗ºa Grok ch╞░a ─æ╞░ß╗úc
    t├ái liß╗çu ho├í tß╗¢i tß╗½ng loß║íi, v├á luß╗ông thß║¡t (─æo 29/08) c├│ ├¡t nhß║Ñt `available_commands` v├á
    `thought` - hai loß║íi kh├┤ng hß╗ü nß║▒m trong bß║úng Javis ─æo├ín ban ─æß║ºu. B├ím t├¬n loß║íi th├¼ cß╗⌐ mß╗ùi
    lß║ºn xAI ─æß╗òi l├á hß╗Ång c├óm th├¬m mß╗Öt lß║ºn nß╗»a; b├ím H├îNH Dß║áNG th├¼ kh├┤ng.
    """
    if str((ev or {}).get("type") or "") in _LOAI_KHONG_PHAI_TRA_LOI:
        return []
    ra = []

    def di(o, sau=0):
        if sau > 6 or len(ra) >= 20:
            return
        if isinstance(o, dict):
            if str(o.get("type") or "") in _LOAI_KHONG_PHAI_TRA_LOI:
                return          # khß╗æi con c┼⌐ng c├│ `type` (vd content block dß║íng thought)
            for k, v in o.items():
                if isinstance(v, str) and v.strip() and str(k).lower() in _KHOA_CHU:
                    ra.append(v)
                else:
                    di(v, sau + 1)
        elif isinstance(o, list):
            for v in o[:20]:
                di(v, sau + 1)

    di(ev)
    return ra


def _chan_dong(chan: dict) -> list:
    """D├▓ng th├┤ ─æß╗â hiß╗çn ra: nß╗¡a ─æß║ºu + nß╗¡a ─æu├┤i, c├│ dß║Ñu cß║»t ß╗ƒ giß╗»a nß║┐u ─æ├ú l╞░ß╗úc."""
    dau = list(chan.get("raw") or [])
    duoi = list(chan.get("duoi") or [])
    bo = int(chan.get("so_dong") or 0) - len(dau) - len(duoi)
    if bo > 0:
        return dau + [f"... (l╞░ß╗úc {bo} d├▓ng giß╗»a) ..."] + duoi
    return dau + duoi


# ---------------------------------------------------------------------------
class GrokCLI:
    """Mß╗Öt l╞░ß╗út chß║íy `grok` headless. C├╣ng hß╗úp ─æß╗ông sß╗▒ kiß╗çn vß╗¢i ClaudeSDK/CodexCLI/GeminiCLI.

    query() sinh dict {"type": "tool_call"|"tool_result"|"final"|"error"|"usage", ...} ─æß╗â mß╗ìi
    n╞íi gß╗ìi (chat dashboard, Telegram, viß╗çc nß╗ün) kh├┤ng phß║úi biß║┐t ─æ├óy l├á engine n├áo.
    """

    def __init__(self, cwd: Optional[str] = None, tag: str = "chat", model: Optional[str] = None,
                 instructions: Optional[str] = None):
        self.cli_path = find_grok_cli()
        self.cwd = cwd or os.getcwd()
        self.tag = tag
        self.model = model
        self.instructions = instructions
        self.session_id = None          # c├│ gi├í trß╗ï ΓåÆ `--resume <id>`; kh├┤ng th├¼ mß╗ƒ mß║ích mß╗¢i
        self.mode = "full"
        self.max_turns = 0              # 0 = ─æß╗â CLI tß╗▒ quß║ún, nh╞░ mß╗ìi engine CLI kh├íc
        self.extra_args: list = []
        # ─Éß╗Ö s├óu suy ngh─⌐ (`main._cli_do_sau_khac` ─æß║╖t). None = kh├┤ng truyß╗ün cß╗¥ n├áo.
        # Chß╗ë tß╗¢i ─æ╞░ß╗úc d├▓ng lß╗çnh khi `co_effort` thß║Ñy bß║ún CLI n├áy khai ─æß╗º cß╗¥ lß║½n gi├í trß╗ï.
        self.effort = None
        # Trß║ºn wall-clock cho Mß╗ÿT l╞░ß╗út. ─É├óy kh├┤ng phß║úi ph├▓ng xa: `permission_cho_mode()` fail-
        # closed, n├¬n tr├¬n mß╗Öt bß║ún CLI kh├┤ng khai `--permission-mode` n├│ kh├┤ng truyß╗ün cß╗¥ n├áo -
        # v├á headless m├á CLI dß╗½ng lß║íi hß╗Åi duyß╗çt l├á treo tß╗¢i v├┤ tß║¡n, im lß║╖ng, kh├┤ng mß╗Öt d├▓ng ra
        # stdout ─æß╗â v├▓ng readline tho├ít. Watchdog d╞░ß╗¢i ─æ├óy l├á thß╗⌐ duy nhß║Ñt gß╗í ─æ╞░ß╗úc ca ─æ├│.
        self.timeout = float(os.environ.get("JAVIS_GROK_TIMEOUT") or 900)

    def is_available(self) -> bool:
        return self.cli_path is not None

    def _build_args(self, prompt_file: Optional[str] = None,
                    prompt_argv: Optional[str] = None,
                    dinh_dang: str = "streaming-json") -> list:
        args = [self.cli_path]
        if self.model and co_co("--model"):
            args += ["--model", self.model]
        args += permission_cho_mode(self.mode)
        args += co_effort(self.effort)
        if self.max_turns and co_co("--max-turns"):
            args += ["--max-turns", str(int(self.max_turns))]
        if co_co("--output-format"):
            args += ["--output-format", dinh_dang]
        if co_co("--no-auto-update"):
            args.append("--no-auto-update")
        # Mß║ích c┼⌐ th├¼ nß╗æi lß║íi; mß║ích mß╗¢i th├¼ KH├öNG tß╗▒ cß║Ñp id.
        #
        # `-s/--session-id` c├│ tß╗ôn tß║íi, nh╞░ng t├ái liß╗çu n├│i id Grok tß╗▒ sinh l├á UUIDv7 c├▓n Javis
        # chß╗ë c├│ uuid4 - cß║Ñp mß╗Öt id sai dß║íng l├á l╞░ß╗út ─æß║ºu tho├ít lß╗ùi v├á hß╗Ång c├óm. ─Éß╗â CLI tß╗▒ sinh
        # rß╗ôi ─Éß╗îC Lß║áI id tß╗½ d├▓ng sß╗▒ kiß╗çn th├¼ ─æ├║ng trong mß╗ìi tr╞░ß╗¥ng hß╗úp. Kh├íc Gemini CLI ß╗ƒ chß╗ù
        # n├áy, v├á kh├íc c├│ chß╗º ├╜.
        if self.session_id and co_co("--resume"):
            args += ["--resume", self.session_id]
        args += list(self.extra_args)
        # Prompt: ╞░u ti├¬n FILE. System prompt cß╗ºa Javis k├¿m ngß╗» cß║únh brain v╞░ß╗út trß║ºn d├▓ng lß╗çnh
        # 32767 k├╜ tß╗▒ cß╗ºa Windows dß╗à nh╞░ ch╞íi (─æ├ú ─æo 36.045 k├╜ tß╗▒ tr├¬n mß╗Öt brain TRß╗ÉNG - xem
        # khß╗æi ch├║ th├¡ch trong antigravity_cli.py), n├¬n argv chß╗ë l├á ─æ╞░ß╗¥ng l├╣i.
        if prompt_file and co_co("--prompt-file"):
            args += ["--prompt-file", prompt_file]
        else:
            args += ["-p", prompt_argv if prompt_argv is not None else ""]
        return args

    async def query(self, prompt: str) -> AsyncIterator[dict]:
        if not self.cli_path:
            yield {"type": "error",
                   "content": f"Kh├┤ng t├¼m thß║Ñy Grok CLI. C├ái bß║▒ng `{lenh_cai()}` rß╗ôi chß║íy "
                              "`grok login` mß╗Öt lß║ºn ─æß╗â ─æ─âng nhß║¡p."}
            return
        # Grok kh├┤ng nhß║¡n system prompt ri├¬ng ß╗ƒ chß║┐ ─æß╗Ö headless ΓåÆ gß╗Öp v├áo ─æß║ºu prompt, ─æ├║ng c├ích
        # CodexCLI v├á GeminiCLI ─æang l├ám.
        full = (self.instructions.strip() + "\n\n" + prompt) if self.instructions else prompt
        tep = None
        try:
            fd, tep = tempfile.mkstemp(prefix="javis-grok-", suffix=".txt")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(full)
        except Exception:
            tep = None
        args = self._build_args(prompt_file=tep, prompt_argv=full)
        chan = _chan_moi()
        chan["qua_file"] = bool(tep and "--prompt-file" in args)
        cac_manh: list = []
        da_loi = False
        async for ra in self._mot_lan(args, cac_manh, chan, xoa_tep=tep):
            if ra.get("type") == "error":
                da_loi = True
            yield ra
        text = "".join(cac_manh).strip()

        # ---- Kh├┤ng ra chß╗» n├áo: ─æß╗½ng bß╗Å cuß╗Öc bß║▒ng mß╗Öt c├óu trß╗æng rß╗ùng ----
        # Ng╞░ß╗¥i d├╣ng b├ío 28/08/2026: ─æ─âng nhß║¡p xong, chat "ch├áo grok" th├¼ chß╗ë nhß║¡n ─æ╞░ß╗úc
        # "Grok CLI chß║íy xong nh╞░ng kh├┤ng trß║ú vß╗ü nß╗Öi dung n├áo." C├óu ─æ├│ kh├┤ng n├│i ─æ╞░ß╗úc ─æiß╗üu g├¼
        # v├á kh├┤ng c├│ ─æ╞░ß╗¥ng n├áo ─æi tiß║┐p. Hai ca ho├án to├án kh├íc nhau nß║Ñp sau n├│:
        #
        #   a) CLI C├ô in JSON, nh╞░ng to├án loß║íi sß╗▒ kiß╗çn Javis ch╞░a biß║┐t -> `_doi_su_kien` bß╗Å
        #      im lß║╖ng. S╞í ─æß╗ô `streaming-json` l├á ─ÉO├üN tß╗½ t├ái liß╗çu, ch╞░a tß╗½ng ─æo tr├¬n m├íy thß║¡t
        #      (Giai ─æoß║ín 0 b╞░ß╗¢c 2), n├¬n ─æ├óy l├á ca rß║Ñt dß╗à xß║úy ra. Chß╗»a: vß╗¢t chß╗» ß╗ƒ mß╗ìi tß║ºng.
        #   b) CLI in ra ─É├ÜNG KH├öNG G├î Cß║ó v├á tho├ít 0. Nhiß╗üu CLI loß║íi n├áy coi `-p/--single` l├á
        #      cß╗¥ Bß║¼T chß║┐ ─æß╗Ö headless, c├▓n `--prompt-file` chß╗ë l├á chß╗ù lß║Ñy nß╗Öi dung - thiß║┐u `-p`
        #      th├¼ n├│ v├áo chß║┐ ─æß╗Ö t╞░╞íng t├íc, gß║╖p stdin rß╗ùng, tho├ít ngay kh├┤ng n├│i g├¼. Chß╗»a:
        #      thß╗¡ lß║íi ─æ├║ng mß╗Öt lß║ºn vß╗¢i prompt ─æ╞░a thß║│ng qua argv.
        if not text and not da_loi:
            text = self._vot_chu(chan)
        if not text and not da_loi:
            # L╞░ß╗út hai: prompt qua argv V├Ç `--output-format json`.
            #
            # Bß║ún 0.50.3 chß╗ë thß╗¡ lß║íi khi stdout Rß╗ûNG, n├¬n ca thß║¡t cß╗ºa ng╞░ß╗¥i d├╣ng (40 d├▓ng
            # to├án `available_commands` + `thought`, ─æo 29/08) kh├┤ng hß╗ü chß║ím tß╗¢i ─æ╞░ß╗¥ng n├áy.
            # ─Éiß╗üu kiß╗çn ─æ├║ng l├á "ch╞░a ra chß╗»", kh├┤ng phß║úi "ch╞░a in g├¼".
            #
            # ─Éß╗òi sang `json` chß╗⌐ kh├┤ng lß║╖p lß║íi `streaming-json`: n├│ trß║ú vß╗ü Mß╗ÿT cß╗Ñc kß║┐t quß║ú
            # thay v├¼ mß╗Öt luß╗ông sß╗▒ kiß╗çn, n├¬n phß║ºn vß╗¢t chß╗ë phß║úi hiß╗âu mß╗Öt h├¼nh dß║íng duy nhß║Ñt.
            # ─É├óy c┼⌐ng ─æ├║ng ─æß╗ïnh dß║íng `kiem_tra_nhanh` vß║½n d├╣ng ─æß╗â trß║ú lß╗¥i "chat ─æ╞░ß╗úc ch╞░a".
            args2 = self._build_args(prompt_file=None, prompt_argv=full, dinh_dang="json")
            chan2 = _chan_moi()
            chan2["lan_hai"] = True
            manh2: list = []
            async for ra in self._mot_lan(args2, manh2, chan2):
                if ra.get("type") == "error":
                    da_loi = True
                yield ra
            text = "".join(manh2).strip() or self._vot_chu(chan2)
            if text:
                # Ghi lß║íi ─æß╗â c├▓n biß║┐t m├á ─æß╗òi hß║│n ─æß╗ïnh dß║íng mß║╖c ─æß╗ïnh nß║┐u ─æ╞░ß╗¥ng kia lu├┤n hß╗Ñt.
                print("[grok] `--output-format streaming-json` kh├┤ng ra nß╗Öi dung, `json` qua "
                      "argv th├¼ ─æ╞░ß╗úc. S╞í ─æß╗ô sß╗▒ kiß╗çn cß╗ºa bß║ún CLI n├áy kh├íc bß║úng Javis ─æang ─æo├ín.",
                      file=sys.stderr)
            else:
                # Giß╗» cß║ú hai ─æß╗â c├óu lß╗ùi kß╗â ─æ╞░ß╗úc cß║ú hai lß║ºn, kh├┤ng chß╗ë lß║ºn sau.
                chan2["loai"] |= set(chan.get("loai") or ())
            chan = chan2

        if text:
            yield {"type": "final", "content": text}
        elif not da_loi:
            yield {"type": "error", "content": self._loi_trong(chan)}

    async def _mot_lan(self, args: list, cac_manh: list, chan: dict,
                       xoa_tep: Optional[str] = None) -> AsyncIterator[dict]:
        """Chß║íy Mß╗ÿT tiß║┐n tr├¼nh `grok` v├á sinh sß╗▒ kiß╗çn theo hß╗úp ─æß╗ông chung.

        T├ích khß╗Åi `query` ─æß╗â chß║íy ─æ╞░ß╗úc lß║ºn hai vß╗¢i bß╗Ö tham sß╗æ kh├íc m├á kh├┤ng ch├⌐p lß║íi cß║ú khß╗æi
        quß║ún tiß║┐n tr├¼nh. `chan` ─æ╞░ß╗úc ─æiß╗ün dß║ºn: d├▓ng th├┤, loß║íi sß╗▒ kiß╗çn ─æ├ú thß║Ñy, m├ú tho├ít,
        stderr - ─æ├│ l├á nhß╗»ng g├¼ `_loi_trong` cß║ºn ─æß╗â n├│i ra sß╗▒ thß║¡t thay v├¼ mß╗Öt c├óu chung chung.
        """
        tep = xoa_tep
        chan["args"] = _cat_args(args)
        loop = asyncio.get_running_loop()
        hang: asyncio.Queue = asyncio.Queue()
        HET = object()

        qua_gio = threading.Event()

        def doc_luong():
            proc = None
            canh = None
            try:
                proc = subprocess.Popen(
                    args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, cwd=self.cwd, text=True, encoding="utf-8",
                    errors="replace", bufsize=1, creationflags=_no_window(),
                    env=_moi_truong(), start_new_session=(os.name != "nt"),
                )

                def cat():
                    """Giß║┐t tiß║┐n tr├¼nh khi qu├í giß╗¥, ─æß╗â v├▓ng readline d╞░ß╗¢i kia tho├ít ra ─æ╞░ß╗úc.

                    `proc.wait(timeout=...)` KH├öNG cß╗⌐u ─æ╞░ß╗úc ca n├áy: n├│ chß╗ë chß║╖n ß╗ƒ b╞░ß╗¢c chß╗¥
                    tho├ít, c├▓n l├║c CLI treo im kh├┤ng in g├¼ th├¼ luß╗ông ─æang ─æß╗⌐ng trong
                    `readline()` chß╗⌐ ch╞░a tß╗¢i ─æ├│.
                    """
                    if proc.poll() is None:
                        qua_gio.set()
                        try:
                            proc.kill()
                        except Exception:
                            pass

                canh = threading.Timer(self.timeout, cat)
                canh.daemon = True
                canh.start()
                for line in iter(proc.stdout.readline, ""):
                    line = line.strip()
                    if not line:
                        continue
                    chan["so_dong"] += 1
                    if len(chan["raw"]) < _CHAN_DAU_TOI_DA:
                        chan["raw"].append(line[:1000])
                    else:
                        chan["duoi"].append(line[:1000])
                    try:
                        loop.call_soon_threadsafe(hang.put_nowait, json.loads(line))
                    except json.JSONDecodeError:
                        # Kh├┤ng phß║úi JSON: bß║ún CLI c┼⌐ ch╞░a c├│ streaming-json, hoß║╖c mß╗Öt d├▓ng
                        # cß║únh b├ío lß╗ìt ra stdout. Giß╗» nguy├¬n l├ám chß╗» thay v├¼ vß╗⌐t ─æi im lß║╖ng.
                        loop.call_soon_threadsafe(hang.put_nowait, {"_raw": line})
                err = ""
                try:
                    err = (proc.stderr.read() or "").strip()
                except Exception:
                    pass
                ma = proc.wait()
                chan["ma_thoat"] = ma
                chan["stderr"] = err[:1000]
                if qua_gio.is_set():
                    loop.call_soon_threadsafe(
                        hang.put_nowait,
                        {"_exit": -1, "_err": f"Grok CLI chß║íy qu├í {int(self.timeout)}s n├¬n bß╗ï "
                                              f"cß║»t. Nß║┐u viß╗çc thß║¡t sß╗▒ d├ái th├¼ n├óng biß║┐n m├┤i "
                                              f"tr╞░ß╗¥ng JAVIS_GROK_TIMEOUT."})
                elif ma != 0:
                    loop.call_soon_threadsafe(hang.put_nowait, {"_exit": ma, "_err": err})
                elif err:
                    # Tho├ít 0 m├á stderr c├│ chß╗» KH├öNG phß║úi lß╗ùi. T├ái liß╗çu ch├¡nh chß╗º n├│i r├╡: ß╗ƒ
                    # chß║┐ ─æß╗Ö headless log ─æi ra stderr, v├á ai ─æß║╖t `RUST_LOG` trong m├┤i tr╞░ß╗¥ng
                    # l├á mß╗ùi l╞░ß╗út lß║íi c├│ v├ái d├▓ng. Coi ─æ├│ l├á lß╗ùi th├¼ l╞░ß╗út n├áo c┼⌐ng ─æß╗Å trong khi
                    # c├óu trß║ú lß╗¥i vß║½n vß╗ü ─æß╗º. Giß╗» lß║íi ß╗ƒ nhß║¡t k├╜ m├íy chß╗º ─æß╗â c├▓n lß║ºn ra khi cß║ºn.
                    print(f"[grok stderr] {err[:2000]}", file=sys.stderr)
            except OSError as e:
                # E2BIG: prompt v╞░ß╗út trß║ºn d├▓ng lß╗çnh. Grok th╞░ß╗¥ng ─æi `--prompt-file` n├¬n hiß║┐m
                # gß║╖p, nh╞░ng bß║ún CLI c┼⌐ thiß║┐u cß╗¥ ─æ├│ th├¼ prompt r╞íi v├áo argv v├á nß╗ò - l├║c ─æ├│
                # KH├öNG c├│ ─æ╞░ß╗¥ng l├╣i n├áo kh├íc, n├¬n n├│i thß║│ng bß║▒ng c├óu ng╞░ß╗¥i d├╣ng l├ám theo ─æ╞░ß╗úc
                # thay v├¼ n├⌐m "OSError: [Errno 7] Argument list too long" ra m├án h├¼nh.
                if getattr(e, "errno", None) in (errno.E2BIG, errno.ENAMETOOLONG):
                    _t = ("Hß╗Öi thoß║íi ─æ├ú qu├í d├ái so vß╗¢i trß║ºn d├▓ng lß╗çnh cß╗ºa hß╗ç ─æiß╗üu h├ánh, m├á bß║ún "
                          "Grok CLI tr├¬n m├íy n├áy ch╞░a c├│ `--prompt-file` ─æß╗â ─æi ─æ╞░ß╗¥ng kh├íc. "
                          "N├óng cß║Ñp Grok CLI (" + lenh_cai() + ") hoß║╖c mß╗ƒ mß╗Öt hß╗Öi thoß║íi mß╗¢i.")
                    loop.call_soon_threadsafe(hang.put_nowait, {"_exit": -1, "_err": _t})
                else:
                    loop.call_soon_threadsafe(
                        hang.put_nowait, {"_exit": -1, "_err": f"{type(e).__name__}: {e}"})
            except Exception as e:
                loop.call_soon_threadsafe(hang.put_nowait,
                                          {"_exit": -1, "_err": f"{type(e).__name__}: {e}"})
            finally:
                if canh:
                    canh.cancel()
                try:
                    if proc and proc.poll() is None:
                        proc.terminate()
                except Exception:
                    pass
                # Dß╗ìn file prompt ß╗ƒ ─É├éY chß╗⌐ kh├┤ng ß╗ƒ v├▓ng ─æß╗ìc sß╗▒ kiß╗çn: luß╗ông n├áy lu├┤n chß║íy hß║┐t,
                # kß╗â cß║ú khi ng╞░ß╗¥i d├╣ng ─æ├│ng tab giß╗»a chß╗½ng v├á kh├┤ng ai ─æß╗ìc nß╗æt h├áng ─æß╗úi nß╗»a.
                # ─Éß╗â s├│t l├á r├íc t├¡ch dß║ºn trong th╞░ mß╗Ñc tß║ím. (B├ái hß╗ìc cß╗ºa antigravity_cli.)
                if tep:
                    try:
                        os.unlink(tep)
                    except Exception:
                        pass
                loop.call_soon_threadsafe(hang.put_nowait, HET)

        threading.Thread(target=doc_luong, name=f"javis-grok-{self.tag}", daemon=True).start()

        while True:
            ev = await hang.get()
            if ev is HET:
                break
            for ra in self._doi_su_kien(ev, cac_manh, chan):
                yield ra

    # -- khi l╞░ß╗út chß║íy KH├öNG ra chß╗» n├áo -------------------------------------
    @staticmethod
    def _vot_chu(chan: dict) -> str:
        """Chß╗» vß╗¢t ─æ╞░ß╗úc tß╗½ nhß╗»ng sß╗▒ kiß╗çn `_doi_su_kien` kh├┤ng nhß║¡n ra loß║íi.

        Chß║íy CHß╗ê khi ─æ╞░ß╗¥ng ch├¡nh ─æ├ú ra rß╗ùng, n├¬n kh├┤ng c├│ nguy c╞í ─æß║┐m chß╗» hai lß║ºn: l╞░ß╗út b├¼nh
        th╞░ß╗¥ng kh├┤ng bao giß╗¥ v├áo ─æ├óy. C├íi gi├í cß╗ºa hai h╞░ß╗¢ng sai rß║Ñt lß╗çch nhau - vß╗¢t nhß║ºm mß╗Öt
        d├▓ng log th├¼ ng╞░ß╗¥i d├╣ng thß║Ñy mß╗Öt c├óu lß║í v├á biß║┐t ngay l├á lß║í; bß╗Å s├│t th├¼ hß╗ì thß║Ñy mß╗Öt ├┤
        trß╗æng v├á kh├┤ng c├│ ─æ╞░ß╗¥ng n├áo ─æi tiß║┐p.

        ╞»u ti├¬n phß║ºn ─æ├ú vß╗¢t Sß║┤N trong luß╗ông (`chan["vot"]`), v├¼ bß╗Ö ─æß╗çm d├▓ng th├┤ c├│ trß║ºn v├á c├óu
        trß║ú lß╗¥i nß║▒m ß╗ƒ cuß╗æi. Qu├⌐t lß║íi d├▓ng th├┤ chß╗ë l├á ─æ╞░ß╗¥ng l├╣i cho n╞íi gß╗ìi dß╗▒ng `chan` bß║▒ng tay
        (`kiem_tra_nhanh` ─æ╞░a v├áo mß╗Öt cß╗Ñc JSON duy nhß║Ñt cß╗ºa `--output-format json`).
        """
        san = [x for x in (chan.get("vot") or []) if str(x).strip()]
        if san:
            return "\n".join(san).strip()
        ra = []
        for dong in list(chan.get("raw") or []) + list(chan.get("duoi") or []):
            try:
                d = json.loads(dong)
            except Exception:
                continue
            ra += _vot_tu_su_kien(d)
        return "\n".join(ra).strip()

    @staticmethod
    def _loi_trong(chan: dict) -> str:
        """C├óu b├ío lß╗ùi cho l╞░ß╗út kh├┤ng ra chß╗» n├áo - N├ôI RA thß╗⌐ Javis thß║¡t sß╗▒ thß║Ñy.

        Bß║ún 0.50.2 chß╗ë c├│ ─æ├║ng mß╗Öt c├óu "Grok CLI chß║íy xong nh╞░ng kh├┤ng trß║ú vß╗ü nß╗Öi dung n├áo",
        kh├┤ng ph├ón biß╗çt "CLI im ho├án to├án" vß╗¢i "CLI n├│i cß║ú tr├áng bß║▒ng thß╗⌐ Javis ch╞░a hiß╗âu".
        Hai ca ─æ├│ cß║ºn hai c├ích chß╗»a kh├íc nhau, m├á c├óu kia th├¼ kh├┤ng dß║½n tß╗¢i c├ích n├áo cß║ú.
        """
        loai = sorted(x for x in (chan.get("loai") or []) if x)
        dong = _chan_dong(chan)
        n = int(chan.get("so_dong") or 0) or len(dong)
        if not n:
            noi = ("Grok CLI chß║íy xong (m├ú tho├ít "
                   f"{chan.get('ma_thoat')}) nh╞░ng KH├öNG in ra g├¼ cß║ú")
            if chan.get("lan_hai"):
                noi += ", kß╗â cß║ú khi thß╗¡ lß║íi vß╗¢i prompt ─æ╞░a thß║│ng qua d├▓ng lß╗çnh"
            noi += (". Thß╗¡ chß║íy tay tr├¬n m├íy chß╗º ─æß╗â xem n├│ n├│i g├¼:\n"
                    "`grok -p \"ch├áo\" --output-format streaming-json`")
        else:
            noi = (f"Grok CLI in ra {n} d├▓ng nh╞░ng Javis kh├┤ng nhß║¡n ra loß║íi sß╗▒ kiß╗çn n├áo l├á "
                   "c├óu trß║ú lß╗¥i")
            if loai:
                noi += " (thß║Ñy: " + ", ".join(loai[:12]) + ")"
            noi += "."
            # D├▓ng ─Éß║ªU v├á d├▓ng CUß╗ÉI. Chß╗ë in d├▓ng ─æß║ºu l├á bß║ún 0.50.3, v├á n├│ ─æ├ú dß║½n sai h╞░ß╗¢ng:
            # d├▓ng ─æß║ºu lu├┤n l├á bß║úng khai b├ío tool, c├▓n c├óu trß║ú lß╗¥i th├¼ nß║▒m ß╗ƒ cuß╗æi.
            if dong:
                noi += "\nD├▓ng ─æß║ºu: " + dong[0][:250]
            if len(dong) > 1:
                noi += "\nD├▓ng cuß╗æi: " + dong[-1][:400]
        if chan.get("stderr"):
            noi += "\nCLI b├ío ß╗ƒ stderr: " + chan["stderr"][:300]
        if chan.get("args"):
            noi += "\nCß╗¥ ─æ├ú truyß╗ün: " + " ".join(chan["args"])
        return noi

    # -- dß╗ïch sß╗▒ kiß╗çn -------------------------------------------------------
    @staticmethod
    def _lay(ev: dict, *ten, mac_dinh=""):
        """Lß║Ñy gi├í trß╗ï ─æß║ºu ti├¬n t├¼m thß║Ñy trong v├ái t├¬n kho├í hß╗úp l├╜.

        T├¬n tr╞░ß╗¥ng cß╗ºa `streaming-json` ch╞░a ─æ╞░ß╗úc t├ái liß╗çu ho├í tß╗¢i mß╗⌐c tß╗½ng kho├í, v├á ─æ├óy l├á bß║ún
        CLI mß╗¢i ─æß╗òi li├¬n tß╗Ñc. D├▓ v├ái t├¬n l├á chß║Ñp nhß║¡n ─æ╞░ß╗úc ß╗ƒ ─æ├óy v├¼ c├íi gi├í cß╗ºa viß╗çc ─æo├ín sai
        rß║Ñt kh├íc nhau: sai t├¬n kho├í tool th├¼ mß║Ñt mß╗Öt nh├ún hiß╗ân thß╗ï, c├▓n nuß╗æt mß║Ñt chß╗» trß║ú lß╗¥i
        th├¼ ng╞░ß╗¥i d├╣ng thß║Ñy "kh├┤ng c├│ nß╗Öi dung trß║ú vß╗ü" tr╞í trß╗ìi.
        """
        for k in ten:
            v = ev.get(k)
            if v not in (None, ""):
                return v
        return mac_dinh

    def _doi_su_kien(self, ev: dict, cac_manh: list, chan: Optional[dict] = None) -> list:
        """Mß╗Öt d├▓ng NDJSON cß╗ºa Grok -> 0..n sß╗▒ kiß╗çn theo hß╗úp ─æß╗ông cß╗ºa Javis."""
        if "_raw" in ev:
            cac_manh.append(str(ev["_raw"]))
            return []
        if "_exit" in ev:
            loi = str(ev.get("_err") or "").strip()
            if ev.get("_exit") == 0 and not loi:
                return []
            l = loi.lower()
            if "xai_api_key" in l or "not authenticated" in l or "unauthorized" in l:
                return [{"type": "error",
                         "content": "Grok CLI ch╞░a ─æ─âng nhß║¡p. Mß╗ƒ trang Models bß║Ñm \"─É─âng nhß║¡p\", "
                                    "hoß║╖c chß║íy `grok login --device-auth` trong terminal."}]
            if not loi:
                loi = f"Grok CLI tho├ít vß╗¢i m├ú {ev.get('_exit')}."
            return [{"type": "error", "content": loi[:1500]}]

        t = str(ev.get("type") or "")
        if chan is not None and t:
            loai = chan.setdefault("loai", set())
            if len(loai) < _CHAN_LOAI_TOI_DA:
                loai.add(t)
        # Id phi├¬n c├│ thß╗â ─æi k├¿m nhiß╗üu loß║íi sß╗▒ kiß╗çn; nhß║╖t ß╗ƒ ─æ├óu thß║Ñy c┼⌐ng ─æ╞░ß╗úc, v├¼ l╞░ß╗út sau chß╗ë
        # cß║ºn ─æ├║ng mß╗Öt id ─æß╗â `--resume`.
        sid = str(self._lay(ev, "sessionId", "session_id") or "").strip()
        if not sid:
            meta = ev.get("metadata")
            if isinstance(meta, dict):
                sid = str(meta.get("sessionId") or meta.get("session_id") or "").strip()
        if sid:
            self.session_id = sid

        if t == "text":
            # `data` ─Éß╗¿NG ─Éß║ªU v├¼ ─æ├│ l├á kho├í THß║¼T, ─æo tr├¬n m├íy ng╞░ß╗¥i d├╣ng ng├áy 29/08:
            #
            #     {"type":"text","data":" nay"}
            #     {"type":"text","data":"?"}
            #
            # Bß║ún 0.50.0 tß╗¢i 0.50.5 chß╗ë d├▓ `text`/`content`/`delta` n├¬n mß╗ìi sß╗▒ kiß╗çn text trß║ú
            # vß╗ü chuß╗ùi rß╗ùng: l╞░ß╗út chß║íy ─æ├║ng, model trß║ú lß╗¥i ─æ├║ng, m├á ng╞░ß╗¥i d├╣ng thß║Ñy mß╗Öt ├┤
            # trß╗æng. ─É├óy l├á gß╗æc rß╗à thß║¡t cß╗ºa "kh├┤ng trß║ú vß╗ü nß╗Öi dung n├áo", v├á ba bß║ún v├í tr╞░ß╗¢c
            # ─æß╗üu ─æi v├▓ng quanh n├│ v├¼ ch╞░a ai ─æo luß╗ông thß║¡t.
            cac_manh.append(str(self._lay(ev, "data", "text", "content", "delta", "value")))
            return []
        if t == "thought":
            return []          # lß║¡p luß║¡n nß╗Öi bß╗Ö, KH├öNG phß║úi c├óu trß║ú lß╗¥i - kh├┤ng gß╗Öp v├áo final
        if t == "tool_call":
            return [{"type": "tool_call",
                     "name": str(self._lay(ev, "name", "tool_name", "tool")),
                     "id": str(self._lay(ev, "id", "tool_call_id", "toolCallId")),
                     "input": self._lay(ev, "input", "parameters", "arguments", mac_dinh={})}]
        if t == "tool_call_update":
            tt = str(self._lay(ev, "status", "state"))
            if tt not in ("completed", "success", "failed", "error"):
                return []      # tiß║┐n ─æß╗Ö chß║íy dß╗ƒ, kh├┤ng phß║úi kß║┐t quß║ú
            return [{"type": "tool_result",
                     "id": str(self._lay(ev, "id", "tool_call_id", "toolCallId")),
                     "status": tt,
                     "content": str(self._lay(ev, "output", "result", "content"))[:2000]}]
        if t == "usage":
            # Luß╗ông thß║¡t bß╗ìc sß╗æ liß╗çu trong kho├í `usage`, kh├┤ng ─æß╗â phß║│ng ß╗ƒ tß║ºng ngo├ái:
            #   {"type":"usage","usage":{"input_tokens":9028,...},"signature":"..."}
            # ─Éß╗ìc tß║ºng ngo├ái l├á mß╗ìi l╞░ß╗út Grok v├áo bß║úng Mß╗⌐c d├╣ng vß╗¢i 0 token.
            u = ev.get("usage")
            return [self._usage(u if isinstance(u, dict) else ev)]
        if t == "end":
            ra: list = []
            u = ev.get("usage")
            if isinstance(u, dict):
                ra.append(self._usage(u))
            # C├│ bß║ún CLI g├│i cß║ú c├óu trß║ú lß╗¥i v├áo sß╗▒ kiß╗çn kß║┐t th├║c. ─Éß╗â d├ánh v├áo phß║ºn vß╗¢t (KH├öNG
            # ─æ╞░a thß║│ng v├áo c├óu trß║ú lß╗¥i): nß║┐u c├íc sß╗▒ kiß╗çn `text` ─æ├ú chß║íy ─æß╗º th├¼ phß║ºn n├áy kh├┤ng
            # bao giß╗¥ ─æ╞░ß╗úc d├╣ng tß╗¢i, c├▓n nß║┐u ch├║ng vß║»ng mß║╖t th├¼ ─æ├óy l├á thß╗⌐ cß╗⌐u cß║ú l╞░ß╗út.
            if chan is not None and len(chan.setdefault("vot", [])) < _CHAN_VOT_TOI_DA:
                chan["vot"] += _vot_tu_su_kien(ev)
            ly_do = str(self._lay(ev, "stopReason", "stop_reason"))
            if ly_do in ("error", "max_turns"):
                tin = str(self._lay(ev, "error", "message"))
                ra.append({"type": "error",
                           "content": tin or f"Grok CLI kß║┐t th├║c sß╗¢m ({ly_do})."})
            return ra
        if t == "error":
            tin = str(self._lay(ev, "message", "error", "content"))
            return [{"type": "error", "content": tin or "Grok CLI lß╗ùi."}]
        # Loß║íi KH├öNG BIß║╛T. Vß║½n KH├öNG ─æ╞░a v├áo c├óu trß║ú lß╗¥i ß╗ƒ ─æ╞░ß╗¥ng ch├¡nh - ─æo├ín bß╗½a mß╗Öt loß║íi lß║í
        # l├á c├óu trß║ú lß╗¥i th├¼ l╞░ß╗út n├áo c┼⌐ng d├¡nh r├íc. Nh╞░ng ─æß╗â d├ánh lß║íi hai thß╗⌐: t├¬n loß║íi (─æ├ú
        # ghi ß╗ƒ tr├¬n) v├á phß║ºn chß╗» vß╗¢t ─æ╞░ß╗úc, ─æß╗â nß║┐u hß║┐t l╞░ß╗út m├á kh├┤ng ra chß╗» n├áo th├¼ c├▓n c├íi m├á
        # d├╣ng thay v├¼ trß║ú vß╗ü mß╗Öt ├┤ trß╗æng.
        #
        # Vß╗¢t NGAY Tß║áI ─É├éY chß╗⌐ kh├┤ng ─æß╗ìc lß║íi `chan["raw"]` l├║c cuß╗æi: bß╗Ö ─æß╗çm ─æ├│ c├│ trß║ºn, m├á c├óu
        # trß║ú lß╗¥i nß║▒m ß╗ƒ cuß╗æi luß╗ông - ─æ├║ng chß╗ù trß║ºn c┼⌐ ─æ├ú cß║»t mß║Ñt (ß║únh chß╗Ñp 29/08).
        if chan is not None and len(chan.setdefault("vot", [])) < _CHAN_VOT_TOI_DA:
            chan["vot"] += _vot_tu_su_kien(ev)
        return []

    @staticmethod
    def _usage(u: dict) -> dict:
        """Sß╗æ token cß╗ºa mß╗Öt l╞░ß╗út. T├¬n kho├í lß║Ñy tß╗½ luß╗ông THß║¼T (─æo 29/08), giß╗» cß║ú t├¬n ─æo├ín c┼⌐.

        Mß║½u thß║¡t:
            {"input_tokens":9028,"output_tokens":54,"cache_read_input_tokens":4352,
             "cache_creation_input_tokens":0,"reasoning_tokens":32,"total_tokens":13434}
        """
        vao = int(u.get("input_tokens") or u.get("input") or u.get("inputTokens") or 0)
        ra = int(u.get("output_tokens") or u.get("output") or u.get("outputTokens") or 0)
        cache = int(u.get("cache_read_input_tokens") or u.get("cache_read")
                    or u.get("cacheRead") or u.get("cached") or 0)
        return {"type": "usage", "input_tokens": vao, "output_tokens": ra,
                "total_tokens": int(u.get("total_tokens") or u.get("total") or (vao + ra)),
                "cached": cache}


# ---------------------------------------------------------------------------
def kiem_tra_nhanh(timeout: float = 30.0) -> dict:
    """Chß║íy thß╗¡ mß╗Öt l╞░ß╗út cß╗▒c ngß║»n ─æß╗â biß║┐t CLI + ─æ─âng nhß║¡p c├│ THß║¼T Sß╗░ d├╣ng ─æ╞░ß╗úc kh├┤ng.

    Trang Models cß║ºn mß╗Öt c├óu trß║ú lß╗¥i Dß╗¿T KHO├üT chß╗⌐ kh├┤ng phß║úi suy ─æo├ín tß╗½ file: token hß║┐t hß║ín
    m├á refresh hß╗Ång th├¼ `auth.json` vß║½n nß║▒m ─æ├│ nguy├¬n vß║╣n. ─É├óy ─æ├║ng l├á chß╗ù Gemini CLI ─æ├ú g├úy
    khi Google ngß║»t hß║íng c├í nh├ón, v├á Grok Build c┼⌐ng gß║»n quyß╗ün d├╣ng v├áo G├ôI chß╗⌐ kh├┤ng v├áo
    binary - n├¬n c├óu hß╗Åi "chat ─æ╞░ß╗úc ch╞░a" chß╗ë trß║ú lß╗¥i ─æ╞░ß╗úc bß║▒ng c├ích chat thß║¡t mß╗Öt l╞░ß╗út.
    """
    cli = find_grok_cli()
    if not cli:
        return {"ok": False, "error": f"Ch╞░a c├ái Grok CLI ({lenh_cai()})."}
    args = [cli]
    args += permission_cho_mode("suggest")
    if co_co("--output-format"):
        args += ["--output-format", "json"]
    if co_co("--no-auto-update"):
        args.append("--no-auto-update")
    args += ["-p", "Trß║ú lß╗¥i ─æ├║ng mß╗Öt chß╗»: ok"]
    try:
        r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout, creationflags=_no_window(),
                           env=_moi_truong(), cwd=str(Path.home()),
                           stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Grok CLI kh├┤ng trß║ú lß╗¥i kß╗ïp."}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}
    if r.returncode != 0:
        loi = (r.stderr or r.stdout or "").strip()
        l = loi.lower()
        if "xai_api_key" in l or "not authenticated" in l or "unauthorized" in l:
            loi = ("Ch╞░a ─æ─âng nhß║¡p. Bß║Ñm \"─É─âng nhß║¡p\" tr├¬n thß║╗ n├áy, hoß║╖c chß║íy "
                   "`grok login --device-auth`.")
        elif "subscription" in l or "not eligible" in l or "forbidden" in l:
            loi = ("T├ái khoß║ún ─æ─âng nhß║¡p kh├┤ng c├│ quyß╗ün d├╣ng Grok Build. N├│ ─æi k├¿m g├│i SuperGrok "
                   "hoß║╖c X Premium+, kh├┤ng phß║úi cß╗⌐ c├│ API key l├á chß║íy ─æ╞░ß╗úc.")
        return {"ok": False, "error": loi[:400] or f"Tho├ít m├ú {r.returncode}"}
    tho = (r.stdout or "").strip()
    try:
        d = json.loads(tho or "{}")
    except json.JSONDecodeError:
        # Kh├┤ng phß║úi JSON nh╞░ng C├ô chß╗»: bß║ún CLI c┼⌐ ch╞░a c├│ `--output-format`. Vß║½n l├á chß║íy ─æ╞░ß╗úc.
        return {"ok": True, "reply": tho[:200]} if tho else {
            "ok": False,
            "error": ("Grok CLI tho├ít 0 nh╞░ng kh├┤ng in ra g├¼ cß║ú. Thß╗¡ chß║íy tay tr├¬n m├íy chß╗º: "
                      "`grok -p \"ch├áo\" --output-format json`")}
    tra = str(d.get("text") or d.get("response") or "").strip()
    if not tra:
        # S╞í ─æß╗ô JSON kh├íc c├íi Javis ─æo├ín. Vß╗¢t ß╗ƒ mß╗ìi tß║ºng ─æ├ú, rß╗ôi mß╗¢i chß╗ïu thua - v├á nß║┐u chß╗ïu
        # thua th├¼ N├ôI RA nguy├¬n v─ân, ─æß╗½ng b├ío "d├╣ng ─æ╞░ß╗úc" trong khi chat vß║½n ra ├┤ trß╗æng.
        tra = GrokCLI._vot_chu({"raw": [tho]}).strip()
    if tra:
        return {"ok": True, "reply": tra[:200]}
    return {"ok": False,
            "error": ("Grok CLI chß║íy xong nh╞░ng Javis kh├┤ng ─æß╗ìc ra c├óu trß║ú lß╗¥i trong thß╗⌐ n├│ "
                      "in ra. Nguy├¬n v─ân: " + tho[:300])}
