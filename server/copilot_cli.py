"""Bộ não GitHub Copilot CLI (`copilot`) - gói Copilot hoặc token GitHub.

Hai lối kết nối (cùng tinh thần Claude Code / Antigravity + thẻ API):
1. Gói: cài CLI rồi `copilot login` (keyring) - như Antigravity với `agy`.
2. Token: dán fine-grained PAT (quyền Copilot Requests) ở trang Models; Javis đưa vào
   `COPILOT_GITHUB_TOKEN` khi chạy binary - đúng khuyến nghị GitHub cho VPS/headless.

File này bám khuôn `antigravity_cli.py`: probe `copilot --help` trước khi truyền cờ chưa chắc
có, và luôn trả về cùng hợp đồng sự kiện `{tool_call, tool_result, usage, final, error}` để
`main.py` dùng lại được ngay.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
import threading
import time
from pathlib import Path
from typing import AsyncIterator, Optional

from claude_cli import _home_dir, _no_window, tim_binary

MODEL_MAC_DINH = ""
LENH_CAI_NPM = "npm install -g @github/copilot"
LENH_CAI_SHELL = "curl -fsSL https://gh.io/copilot-install | bash"

_HELP_CACHE: dict = {"path": None, "text": "", "ts": 0.0}
_HELP_TTL = 300.0
_HELP_TTL_LOI = 120.0

_AUTH_CACHE: dict = {"ts": 0.0, "val": None}
_AUTH_TTL = 60.0
_AUTH_LAM_MOI = {"dang_chay": False}


def lenh_cai() -> str:
    return LENH_CAI_NPM


def xoa_cache_auth() -> None:
    _AUTH_CACHE.update(ts=0.0, val=None)


def token_tu_cau_hinh(settings: Optional[dict] = None) -> str:
    """Token dán ở trang Models (`model.copilot_github_token`)."""
    try:
        import config as cfgmod
        s = settings if settings is not None else cfgmod.read_settings()
        return str(((s.get("model") or {}).get("copilot_github_token") or "")).strip()
    except Exception:
        return ""


def env_cho_cli(settings: Optional[dict] = None) -> dict:
    """Biến môi trường thêm cho tiến trình `copilot`.

    Nếu máy đã có COPILOT_GITHUB_TOKEN / GH_TOKEN / GITHUB_TOKEN thì không đè.
    Không thì đưa token đã lưu trong settings (nếu có).
    """
    if _env_token()[0]:
        return {}
    k = token_tu_cau_hinh(settings)
    return {"COPILOT_GITHUB_TOKEN": k} if k else {}


def _moi_truong_cli(settings: Optional[dict] = None) -> dict:
    env = os.environ.copy()
    them = env_cho_cli(settings)
    if them:
        env.update(them)
    return env


def find_copilot_cli() -> Optional[str]:
    """Tìm binary `copilot`. Có cửa thoát JAVIS_COPILOT_BIN cho máy cài chỗ lạ."""
    envp = (os.environ.get("JAVIS_COPILOT_BIN") or "").strip()
    if envp:
        try:
            if Path(envp).exists():
                return envp
        except Exception:
            pass
    cli = tim_binary("copilot")
    if cli:
        return cli
    home = _home_dir()
    ung_vien = [
        home / ".local" / "bin" / "copilot",
        home / ".npm-global" / "bin" / "copilot",
        Path("/usr/local/bin/copilot"),
        Path("/opt/homebrew/bin/copilot"),
        Path(os.environ.get("APPDATA", "")) / "npm" / "copilot.cmd",
        Path(os.environ.get("APPDATA", "")) / "npm" / "copilot.exe",
    ]
    for p in ung_vien:
        try:
            if p and str(p) not in ("", ".") and p.exists():
                return str(p)
        except Exception:
            pass
    return None


def _help_text() -> str:
    """Nội dung `copilot --help`, nhớ trong RAM. Rỗng nếu không chạy được."""
    cli = find_copilot_cli()
    if not cli:
        return ""
    now = time.time()
    ttl = _HELP_TTL if _HELP_CACHE["text"] else _HELP_TTL_LOI
    if _HELP_CACHE["path"] == cli and now - _HELP_CACHE["ts"] < ttl:
        return _HELP_CACHE["text"]
    try:
        r = subprocess.run(
            [cli, "--help"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
            creationflags=_no_window(),
            stdin=subprocess.DEVNULL,
            env=_moi_truong_cli(),
        )
        txt = (r.stdout or "") + "\n" + (r.stderr or "")
    except Exception:
        txt = ""
    _HELP_CACHE.update(path=cli, text=txt, ts=now)
    return txt


def co_co(*ten_co: str) -> bool:
    txt = _help_text()
    if not txt:
        return False
    return any(c in txt for c in ten_co)


def _env_token() -> tuple[str, str]:
    for k in ("COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"):
        v = (os.environ.get(k) or "").strip()
        if v:
            return k, v
    return "", ""


def login_huong_dan() -> dict:
    return {
        "cai": LENH_CAI_NPM,
        "cai_shell": LENH_CAI_SHELL,
        "cai_curl": LENH_CAI_SHELL,
        "dang_nhap": "copilot login",
        "ghi_chu": (
            "Hai lối: (1) gói - gõ `copilot login` rồi Kiểm tra lại; "
            "(2) dán fine-grained PAT (quyền Copilot Requests) vào ô token trên thẻ này."
        ),
    }


def _tach_model(doc) -> list[str]:
    if isinstance(doc, dict):
        for k in ("models", "data", "items", "result"):
            if isinstance(doc.get(k), list):
                doc = doc[k]
                break
    if not isinstance(doc, list):
        return []
    ra: list[str] = []
    for m in doc:
        ten = ""
        if isinstance(m, str):
            ten = m.strip()
        elif isinstance(m, dict):
            for k in ("id", "slug", "model", "name", "label", "display_name"):
                v = m.get(k)
                if isinstance(v, str) and v.strip():
                    ten = v.strip()
                    break
        if ten and ten not in ra:
            ra.append(ten)
    return ra


def list_models() -> Optional[list]:
    """Danh sách model hỏi thẳng CLI. None = chưa cài; [] = có CLI nhưng chưa lấy được."""
    cli = find_copilot_cli()
    if not cli:
        return None
    help_txt = _help_text()
    args_list = [[cli, "models", "list"]]
    if "--json" in help_txt or " json" in help_txt.lower():
        args_list.insert(0, [cli, "models", "list", "--json"])
    env = _moi_truong_cli()
    for args in args_list:
        try:
            r = subprocess.run(
                args,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                creationflags=_no_window(),
                stdin=subprocess.DEVNULL,
                env=env,
            )
        except Exception:
            continue
        out = (r.stdout or "").strip()
        if r.returncode != 0 or not out:
            continue
        if out.startswith("{") or out.startswith("["):
            try:
                ds = _tach_model(json.loads(out))
                if ds:
                    return ds
            except Exception:
                pass
        ra: list[str] = []
        for dong in out.splitlines():
            d = dong.strip().lstrip("*->•").strip()
            if not d or d.endswith(":"):
                continue
            d = re.split(r"\t|\s{2,}", d)[0].strip()
            if not d or " " in d or d.lower().startswith("fetch"):
                continue
            if d not in ra:
                ra.append(d)
        if ra:
            return ra
    return []


def auth_status(bo_qua_cache: bool = False) -> dict:
    """Đã có đường đăng nhập Copilot dùng được chưa (gói login, env, hoặc token Models)."""
    cli = find_copilot_cli()
    if not cli:
        return {
            "connected": False,
            "method": "",
            "email": "",
            "error": f"Chưa cài GitHub Copilot CLI. Cài một lần: {LENH_CAI_NPM} hoặc {LENH_CAI_SHELL}",
        }
    now = time.time()
    if not bo_qua_cache and _AUTH_CACHE["val"] and now - _AUTH_CACHE["ts"] < _AUTH_TTL:
        return dict(_AUTH_CACHE["val"])
    env_name, _tok = _env_token()
    if env_name:
        d = {"connected": True, "method": env_name, "email": "", "error": ""}
        _AUTH_CACHE.update(ts=now, val=dict(d))
        return d
    if token_tu_cau_hinh():
        d = {"connected": True, "method": "token (Models)", "email": "", "error": ""}
        _AUTH_CACHE.update(ts=now, val=dict(d))
        return d
    ds = list_models()
    if ds:
        d = {"connected": True, "method": "copilot login", "email": "", "error": ""}
    else:
        d = {
            "connected": False,
            "method": "",
            "email": "",
            "error": (
                "Đã cài GitHub Copilot CLI nhưng chưa kết nối. "
                "Gõ `copilot login` trên máy chạy Javis, hoặc dán fine-grained PAT "
                "(quyền Copilot Requests) vào ô token trên thẻ Models."
            ),
        }
    _AUTH_CACHE.update(ts=now, val=dict(d))
    return d


def auth_status_nen() -> dict:
    """Bản hot-path cho dashboard: trả cache ngay, làm mới ở nền."""
    cli = find_copilot_cli()
    if not cli:
        return {
            "connected": False,
            "method": "",
            "email": "",
            "error": f"Chưa cài GitHub Copilot CLI. Cài một lần: {LENH_CAI_NPM} hoặc {LENH_CAI_SHELL}",
        }
    if token_tu_cau_hinh():
        return {"connected": True, "method": "token (Models)", "email": "", "error": ""}
    now = time.time()
    cu = _AUTH_CACHE["val"]
    if cu and now - _AUTH_CACHE["ts"] < _AUTH_TTL:
        return dict(cu)
    if not _AUTH_LAM_MOI["dang_chay"]:
        _AUTH_LAM_MOI["dang_chay"] = True

        def _lam_moi():
            try:
                auth_status(bo_qua_cache=True)
            finally:
                _AUTH_LAM_MOI["dang_chay"] = False

        threading.Thread(target=_lam_moi, daemon=True, name="copilot-auth-refresh").start()
    if cu:
        return dict(cu)
    return {
        "connected": False,
        "method": "",
        "email": "",
        "error": "Đang kiểm tra phiên Copilot…",
    }


def co_quyen_cho_mode(mode: Optional[str]) -> list[str]:
    """Mode full -> tự duyệt tool nếu binary có cờ. Mọi mode khác giữ chặt."""
    m = str(mode or "").strip().lower()
    if m != "full":
        return []
    if co_co("--allow-all-tools"):
        return ["--allow-all-tools"]
    if co_co("--allow-all"):
        return ["--allow-all"]
    return []


def hub_entry(url: str, headers: Optional[dict] = None) -> dict:
    e = {"type": "http", "url": str(url or "")}
    if headers:
        e["headers"] = {str(k): str(v) for k, v in headers.items()}
    return e


def _duong_mcp_local(vault_root) -> Optional[Path]:
    if not vault_root:
        return None
    try:
        return Path(vault_root).expanduser() / ".copilot" / "javis-mcp-config.json"
    except Exception:
        return None


def _duong_mcp_home() -> Path:
    return _home_dir() / ".copilot" / "mcp-config.json"


def _doc_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def _ghi_mot_mcp(p: Path, hub: Optional[dict]) -> bool:
    cu = _doc_json(p) if p.exists() else {}
    if not isinstance(cu, dict):
        cu = {}
    servers = cu.get("servers")
    if not isinstance(servers, dict):
        servers = {}
    if hub:
        servers["javis"] = hub
    else:
        servers.pop("javis", None)
    if servers:
        cu["servers"] = servers
    else:
        cu.pop("servers", None)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(cu, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        os.chmod(p, 0o600)
    except Exception:
        pass
    return True


def ghi_mcp_settings(vault_root, hub: Optional[dict]) -> Optional[str]:
    """Ghi file MCP cho Copilot. Ưu tiên file riêng của brain, vẫn cập nhật HOME làm dự phòng."""
    ra = None
    for p in [_duong_mcp_local(vault_root), _duong_mcp_home()]:
        if p is None:
            continue
        try:
            if _ghi_mot_mcp(p, hub) and ra is None:
                ra = str(p)
        except Exception:
            pass
    return ra


def trang_thai_mcp(vault_root=None) -> dict:
    ds = []
    for p in [_duong_mcp_local(vault_root), _duong_mcp_home()]:
        if p is None:
            continue
        doc = _doc_json(p) if p.exists() else {}
        e = ((doc.get("servers") or {}).get("javis") or {}) if isinstance(doc, dict) else {}
        ds.append({
            "path": str(p),
            "co_javis": bool(e.get("url")),
            "type": str(e.get("type") or ""),
            "url": str(e.get("url") or ""),
        })
    return {"ok": any(x["co_javis"] for x in ds), "files": ds}


def _tran_argv() -> int:
    return 28000 if os.name == "nt" else 120000


def _do_dai_argv(s: str) -> int:
    s = str(s or "")
    if os.name == "nt":
        return len(s.encode("utf-16-le", errors="replace")) // 2
    return len(s.encode("utf-8", errors="replace"))


class CopilotCLI:
    """Một lượt chạy `copilot` headless. Hợp đồng sự kiện giống Antigravity/Grok."""

    def __init__(self, cwd: Optional[str] = None, tag: str = "chat", model: Optional[str] = None,
                 instructions: Optional[str] = None):
        self.provider = "copilot-cli"
        self.cli_path = find_copilot_cli()
        self.cwd = cwd or os.getcwd()
        self.tag = tag
        self.model = model
        self.instructions = instructions
        self.session_id = None
        self.mode = "suggest"
        self.mcp_config: Optional[str] = None
        self.extra_args: list[str] = []
        self.timeout = float(os.environ.get("JAVIS_COPILOT_TIMEOUT") or 900)

    def is_available(self) -> bool:
        return self.cli_path is not None

    def _co_model_flag(self) -> str:
        txt = _help_text()
        if "--model=" in txt:
            return "--model="
        if "--model" in txt:
            return "--model="
        return ""

    def _build_args(self, prompt_argv: Optional[str]) -> list[str]:
        args = [self.cli_path]
        model_flag = self._co_model_flag()
        if self.model and model_flag:
            if model_flag.endswith("="):
                args.append(f"{model_flag}{self.model}")
            else:
                args += [model_flag, str(self.model)]
        if co_co("-s", "--silent"):
            args.append("-s" if "-s" in (_help_text() or "") else "--silent")
        if co_co("--no-ask-user"):
            args.append("--no-ask-user")
        args += co_quyen_cho_mode(self.mode)
        if self.mcp_config and co_co("--additional-mcp-config"):
            args.append(f"--additional-mcp-config=@{self.mcp_config}")
        args += list(self.extra_args)
        if prompt_argv is not None and co_co("-p", "--prompt"):
            args += ["-p", prompt_argv]
        return args

    def _chon_stdin(self, full: str) -> bool:
        do_dai = _do_dai_argv(full) + sum(_do_dai_argv(a) + 3 for a in self._build_args(""))
        return do_dai > _tran_argv()

    async def query(self, prompt: str) -> AsyncIterator[dict]:
        if not self.cli_path:
            yield {
                "type": "error",
                "content": (
                    "Không tìm thấy GitHub Copilot CLI (`copilot`). Cài một lần:\n\n"
                    f"`{LENH_CAI_NPM}`\n\nHoặc:\n\n`{LENH_CAI_SHELL}`"
                ),
            }
            return
        full = (self.instructions.strip() + "\n\n" + prompt) if self.instructions else prompt
        dung_stdin = await asyncio.to_thread(self._chon_stdin, full)
        args = self._build_args(None if dung_stdin else full)

        loop = asyncio.get_running_loop()
        hang: asyncio.Queue = asyncio.Queue()
        HET = object()

        def doc_luong():
            proc = None
            try:
                proc = subprocess.Popen(
                    args,
                    stdin=subprocess.PIPE if dung_stdin else subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=self.cwd,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    bufsize=1,
                    creationflags=_no_window(),
                    start_new_session=(os.name != "nt"),
                    env=_moi_truong_cli(),
                )
                try:
                    if dung_stdin and proc.stdin is not None:
                        proc.stdin.write(full)
                        proc.stdin.close()
                except Exception:
                    pass
                for line in iter(proc.stdout.readline, ""):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        loop.call_soon_threadsafe(hang.put_nowait, json.loads(line))
                    except json.JSONDecodeError:
                        loop.call_soon_threadsafe(hang.put_nowait, {"_raw": line})
                err = ""
                try:
                    err = (proc.stderr.read() or "").strip()
                except Exception:
                    pass
                try:
                    ma = proc.wait(timeout=self.timeout)
                except subprocess.TimeoutExpired:
                    loop.call_soon_threadsafe(
                        hang.put_nowait,
                        {"_exit": -1, "_err": f"GitHub Copilot CLI chạy quá {int(self.timeout)}s nên bị cắt."},
                    )
                    return
                if ma != 0 or err:
                    loop.call_soon_threadsafe(hang.put_nowait, {"_exit": ma, "_err": err})
            except Exception as e:
                loop.call_soon_threadsafe(
                    hang.put_nowait, {"_exit": -1, "_err": f"{type(e).__name__}: {e}"},
                )
            finally:
                try:
                    if proc and proc.poll() is None:
                        proc.terminate()
                except Exception:
                    pass
                loop.call_soon_threadsafe(hang.put_nowait, HET)

        threading.Thread(target=doc_luong, name=f"javis-copilot-{self.tag}", daemon=True).start()

        cac_manh: list[str] = []
        da_loi = False
        while True:
            ev = await hang.get()
            if ev is HET:
                break
            for ra in self._doi_su_kien(ev, cac_manh):
                if ra.get("type") == "error":
                    da_loi = True
                yield ra
        text = "".join(cac_manh).strip()
        if text:
            yield {"type": "final", "content": text}
        elif not da_loi:
            yield {"type": "error", "content": "GitHub Copilot CLI chạy xong nhưng không trả nội dung nào."}

    def _doi_su_kien(self, ev: dict, cac_manh: list[str]) -> list[dict]:
        if "_raw" in ev:
            cac_manh.append(str(ev["_raw"]))
            return []
        if "_exit" in ev:
            loi = str(ev.get("_err") or "").strip()
            if ev.get("_exit") == 0 and not loi:
                return []
            if _la_loi_chua_dang_nhap(loi):
                return [{
                    "type": "error",
                    "content": "GitHub Copilot CLI chưa đăng nhập. Gõ `copilot login` hoặc đặt token GitHub vào môi trường.",
                }]
            return [{"type": "error", "content": loi[:1500] or f"GitHub Copilot CLI thoát mã {ev.get('_exit')}."}]

        t = str(ev.get("type") or ev.get("event") or "").lower()
        if t in ("tool_call", "tool_use", "tool"):
            return [{
                "type": "tool_call",
                "name": str(ev.get("name") or ev.get("tool_name") or ev.get("toolName") or ""),
                "id": str(ev.get("id") or ev.get("tool_id") or ev.get("toolCallId") or ""),
                "input": ev.get("input") or ev.get("parameters") or ev.get("rawInput") or {},
            }]
        if t in ("tool_result", "tool_output", "tool_call_update"):
            return [{
                "type": "tool_result",
                "id": str(ev.get("id") or ev.get("tool_id") or ev.get("toolCallId") or ""),
                "status": str(ev.get("status") or ""),
                "content": str(ev.get("content") or ev.get("output") or ev.get("rawOutput") or "")[:2000],
            }]
        if t == "usage":
            return [{
                "type": "usage",
                "input_tokens": int(ev.get("input_tokens") or ev.get("prompt_tokens") or ev.get("input") or 0),
                "output_tokens": int(ev.get("output_tokens") or ev.get("completion_tokens") or ev.get("output") or 0),
                "total_tokens": int(ev.get("total_tokens") or ev.get("total") or 0),
                "cached": int(ev.get("cached") or 0),
            }]
        if t == "error":
            tin = str(ev.get("message") or ev.get("error") or "GitHub Copilot CLI lỗi.")
            if isinstance(ev.get("error"), dict):
                tin = str(ev["error"].get("message") or tin)
            if _la_loi_chua_dang_nhap(tin):
                tin = "GitHub Copilot CLI chưa đăng nhập. Gõ `copilot login` hoặc dán token trên trang Models."
            return [{"type": "error", "content": tin[:1500]}]

        ra = []
        if t in ("result", "final", "done", "complete"):
            st = ev.get("usage") or ev.get("stats") or {}
            if isinstance(st, dict) and st:
                ra.append({
                    "type": "usage",
                    "input_tokens": int(st.get("input_tokens") or st.get("prompt_tokens") or st.get("input") or 0),
                    "output_tokens": int(st.get("output_tokens") or st.get("completion_tokens") or st.get("output") or 0),
                    "total_tokens": int(st.get("total_tokens") or st.get("total") or 0),
                    "cached": int(st.get("cached") or 0),
                })
            if not cac_manh:
                for k in ("text", "content", "message", "response", "output"):
                    v = ev.get(k)
                    if isinstance(v, str) and v:
                        cac_manh.append(v)
                        break
            return ra

        if str(ev.get("role") or "").lower() in ("assistant", "model", "agent"):
            for k in ("text", "content", "message", "response", "output"):
                v = ev.get(k)
                if isinstance(v, str) and v:
                    cac_manh.append(v)
                    return []
        if t in ("content", "message", "text", "assistant"):
            for k in ("text", "content", "delta", "message", "response", "output"):
                v = ev.get(k)
                if isinstance(v, str) and v:
                    cac_manh.append(v)
                    return []
        return ra


def _la_loi_chua_dang_nhap(loi: str) -> bool:
    l = (loi or "").lower()
    return any(k in l for k in (
        "not logged in", "not signed in", "authentication required", "sign in",
        "please login", "please log in", "run copilot login", "401", "unauthorized",
    ))


def kiem_tra_nhanh(timeout: float = 60.0) -> dict:
    """Chạy thử một lượt ngắn cho nút Kiểm tra lại."""
    cli = find_copilot_cli()
    if not cli:
        return {"ok": False, "error": f"Chưa cài GitHub Copilot CLI. {LENH_CAI_NPM}"}
    st = auth_status()
    if not st.get("connected"):
        return {"ok": False, "error": st.get("error") or "Chưa đăng nhập."}
    args = [cli]
    if co_co("-s", "--silent"):
        args.append("-s" if "-s" in (_help_text() or "") else "--silent")
    if co_co("--no-ask-user"):
        args.append("--no-ask-user")
    args += ["-p", "Trả lời đúng một chữ: ok"]
    try:
        r = subprocess.run(
            args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            creationflags=_no_window(),
            stdin=subprocess.DEVNULL,
            env=_moi_truong_cli(),
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "GitHub Copilot CLI không trả lời kịp."}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}
    out = (r.stdout or "").strip()
    if r.returncode != 0:
        loi = (r.stderr or out or "").strip()
        if _la_loi_chua_dang_nhap(loi):
            return {"ok": False, "error": "Chưa đăng nhập. Gõ `copilot login` hoặc đặt token GitHub."}
        return {"ok": False, "error": loi[:400] or f"Thoát mã {r.returncode}"}
    if not out:
        return {"ok": False, "error": "CLI chạy xong nhưng không in ra gì."}
    return {"ok": True, "reply": out[:200]}
