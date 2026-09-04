"""Bộ não thứ 11: xAI Grok Build CLI (binary `grok`) - gói SuperGrok / X Premium+.

Đối xứng với `gemini_cli.py` / `antigravity_cli.py`: Javis không sở hữu token, chỉ gọi đúng
binary `grok` trên máy và mượn phiên mà chính CLI giữ trong `~/.grok/auth.json` (quyền 0600).

**Đo, không đoán (trong tầm có thể).** Tài liệu chính chủ (docs.x.ai/build, npm `@xai-official/grok`)
đã đủ để chốt: lệnh cài, chỗ credential, MCP qua `[mcp_servers.*]` với khoá `url`, headless
`-p` + `--output-format streaming-json`, nối mạch bằng `--resume`, device auth bằng
`grok login --device-auth`. Cờ phụ (vd `--yolo`) vẫn dò qua `--help` trước khi truyền, để bản
CLI cũ không chết vì "unknown flag".

Quyền dùng Grok Build gắn vào GÓI (SuperGrok / X Premium+), không chỉ vào binary - đúng hạng
chuyện đã làm Gemini CLI chết lặng khi Google ngắt hạng cá nhân. Nên `kiem_tra_nhanh` chạy
thật một lượt, không suy từ file.
"""
from __future__ import annotations

import asyncio
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

# Hạt giống khi `grok models` chưa kịp trả - không phải bảng chân lý.
MODELS_MAC_DINH = ["grok-4.6", "grok-4", "grok-3"]
MODEL_MAC_DINH = "grok-4.6"

LENH_CAI = {
    "linux": "curl -fsSL https://x.ai/cli/install.sh | bash",
    "mac": "curl -fsSL https://x.ai/cli/install.sh | bash",
    "windows": "irm https://x.ai/cli/install.ps1 | iex",
}
# Đường npm dự phòng (cùng gói chính chủ trên npmjs: @xai-official/grok).
LENH_CAI_NPM = "npm i -g @xai-official/grok"

# mức quyền Javis -> cờ duyệt của Grok (chỉ thêm khi --help khai).
# full: --yolo / --always-approve. suggest/auto: không truyền (CLI hỏi hoặc chặn theo mặc định).
_QUYEN_FULL = ("--yolo", "--always-approve")

_HELP_CACHE: dict = {"path": None, "text": "", "ts": 0.0}
_HELP_TTL = 300.0

# Vòng device-auth đang chạy (một máy một vòng).
_LOGIN: dict = {
    "proc": None,
    "uri": "",
    "code": "",
    "err": "",
    "started": 0.0,
    "done": False,
    "ok": False,
}


def lenh_cai() -> str:
    """Lệnh cài Grok Build CLI cho OS hiện tại (in ra thẻ Models để người dùng chép)."""
    if os.name == "nt":
        return LENH_CAI["windows"]
    return LENH_CAI["linux"]


def find_grok_cli() -> Optional[str]:
    """Tìm binary `grok`. Cửa thoát JAVIS_GROK_BIN cho máy cài chỗ lạ.

    Trình cài chính chủ thả vào `~/.local/bin/grok`; systemd / app macOS thường không có thư
    mục đó trong PATH nên phải soi tay, đúng bài học của `agy`.
    """
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
    ung_vien = [
        home / ".local" / "bin" / "grok",
        home / ".grok" / "bin" / "grok",
        home / ".npm-global" / "bin" / "grok",
        Path("/usr/local/bin/grok"),
        Path("/opt/homebrew/bin/grok"),
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "grok" / "grok.exe",
        Path(os.environ.get("APPDATA", "")) / "npm" / "grok.cmd",
        Path(os.environ.get("APPDATA", "")) / "npm" / "grok.exe",
    ]
    for p in ung_vien:
        try:
            if p and str(p) not in (".", "") and p.exists():
                return str(p)
        except Exception:
            pass
    return None


def _grok_home() -> Path:
    env = (os.environ.get("GROK_HOME") or "").strip()
    if env:
        try:
            return Path(env).expanduser()
        except Exception:
            pass
    return _home_dir() / ".grok"


def _doc_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _help_text() -> str:
    """Nội dung `grok --help`, nhớ trong RAM. Rỗng nếu không chạy được."""
    cli = find_grok_cli()
    if not cli:
        return ""
    now = time.time()
    if (_HELP_CACHE["path"] == cli and _HELP_CACHE["text"]
            and now - _HELP_CACHE["ts"] < _HELP_TTL):
        return _HELP_CACHE["text"]
    try:
        r = subprocess.run(
            [cli, "--help"], capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=20, creationflags=_no_window(),
        )
        txt = (r.stdout or "") + "\n" + (r.stderr or "")
    except Exception:
        txt = ""
    _HELP_CACHE.update(path=cli, text=txt, ts=now)
    return txt


def co_co(*ten_co: str) -> bool:
    """Binary trên máy CÓ khai cờ này không (`--help` nhắc tới nó)."""
    txt = _help_text()
    if not txt:
        return False
    return any(c in txt for c in ten_co)


def _toml_str(s: str) -> str:
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


# ---------------------------------------------------------------------------
# Đăng nhập / trạng thái
# ---------------------------------------------------------------------------
def auth_status() -> dict:
    """Đã đăng nhập xAI cho Grok Build chưa: {connected, method, account, plan, error}.

    ĐỌC FILE, không gọi CLI. `~/.grok/auth.json` là kho credential chính chủ (0600); trang
    Models gọi hàm này mỗi lần mở - đẻ tiến trình mỗi lần là phí và rủi ro treo.
    """
    cli = find_grok_cli()
    if not cli:
        return {
            "connected": False, "method": "", "account": "", "plan": "", "email": "",
            "error": f"Chưa cài Grok Build CLI. Cài một lần: `{lenh_cai()}` "
                     f"(hoặc `{LENH_CAI_NPM}`).",
        }
    if (os.environ.get("XAI_API_KEY") or "").strip():
        # API key là fallback khi không có session (docs.x.ai). Coi là đã cấu hình.
        return {
            "connected": True, "method": "XAI_API_KEY", "account": "", "plan": "",
            "email": "", "error": "",
        }
    auth_p = _grok_home() / "auth.json"
    raw = _doc_json(auth_p)
    if not isinstance(raw, dict):
        return {
            "connected": False, "method": "", "account": "", "plan": "", "email": "",
            "error": "Đã cài Grok Build CLI nhưng chưa đăng nhập. Bấm \"Đăng nhập\" trên thẻ "
                     "Grok (chạy được cả trên VPS: in ra link + mã).",
        }
    token = (raw.get("access_token") or raw.get("accessToken")
             or raw.get("token") or raw.get("session_token") or "")
    refresh = raw.get("refresh_token") or raw.get("refreshToken") or ""
    if not (token or refresh):
        # Một số bản bọc token trong object con.
        for k in ("credentials", "auth", "session", "oauth"):
            sub = raw.get(k)
            if isinstance(sub, dict) and (
                    sub.get("access_token") or sub.get("refresh_token")
                    or sub.get("accessToken") or sub.get("token")):
                token = sub.get("access_token") or sub.get("accessToken") or sub.get("token") or ""
                refresh = sub.get("refresh_token") or sub.get("refreshToken") or refresh
                raw = {**raw, **sub}
                break
    if not (token or refresh):
        return {
            "connected": False, "method": "", "account": "", "plan": "", "email": "",
            "error": "Có `~/.grok/auth.json` nhưng thiếu token. Chạy lại đăng nhập trên thẻ Grok.",
        }
    email = str(raw.get("email") or raw.get("user_email") or raw.get("account") or "")
    plan = str(raw.get("plan") or raw.get("subscription") or raw.get("tier") or "")
    account = str(raw.get("name") or raw.get("username") or email or "")
    method = str(raw.get("method") or raw.get("auth_method") or "oauth (auth.json)")
    return {
        "connected": True, "method": method, "account": account, "plan": plan,
        "email": email, "error": "",
    }


def login_huong_dan() -> dict:
    """Hướng dẫn đăng nhập - đường terminal dự phòng khi không dùng nút trên dashboard."""
    return {
        "cai": lenh_cai(),
        "cai_npm": LENH_CAI_NPM,
        "dang_nhap": "grok login --device-auth",
        "ghi_chu": (
            "Trên máy có trình duyệt: chạy `grok` hoặc `grok login` rồi làm theo. "
            "Trên VPS / SSH: `grok login --device-auth` - CLI in ra một link và một mã, "
            "mở link trên máy của bạn, nhập mã, xong. Tài liệu: https://docs.x.ai/build/overview"
        ),
    }


def chan_doan() -> dict:
    """Chẩn đoán an toàn cho trang Models: chỉ TÊN file / TÊN khoá, không giá trị token."""
    home = _grok_home()
    auth_p = home / "auth.json"
    ra: dict = {
        "cli_path": find_grok_cli() or "",
        "grok_home": str(home),
        "auth_file": str(auth_p),
        "auth_exists": False,
        "auth_keys": [],
        "env_XAI_API_KEY": bool((os.environ.get("XAI_API_KEY") or "").strip()),
        "env_JAVIS_GROK_BIN": bool((os.environ.get("JAVIS_GROK_BIN") or "").strip()),
    }
    try:
        if auth_p.exists():
            ra["auth_exists"] = True
            try:
                st = auth_p.stat()
                ra["auth_mode"] = oct(st.st_mode & 0o777)
            except Exception:
                pass
            raw = _doc_json(auth_p)
            if isinstance(raw, dict):
                ra["auth_keys"] = sorted(str(k) for k in raw.keys())
            else:
                ra["auth_parse"] = "khong-phai-object-json"
    except Exception as e:
        ra["loi"] = f"{type(e).__name__}: {e}"
    return ra


def _boc_device_auth(text: str) -> tuple[str, str]:
    """Lấy (verification_uri, user_code) từ chữ CLI in ra. Rỗng nếu chưa thấy."""
    uri = ""
    code = ""
    if not text:
        return uri, code
    m = re.search(r"https?://[^\s\]\)\"'<>]+", text)
    if m:
        uri = m.group(0).rstrip(".,;")
    # Mã device thường dạng ABCD-EFGH / XXXX-XXXX; tránh nuốt cả URL.
    for pat in (
        r"(?:code|mã|enter)\s*[:=]?\s*([A-Z0-9]{4,8}(?:-[A-Z0-9]{4,8})+)",
        r"\b([A-Z0-9]{4,5}-[A-Z0-9]{4,5})\b",
    ):
        m2 = re.search(pat, text, re.I)
        if m2:
            code = m2.group(1).upper()
            break
    return uri, code


def _login_doc_luong(proc: subprocess.Popen) -> None:
    """Đọc stdout/stderr của `grok login --device-auth` tới khi có link+mã hoặc tiến trình chết."""
    buf: list[str] = []
    try:
        assert proc.stdout is not None
        for line in iter(proc.stdout.readline, ""):
            buf.append(line)
            gop = "".join(buf)
            uri, code = _boc_device_auth(gop)
            if uri:
                _LOGIN["uri"] = uri
            if code:
                _LOGIN["code"] = code
            if _LOGIN["uri"] and _LOGIN["code"]:
                break
            if proc.poll() is not None:
                break
        try:
            rest = proc.stdout.read() or ""
            if rest:
                buf.append(rest)
        except Exception:
            pass
        gop = "".join(buf)
        uri, code = _boc_device_auth(gop)
        if uri:
            _LOGIN["uri"] = uri
        if code:
            _LOGIN["code"] = code
        ma = proc.wait(timeout=600)
        _LOGIN["done"] = True
        _LOGIN["ok"] = (ma == 0) or auth_status().get("connected")
        if ma != 0 and not _LOGIN["ok"]:
            _LOGIN["err"] = (gop[-800:] or f"thoát mã {ma}").strip()
    except Exception as e:
        _LOGIN["done"] = True
        _LOGIN["ok"] = False
        _LOGIN["err"] = f"{type(e).__name__}: {e}"
    finally:
        try:
            if proc.poll() is None:
                proc.terminate()
        except Exception:
            pass


def login_start() -> dict:
    """Bước 1: mở `grok login --device-auth`, trả link + mã cho dashboard.

    CLI tự đứng poll tới khi người dùng xác nhận trên web; Javis không nhận mã dán ngược.
    Giao diện gọi `login_trang_thai()` để biết đã xong chưa.
    """
    cli = find_grok_cli()
    if not cli:
        return {
            "ok": False,
            "error": f"Chưa cài Grok Build CLI. Cài: `{lenh_cai()}` (hoặc `{LENH_CAI_NPM}`).",
        }
    # Hạ vòng cũ nếu còn.
    cu = _LOGIN.get("proc")
    if cu is not None:
        try:
            if cu.poll() is None:
                cu.terminate()
        except Exception:
            pass
    _LOGIN.update(proc=None, uri="", code="", err="", started=time.time(),
                  done=False, ok=False)
    try:
        proc = subprocess.Popen(
            [cli, "login", "--device-auth"],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace", bufsize=1,
            creationflags=_no_window(), start_new_session=(os.name != "nt"),
        )
    except Exception as e:
        return {"ok": False, "error": f"Không chạy được `grok login --device-auth`: "
                                      f"{type(e).__name__}: {e}"}
    _LOGIN["proc"] = proc
    threading.Thread(target=_login_doc_luong, args=(proc,),
                     name="javis-grok-login", daemon=True).start()
    # Chờ một nhịp ngắn để CLI kịp in link+mã (thường < 2s).
    deadline = time.time() + 8.0
    while time.time() < deadline:
        if _LOGIN["uri"] and _LOGIN["code"]:
            break
        if _LOGIN["done"]:
            break
        time.sleep(0.2)
    if _LOGIN["err"] and not (_LOGIN["uri"] or auth_status().get("connected")):
        return {"ok": False, "error": _LOGIN["err"][:500]}
    if auth_status().get("connected") and _LOGIN["done"]:
        return {"ok": True, "status": "connected",
                "verification_uri": _LOGIN["uri"], "user_code": _LOGIN["code"]}
    if not _LOGIN["uri"]:
        # Vẫn trả ok để UI poll - một số bản in chậm hoặc chỉ hiện mã trong TUI.
        return {
            "ok": True, "status": "pending",
            "verification_uri": _LOGIN["uri"] or "https://accounts.x.ai/device",
            "user_code": _LOGIN["code"],
            "ghi_chu": ("CLI đang chạy device-auth. Nếu không thấy mã trên trang, mở terminal "
                        "máy chạy Javis và xem output của `grok login --device-auth`."),
        }
    return {
        "ok": True, "status": "pending",
        "verification_uri": _LOGIN["uri"],
        "user_code": _LOGIN["code"],
    }


def login_trang_thai() -> dict:
    """Bước 2: vòng đăng nhập tới đâu. Dashboard hỏi lặp lại sau login_start."""
    st = auth_status()
    if st.get("connected"):
        return {"status": "connected", "ok": True, **{k: st.get(k, "")
                for k in ("method", "account", "plan", "email")}}
    proc = _LOGIN.get("proc")
    song = bool(proc is not None and proc.poll() is None)
    if _LOGIN.get("done") and not st.get("connected"):
        return {
            "status": "error", "ok": False,
            "error": (_LOGIN.get("err") or "Đăng nhập chưa thành công.").strip()[:500],
            "verification_uri": _LOGIN.get("uri") or "",
            "user_code": _LOGIN.get("code") or "",
        }
    if not song and not _LOGIN.get("started"):
        return {"status": "idle", "ok": False, "error": "Chưa bắt đầu đăng nhập."}
    return {
        "status": "pending", "ok": True,
        "verification_uri": _LOGIN.get("uri") or "",
        "user_code": _LOGIN.get("code") or "",
    }


def logout() -> dict:
    """Ngắt tài khoản xAI khỏi máy này (`grok logout`)."""
    cli = find_grok_cli()
    if not cli:
        # Vẫn cố gỡ file credential nếu còn sót.
        try:
            p = _grok_home() / "auth.json"
            if p.exists():
                p.unlink()
                return {"ok": True, "method": "xoa-auth.json",
                        "message": "Đã xoá `~/.grok/auth.json` (không có binary `grok`)."}
            return {"ok": True, "message": "Không có binary `grok` và cũng không còn auth.json."}
        except Exception as e:
            return {"ok": False, "error": f"{type(e).__name__}: {e}"}
    try:
        r = subprocess.run(
            [cli, "logout"], capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=30, creationflags=_no_window(),
        )
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}
    if r.returncode != 0:
        loi = (r.stderr or r.stdout or "").strip()
        return {"ok": False, "error": loi[:400] or f"Thoát mã {r.returncode}"}
    return {"ok": True, "message": "Đã đăng xuất Grok Build CLI."}


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------
def list_models() -> Optional[list]:
    """Danh sách model hỏi thẳng CLI. None = chưa cài; [] = hỏi được nhưng rỗng/lỗi."""
    cli = find_grok_cli()
    if not cli:
        return None
    # `grok models` (docs / cheat sheet). Thử --json nếu help có.
    args_list = [[cli, "models", "--json"], [cli, "models", "--output-format", "json"],
                 [cli, "models"]]
    for args in args_list:
        if "--json" in args and not co_co("--json"):
            continue
        if "--output-format" in args and not co_co("--output-format"):
            continue
        try:
            r = subprocess.run(
                args, capture_output=True, text=True, encoding="utf-8",
                errors="replace", timeout=30, creationflags=_no_window(),
            )
        except Exception:
            continue
        if r.returncode != 0:
            continue
        out = (r.stdout or "").strip()
        if not out:
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
    return list(MODELS_MAC_DINH)


def _tach_model(obj) -> list[str]:
    ra: list[str] = []
    if isinstance(obj, list):
        for it in obj:
            if isinstance(it, str) and it.strip():
                ra.append(it.strip())
            elif isinstance(it, dict):
                ten = str(it.get("id") or it.get("name") or it.get("model") or "").strip()
                if ten and ten not in ra:
                    ra.append(ten)
    elif isinstance(obj, dict):
        for k in ("models", "data", "items"):
            if k in obj:
                return _tach_model(obj[k])
        for ten in obj.keys():
            if isinstance(ten, str) and ten and " " not in ten and ten not in ra:
                ra.append(ten)
    return ra


# ---------------------------------------------------------------------------
# MCP: hub Javis vào `.grok/config.toml` của THƯ MỤC LÀM VIỆC (brain)
# ---------------------------------------------------------------------------
def hub_entry(hub_url: str, headers: dict) -> dict:
    """Hình dạng entry MCP mà Grok Build đọc được.

    Grok dùng khoá `url` (+ `headers`). Gemini CLI dùng `httpUrl`, `agy` dùng `serverUrl` -
    chép nhầm khoá là bộ não chạy trơn mà không có lấy một tool nào.
    """
    return {
        "url": str(hub_url or ""),
        "headers": {str(k): str(v) for k, v in (headers or {}).items()},
        "startup_timeout_sec": 20,
    }


def _mcp_config_path(vault_root) -> Path:
    return Path(vault_root).expanduser() / ".grok" / "config.toml"


def _go_section_mcp_javis(text: str) -> str:
    """Gỡ khối `[mcp_servers.javis]` và mọi `[mcp_servers.javis.*]` khỏi TOML (giữ phần còn)."""
    if not text:
        return ""
    lines = text.splitlines(keepends=True)
    ra: list[str] = []
    bo = False
    for line in lines:
        s = line.strip()
        if s.startswith("[") and s.endswith("]"):
            ten = s[1:-1].strip()
            bo = (ten == "mcp_servers.javis"
                  or ten.startswith("mcp_servers.javis."))
        if not bo:
            ra.append(line)
    return "".join(ra).rstrip() + ("\n" if ra else "")


def _viet_mcp_javis(hub: dict) -> str:
    """Một khối TOML `[mcp_servers.javis]` đúng format docs.x.ai."""
    lines = ["[mcp_servers.javis]", f"url = {_toml_str(hub.get('url') or '')}"]
    try:
        timeout = int(hub.get("startup_timeout_sec") or 20)
    except Exception:
        timeout = 20
    lines.append(f"startup_timeout_sec = {timeout}")
    headers = hub.get("headers") or {}
    if isinstance(headers, dict) and headers:
        lines.append("")
        lines.append("[mcp_servers.javis.headers]")
        for hk, hv in headers.items():
            # Khoá có dấu gạch / chữ hoa -> quote cho chắc.
            key = str(hk)
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
                lines.append(f"{key} = {_toml_str(hv)}")
            else:
                lines.append(f"{_toml_str(key)} = {_toml_str(hv)}")
    return "\n".join(lines) + "\n"


def ghi_mcp_settings(vault_root, hub: Optional[dict]) -> Optional[str]:
    """Ghi `<vault>/.grok/config.toml` với entry MCP `javis` (hoặc gỡ nếu hub=None).

    Ghi vào brain chứ không vào `~/.grok/config.toml`: file HOME là của người dùng; nhiều brain
    thì brain nọ đọc header brain kia. Grok đọc project `.grok/config.toml` từ cwd lên - Javis
    luôn chạy với cwd = gốc brain.
    """
    if not vault_root:
        return None
    try:
        p = _mcp_config_path(vault_root)
        cu = ""
        if p.exists():
            try:
                cu = p.read_text(encoding="utf-8")
            except Exception:
                cu = ""
        cu = _go_section_mcp_javis(cu)
        if hub:
            if cu and not cu.endswith("\n"):
                cu += "\n"
            if cu:
                cu += "\n"
            cu += _viet_mcp_javis(hub)
        p.parent.mkdir(parents=True, exist_ok=True)
        if cu.strip():
            p.write_text(cu, encoding="utf-8")
        elif p.exists():
            # Không còn gì - xoá file rỗng cho sạch.
            try:
                p.unlink()
            except Exception:
                p.write_text("", encoding="utf-8")
        try:
            if p.exists():
                os.chmod(p, 0o600)   # chứa hub token trong headers
        except Exception:
            pass
        return str(p) if p.exists() else None
    except Exception as e:
        print(f"[grok mcp settings] {e}", file=sys.stderr)
        return None


def trang_thai_mcp(vault_root) -> dict:
    """Đọc lại file MCP vừa ghi: có entry javis + khoá `url` không.

    Canh đúng hạng lỗi đã lọt lưới với `agy`: ghi thành công nhưng sai chỗ / sai khoá thì CLI
    chạy trơn mà không có tool Javis, và không câu lỗi nào để lần.
    """
    ra: dict = {"co_javis": False, "path": "", "keys": [], "url_ok": False, "loi": ""}
    if not vault_root:
        ra["loi"] = "thieu vault_root"
        return ra
    p = _mcp_config_path(vault_root)
    ra["path"] = str(p)
    if not p.exists():
        ra["loi"] = "chua-co-file"
        return ra
    try:
        import tomllib
        data = tomllib.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        ra["loi"] = f"doc-toml: {type(e).__name__}: {e}"
        return ra
    servers = data.get("mcp_servers") if isinstance(data, dict) else None
    if not isinstance(servers, dict):
        ra["loi"] = "thieu-mcp_servers"
        return ra
    javis = servers.get("javis")
    if not isinstance(javis, dict):
        ra["loi"] = "thieu-javis"
        return ra
    ra["co_javis"] = True
    ra["keys"] = sorted(str(k) for k in javis.keys())
    ra["url_ok"] = bool(str(javis.get("url") or "").strip())
    # Không trả giá trị header/token.
    ra["co_headers"] = isinstance(javis.get("headers"), dict) and bool(javis.get("headers"))
    return ra


# ---------------------------------------------------------------------------
# Một lượt chạy
# ---------------------------------------------------------------------------
class GrokCLI:
    """Một lượt chạy `grok` headless. Cùng hợp đồng sự kiện với GeminiCLI / AntigravityCLI.

    query() sinh dict {"type": "tool_call"|"text"|"final"|"error"|"usage", ...}.
    """

    def __init__(self, cwd: Optional[str] = None, tag: str = "chat",
                 model: Optional[str] = None, instructions: Optional[str] = None):
        self.cli_path = find_grok_cli()
        self.cwd = cwd or os.getcwd()
        self.tag = tag
        self.model = model
        self.instructions = instructions
        self.session_id = None          # có → `--resume`; không thì CLI mở mạch mới
        self.mode = "suggest"
        self.extra_args: list[str] = []
        self.include_dirs: list[str] = []
        self.timeout = float(os.environ.get("JAVIS_GROK_TIMEOUT") or 900)

    def is_available(self) -> bool:
        return self.cli_path is not None

    def _co_quyen(self) -> list[str]:
        if str(self.mode or "").strip().lower() != "full":
            return []
        for c in _QUYEN_FULL:
            if co_co(c):
                return [c]
        return []

    def _build_args(self, prompt_argv: Optional[str], prompt_file: Optional[str] = None
                    ) -> list[str]:
        args = [self.cli_path]
        if co_co("--no-auto-update"):
            args += ["--no-auto-update"]
        if self.model and co_co("-m", "--model"):
            args += ["-m", str(self.model)]
        args += self._co_quyen()
        if co_co("--output-format"):
            # Tài liệu chính chủ: streaming-json (có dấu gạch). Một số bản cũ dùng stream-json.
            fmt = "streaming-json" if "streaming-json" in (_help_text() or "") else "stream-json"
            if fmt == "stream-json" and "stream-json" not in (_help_text() or ""):
                fmt = "streaming-json"
            args += ["--output-format", fmt]
        if self.session_id and co_co("--resume", "-r"):
            args += ["--resume", str(self.session_id)]
        args += list(self.extra_args)
        # Prompt cuối cùng (cờ sau -p bị một số CLI bỏ qua - giữ khuôn an toàn).
        if prompt_file and co_co("--prompt-file"):
            args += ["--prompt-file", prompt_file]
            if co_co("-p", "--single"):
                args += ["-p", ""]
        elif prompt_argv is not None:
            args += ["-p", prompt_argv]
        return args

    async def query(self, prompt: str) -> AsyncIterator[dict]:
        if not self.cli_path:
            yield {
                "type": "error",
                "content": (
                    f"Không tìm thấy Grok Build CLI (`grok`). Cài một lần:\n\n"
                    f"`{lenh_cai()}`\n\n"
                    f"Hoặc: `{LENH_CAI_NPM}`\n\n"
                    "Rồi bấm Đăng nhập ở thẻ Grok trên trang Models."
                ),
            }
            return
        full = (self.instructions.strip() + "\n\n" + prompt) if self.instructions else prompt
        # Prompt dài: Windows chặn argv ~32k; system prompt Javis dễ vượt. Đi --prompt-file.
        tep: Optional[str] = None
        prompt_argv: Optional[str] = full
        dung_file = False
        tran = 28000 if os.name == "nt" else 100000
        if len(full) > tran and co_co("--prompt-file"):
            dung_file = True
        elif len(full) > tran:
            # Không có --prompt-file: vẫn thử argv; nếu fail sẽ hiện lỗi CLI.
            dung_file = False
        try:
            if dung_file:
                fd, tep = tempfile.mkstemp(prefix="javis-grok-", suffix=".txt")
                os.close(fd)
                Path(tep).write_text(full, encoding="utf-8")
                prompt_argv = None
            args = self._build_args(prompt_argv, prompt_file=tep)
        except Exception as e:
            yield {"type": "error",
                   "content": f"Không chuẩn bị được lệnh Grok: {type(e).__name__}: {e}"}
            return

        loop = asyncio.get_running_loop()
        hang: asyncio.Queue = asyncio.Queue()
        HET = object()

        def doc_luong():
            proc = None
            try:
                proc = subprocess.Popen(
                    args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, cwd=self.cwd, text=True, encoding="utf-8",
                    errors="replace", bufsize=1, creationflags=_no_window(),
                    start_new_session=(os.name != "nt"),
                )
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
                        {"_exit": -1,
                         "_err": f"Grok Build CLI chạy quá {int(self.timeout)}s nên bị cắt. "
                                 f"Nâng JAVIS_GROK_TIMEOUT nếu việc thật sự dài."},
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
                if tep and not os.environ.get("JAVIS_GROK_GIU_PROMPT"):
                    try:
                        os.unlink(tep)
                    except Exception:
                        pass
                loop.call_soon_threadsafe(hang.put_nowait, HET)

        threading.Thread(target=doc_luong, name=f"javis-grok-{self.tag}", daemon=True).start()

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
            yield {"type": "error",
                   "content": "Grok Build CLI chạy xong nhưng không trả về nội dung nào."}

    def _doi_su_kien(self, ev: dict, cac_manh: list) -> list:
        """Một dòng NDJSON của `grok` -> 0..n sự kiện theo hợp đồng của Javis.

        Nhận rộng theo docs streaming-json (text / tool_call / end / error) và vài hình gần
        Gemini/agy. Dòng lạ giữ làm chữ - mất công đẹp còn hơn mất câu trả lời.
        """
        if "_raw" in ev:
            s = str(ev["_raw"])
            cac_manh.append(s)
            if len(s.strip()) > 8:
                return [{"type": "text", "content": s}]
            return []
        if "_exit" in ev:
            loi = str(ev.get("_err") or "").strip()
            if ev.get("_exit") == 0 and not loi:
                return []
            if _la_loi_chua_dang_nhap(loi):
                return [{"type": "error",
                         "content": "Grok Build CLI chưa đăng nhập. Bấm Đăng nhập ở thẻ Grok "
                                    "trên trang Models (hoặc chạy `grok login --device-auth`)."}]
            if not loi:
                loi = f"Grok Build CLI thoát với mã {ev.get('_exit')}."
            return [{"type": "error", "content": loi[:1500]}]

        t = str(ev.get("type") or ev.get("event") or "").lower()

        # Nhặt session id để lượt sau --resume (main.py lưu vào SQLite).
        if t in ("init", "system", "start", "session", "begin"):
            for k in ("sessionId", "session_id", "conversation_id", "id"):
                v = ev.get(k)
                if isinstance(v, str) and v.strip():
                    self.session_id = v.strip()
                    break
            return []

        if t in ("tool_call", "tool_use", "tool"):
            return [{"type": "tool_call",
                     "name": str(ev.get("toolName") or ev.get("tool_name")
                                 or ev.get("name") or ev.get("title") or ""),
                     "id": str(ev.get("toolCallId") or ev.get("tool_id")
                               or ev.get("id") or ""),
                     "input": ev.get("rawInput") or ev.get("parameters")
                              or ev.get("input") or {}}]
        if t in ("tool_call_update", "tool_result", "tool_output"):
            return [{"type": "tool_result",
                     "id": str(ev.get("toolCallId") or ev.get("tool_id")
                               or ev.get("id") or ""),
                     "status": str(ev.get("status") or ""),
                     "content": str(ev.get("rawOutput") or ev.get("output")
                                    or ev.get("content") or "")[:2000]}]
        if t == "error":
            tin = str(ev.get("message") or ev.get("error") or "Grok Build CLI lỗi.")
            if isinstance(ev.get("error"), dict):
                tin = str(ev["error"].get("message") or tin)
            if _la_loi_chua_dang_nhap(tin):
                return [{"type": "error",
                         "content": "Grok Build CLI chưa đăng nhập. Bấm Đăng nhập ở thẻ Grok."}]
            if str(ev.get("severity") or "error") == "warning":
                return []
            return [{"type": "error", "content": tin[:1500]}]

        ra = []
        if t in ("end", "result", "final", "done", "complete"):
            for k in ("sessionId", "session_id"):
                v = ev.get(k)
                if isinstance(v, str) and v.strip():
                    self.session_id = v.strip()
                    break
            st = ev.get("usage") or ev.get("stats") or {}
            if isinstance(st, dict) and st:
                ra.append({"type": "usage",
                           "input_tokens": int(st.get("input_tokens")
                                               or st.get("prompt_tokens")
                                               or st.get("inputTokens") or 0),
                           "output_tokens": int(st.get("output_tokens")
                                                or st.get("completion_tokens")
                                                or st.get("outputTokens") or 0),
                           "total_tokens": int(st.get("total_tokens")
                                               or st.get("totalTokens") or 0),
                           "cached": int(st.get("cached") or 0)})
            status = str(ev.get("status") or ev.get("stopReason") or "").lower()
            if status in ("error", "failed"):
                e = ev.get("error") or {}
                tin = str(e.get("message") if isinstance(e, dict) else e) or ""
                ra.append({"type": "error",
                           "content": tin[:1500] or "Grok Build CLI kết thúc với lỗi."})
                return ra
            # `end`/`result` đôi khi mang toàn văn; tránh nhân đôi nếu đã gom delta.
            if not cac_manh:
                for k in ("text", "response", "content", "output", "message"):
                    v = ev.get(k)
                    if isinstance(v, str) and v:
                        cac_manh.append(v)
                        break
            return ra

        if t in ("text", "message", "agent_response", "step_update"):
            for k in ("text", "content", "text_delta", "delta", "message", "response"):
                v = ev.get(k)
                if isinstance(v, str) and v:
                    cac_manh.append(v)
                    return [{"type": "text", "content": v}]
                if isinstance(v, dict):
                    vv = v.get("text") or v.get("content")
                    if isinstance(vv, str) and vv:
                        cac_manh.append(vv)
                        return [{"type": "text", "content": vv}]
            return []

        # Lưới cuối: mọi thứ trông như chữ trợ lý.
        if str(ev.get("role") or "assistant").lower() in ("assistant", "model", "agent", ""):
            for k in ("text", "content", "delta", "message", "response", "output"):
                v = ev.get(k)
                if isinstance(v, str) and v:
                    cac_manh.append(v)
                    break
        return ra


def _la_loi_chua_dang_nhap(loi: str) -> bool:
    l = (loi or "").lower()
    return any(k in l for k in (
        "not signed in", "not logged in", "sign in", "login required",
        "unauthenticated", "no active session", "authentication required",
        "please login", "please log in", "run grok login", "auth.json",
    ))


def kiem_tra_nhanh(timeout: float = 60.0) -> dict:
    """Chạy thử một lượt cực ngắn cho nút Kiểm tra lại ở trang Models."""
    cli = find_grok_cli()
    if not cli:
        return {"ok": False, "error": f"Chưa cài Grok Build CLI. {lenh_cai()}"}
    st = auth_status()
    if not st.get("connected"):
        return {"ok": False, "error": st.get("error") or "Chưa đăng nhập."}
    args = [cli]
    if co_co("--no-auto-update"):
        args += ["--no-auto-update"]
    if co_co("--output-format"):
        args += ["--output-format", "json"]
    # Không --yolo ở đây: chỉ cần biết chat được, không cần quyền ghi.
    args += ["-p", "Trả lời đúng một chữ: ok"]
    try:
        r = subprocess.run(
            args, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=timeout, creationflags=_no_window(),
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Grok Build CLI không trả lời kịp."}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}
    out = (r.stdout or "").strip()
    if r.returncode != 0:
        loi = (r.stderr or out or "").strip()
        if _la_loi_chua_dang_nhap(loi):
            return {"ok": False, "error": "Chưa đăng nhập. Bấm Đăng nhập ở thẻ Grok."}
        return {"ok": False, "error": loi[:400] or f"Thoát mã {r.returncode}"}
    if not out:
        return {"ok": False, "error": "CLI chạy xong nhưng không in ra gì."}
    try:
        d = json.loads(out)
    except json.JSONDecodeError:
        # Có thể là nhiều dòng streaming-json dù ta xin json - lấy chữ thô.
        return {"ok": True, "reply": out[:200]}
    if isinstance(d, dict) and d.get("error"):
        e = d["error"]
        return {"ok": False,
                "error": str(e.get("message") if isinstance(e, dict) else e)[:400]}
    tra = ""
    if isinstance(d, dict):
        for k in ("text", "response", "result", "content", "output"):
            if isinstance(d.get(k), str):
                tra = d[k]
                break
        sid = d.get("sessionId") or d.get("session_id")
        if isinstance(sid, str) and sid.strip():
            # Không lưu vào instance - chỉ xác nhận CLI sống.
            pass
    return {"ok": True, "reply": (tra or out)[:200]}


def phien_moi() -> str:
    """UUID dự phòng khi cần id mạch phía Javis (CLI thường tự phát sessionId)."""
    return str(uuid.uuid4())
