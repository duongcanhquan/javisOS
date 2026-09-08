"""OpenMAIC LLM config — user chọn Gemini / OpenAI / DeepSeek trong Javis.

Key lấy từ Models (đã lưu). Áp dụng: ghi state + recreate container OpenMAIC
qua Docker socket (nếu có). Deploy sync cũng đọc file state này.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import quote


def _docker_api(method: str, path: str, json_body: Any = None, timeout: float = 60.0):
    """Gọi Docker Engine API qua unix socket (không cần binary docker)."""
    import httpx

    sock = "/var/run/docker.sock"
    if not Path(sock).exists():
        raise RuntimeError("no docker.sock")
    transport = httpx.HTTPTransport(uds=sock)
    with httpx.Client(transport=transport, base_url="http://localhost", timeout=timeout) as client:
        r = client.request(method, path, json=json_body)
        return r


def docker_available() -> bool:
    try:
        r = _docker_api("GET", "/_ping", timeout=5.0)
        return r.status_code == 200 and (r.text or "").strip() == "OK"
    except Exception:
        return False


def _docker_inspect(name: str = "openmaic") -> dict[str, Any]:
    try:
        r = _docker_api("GET", f"/containers/{quote(name)}/json", timeout=20.0)
        if r.status_code != 200:
            return {}
        data = r.json()
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _docker_inspect_env(name: str = "openmaic") -> dict[str, str]:
    data = _docker_inspect(name)
    arr = ((data.get("Config") or {}) if isinstance(data.get("Config"), dict) else {}).get("Env") or []
    env: dict[str, str] = {}
    for item in arr:
        if not isinstance(item, str) or "=" not in item:
            continue
        k, _, v = item.partition("=")
        env[k] = v
    return env


def _docker_image(name: str = "openmaic") -> str:
    data = _docker_inspect(name)
    img = ((data.get("Config") or {}) if isinstance(data.get("Config"), dict) else {}).get("Image")
    if isinstance(img, str) and img.strip():
        return img.strip()
    return "devprincekumar/openmaic:latest"


def _host_openmaic_dir() -> Path | None:
    env = (os.getenv("OPENMAIC_HOST_DIR") or "").strip()
    candidates = []
    if env:
        candidates.append(Path(env))
    # Bind-mount vào container (tuỳ chọn)
    candidates.append(Path("/data/openmaic-host"))
    for c in candidates:
        if c.is_dir():
            return c
    return None


# provider id → (env key name trong OpenMAIC, prefix DEFAULT_MODEL, field Models)
PROVIDERS: dict[str, dict[str, Any]] = {
    "google": {
        "label": "Google Gemini",
        "env_key": "GOOGLE_API_KEY",
        "model_prefix": "google",
        "javis_key_field": "gemini_api_key",
        "default_model": "gemini-3.6-flash",
        "models": ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.1-pro-preview"],
    },
    "openai": {
        "label": "OpenAI (ChatGPT API)",
        "env_key": "OPENAI_API_KEY",
        "model_prefix": "openai",
        "javis_key_field": "openai_api_key",
        "default_model": "gpt-4o-mini",
        "models": ["gpt-4o-mini", "gpt-4o", "gpt-5.4-mini", "o4-mini"],
    },
    "deepseek": {
        "label": "DeepSeek",
        "env_key": "DEEPSEEK_API_KEY",
        "model_prefix": "deepseek",
        "javis_key_field": "deepseek_api_key",
        "default_model": "deepseek-chat",
        "models": ["deepseek-chat", "deepseek-reasoner", "deepseek-v4-flash", "deepseek-v4-pro"],
    },
}

STATE_NAME = "openmaic_llm.json"


def _state_dir() -> Path:
    return Path(os.getenv("JAVIS_STATE_DIR") or "/data/state")


def state_path() -> Path:
    return _state_dir() / STATE_NAME


def load_config() -> dict[str, Any]:
    p = state_path()
    if not p.is_file():
        return {
            "provider": "google",
            "model": "gemini-3.6-flash",
            "updated": "",
        }
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"provider": "google", "model": "gemini-3.6-flash", "updated": ""}
    if not isinstance(data, dict):
        return {"provider": "google", "model": "gemini-3.6-flash", "updated": ""}
    prov = str(data.get("provider") or "google").strip().lower()
    if prov == "gemini":
        prov = "google"
    if prov not in PROVIDERS:
        prov = "google"
    model = str(data.get("model") or PROVIDERS[prov]["default_model"]).strip()
    # Cho phép DEFAULT_MODEL dạng google:xxx — tách lấy phần model
    if ":" in model:
        pref, _, rest = model.partition(":")
        if pref in PROVIDERS and rest:
            prov = pref
            model = rest
    return {
        "provider": prov,
        "model": model or PROVIDERS[prov]["default_model"],
        "updated": str(data.get("updated") or ""),
        "last_apply": data.get("last_apply") or {},
    }


def save_config(provider: str, model: str, last_apply: dict | None = None) -> dict[str, Any]:
    from datetime import datetime, timezone

    prov = (provider or "").strip().lower()
    if prov == "gemini":
        prov = "google"
    if prov not in PROVIDERS:
        raise ValueError(f"Provider không hỗ trợ: {provider}")
    mdl = (model or "").strip()
    if ":" in mdl:
        _, _, mdl = mdl.partition(":")
    mdl = mdl or PROVIDERS[prov]["default_model"]
    out = {
        "provider": prov,
        "model": mdl,
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    if last_apply is not None:
        out["last_apply"] = last_apply
    elif isinstance(load_config().get("last_apply"), dict):
        out["last_apply"] = load_config()["last_apply"]
    _state_dir().mkdir(parents=True, exist_ok=True)
    state_path().write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out


def default_model_string(provider: str, model: str) -> str:
    meta = PROVIDERS[provider]
    return f"{meta['model_prefix']}:{model}"


def _decrypt_key(raw: str) -> str:
    k = (raw or "").strip()
    if not k:
        return ""
    if k.startswith(("enc:", "plain:")):
        try:
            import secrets_store

            k = (secrets_store.decrypt(k) or "").strip()
        except Exception:
            return ""
    if k.startswith(("enc:", "plain:")):
        return ""
    return k


def get_javis_api_key(provider: str) -> str:
    """Plain API key từ Models settings."""
    meta = PROVIDERS.get(provider) or PROVIDERS["google"]
    field = meta["javis_key_field"]
    try:
        import config as cfgmod

        m = (cfgmod.read_settings().get("model") or {})
        return _decrypt_key(str(m.get(field) or ""))
    except Exception:
        return ""


def key_status() -> dict[str, Any]:
    out = {}
    for pid, meta in PROVIDERS.items():
        k = get_javis_api_key(pid)
        out[pid] = {
            "label": meta["label"],
            "has_key": bool(k),
            "key_len": len(k),
            "models": list(meta["models"]),
            "default_model": meta["default_model"],
        }
    return out


def docker_available() -> bool:
    sock = Path("/var/run/docker.sock")
    if not sock.exists():
        return False
    try:
        r = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=8,
        )
        return r.returncode == 0
    except Exception:
        return False


def _docker_inspect_env(name: str = "openmaic") -> dict[str, str]:
    try:
        r = subprocess.run(
            ["docker", "inspect", name, "--format", "{{json .Config.Env}}"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if r.returncode != 0:
            return {}
        arr = json.loads(r.stdout.strip() or "[]")
        env: dict[str, str] = {}
        for item in arr or []:
            if not isinstance(item, str) or "=" not in item:
                continue
            k, _, v = item.partition("=")
            env[k] = v
        return env
    except Exception:
        return {}


def _docker_image(name: str = "openmaic") -> str:
    try:
        r = subprocess.run(
            ["docker", "inspect", name, "--format", "{{.Config.Image}}"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except Exception:
        pass
    return "devprincekumar/openmaic:latest"


def _host_openmaic_dir() -> Path | None:
    env = (os.getenv("OPENMAIC_HOST_DIR") or "").strip()
    candidates = []
    if env:
        candidates.append(Path(env))
    # Bind-mount vào container (tuỳ chọn)
    candidates.append(Path("/data/openmaic-host"))
    for c in candidates:
        if c.is_dir():
            return c
    return None


def _merge_env_for_provider(old: dict[str, str], provider: str, model: str, api_key: str) -> dict[str, str]:
    """Giữ TTS / ACCESS / PORT; đặt LLM theo provider đã chọn."""
    env = dict(old)
    # Xoá key LLM cũ để khỏi nhầm provider
    for k in (
        "GOOGLE_API_KEY",
        "OPENAI_API_KEY",
        "DEEPSEEK_API_KEY",
        "ANTHROPIC_API_KEY",
        "DEFAULT_MODEL",
        "DEFAULT_PROVIDER",
    ):
        # Không xoá TTS_OPENAI_* 
        if k.startswith("TTS_"):
            continue
        env.pop(k, None)

    meta = PROVIDERS[provider]
    env[meta["env_key"]] = api_key
    env["DEFAULT_PROVIDER"] = meta["model_prefix"]
    env["DEFAULT_MODEL"] = default_model_string(provider, model)
    # TTS giữ nguyên nếu đã có; không đụng TTS_OPENAI_API_KEY
    env.setdefault("TTS_BROWSER_NATIVE_ENABLED", "false")
    env.setdefault("NODE_ENV", "production")
    env.setdefault("PORT", "3000")
    return env


def _write_env_file(path: Path, env: dict[str, str]) -> None:
    lines = ["# Generated by Javis OpenMAIC LLM module — do not commit"]
    # Ưu tiên thứ tự đọc
    order = [
        "GOOGLE_API_KEY",
        "OPENAI_API_KEY",
        "DEEPSEEK_API_KEY",
        "DEFAULT_PROVIDER",
        "DEFAULT_MODEL",
        "TTS_BROWSER_NATIVE_ENABLED",
        "TTS_OPENAI_ENABLED",
        "TTS_OPENAI_API_KEY",
        "TTS_OPENAI_BASE_URL",
        "ACCESS_CODE",
        "NODE_ENV",
        "PORT",
    ]
    seen = set()
    for k in order:
        if k in env:
            lines.append(f"{k}={env[k]}")
            seen.add(k)
    for k in sorted(env.keys()):
        if k in seen:
            continue
        if re.match(r"^[A-Z0-9_]+$", k):
            lines.append(f"{k}={env[k]}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass


def _recreate_openmaic_container(env: dict[str, str], env_file: Path | None = None) -> tuple[bool, str]:
    """Recreate container openmaic qua Docker Engine API."""
    del env_file  # giữ chữ ký; apply luôn dùng Env list
    img = _docker_image("openmaic")
    port = (os.getenv("OPENMAIC_PORT") or "3000").strip() or "3000"

    # Xoá container cũ (ignore 404)
    try:
        _docker_api("DELETE", f"/containers/{quote('openmaic')}?force=true", timeout=60.0)
    except Exception as e:
        return False, f"xoá container cũ: {e}"

    env_list = [f"{k}={v}" for k, v in env.items() if v is not None]
    binds: list[str] = ["openmaic_data:/app/data"]
    host_dir = _host_openmaic_dir()
    if host_dir and (host_dir / "server-providers.yml").is_file():
        # Path trong container — Docker API cần path HOST. Chỉ mount nếu OPENMAIC_HOST_DIR là path host.
        host_sp = (os.getenv("OPENMAIC_HOST_DIR") or "").strip()
        if host_sp:
            binds.append(f"{host_sp.rstrip('/')}/server-providers.yml:/app/server-providers.yml:ro")

    body = {
        "Image": img,
        "Env": env_list,
        "ExposedPorts": {"3000/tcp": {}},
        "HostConfig": {
            "RestartPolicy": {"Name": "unless-stopped"},
            "PortBindings": {"3000/tcp": [{"HostPort": port}]},
            "Binds": binds,
            "ExtraHosts": ["host.docker.internal:host-gateway"],
        },
    }
    try:
        cr = _docker_api("POST", "/containers/create?name=openmaic", json_body=body, timeout=120.0)
    except Exception as e:
        return False, f"create: {e}"
    if cr.status_code not in (200, 201):
        return False, f"create HTTP {cr.status_code}: {(cr.text or '')[:400]}"
    try:
        cid = (cr.json() or {}).get("Id") or ""
    except Exception:
        cid = ""
    if not cid:
        return False, "create không trả Id"
    try:
        st = _docker_api("POST", f"/containers/{quote(cid)}/start", timeout=60.0)
    except Exception as e:
        return False, f"start: {e}"
    if st.status_code not in (204, 200):
        return False, f"start HTTP {st.status_code}: {(st.text or '')[:400]}"
    return True, cid[:12]


def apply_llm(provider: str, model: str) -> dict[str, Any]:
    """Lưu config + áp lên OpenMAIC (recreate nếu có docker.sock)."""
    prov = (provider or "").strip().lower()
    if prov == "gemini":
        prov = "google"
    if prov not in PROVIDERS:
        return {"ok": False, "error": f"Provider không hỗ trợ: {provider}"}
    mdl = (model or "").strip()
    if ":" in mdl:
        _, _, mdl = mdl.partition(":")
    mdl = mdl or PROVIDERS[prov]["default_model"]

    api_key = get_javis_api_key(prov)
    if not api_key:
        field = PROVIDERS[prov]["javis_key_field"]
        return {
            "ok": False,
            "error": (
                f"Chưa có API key cho {PROVIDERS[prov]['label']}. "
                f"Vào Models → dán key, rồi Áp dụng lại."
            ),
            "need_models_field": field,
        }

    cfg = save_config(prov, mdl)
    dm = default_model_string(prov, mdl)

    if not docker_available():
        last = {
            "ok": False,
            "mode": "state_only",
            "default_model": dm,
            "hint": (
                "Đã lưu lựa chọn. Container Javis chưa có Docker socket nên chưa recreate OpenMAIC. "
                "Chạy Actions «Deploy OpenMAIC to VPS» (sync_key_only=1) hoặc gắn "
                "/var/run/docker.sock vào service javis."
            ),
        }
        save_config(prov, mdl, last_apply=last)
        return {"ok": True, "applied": False, "config": cfg, **last}

    old = _docker_inspect_env("openmaic")
    if not old:
        # Container chưa có — vẫn ghi file nếu mount host
        old = {
            "TTS_BROWSER_NATIVE_ENABLED": "false",
            "TTS_OPENAI_ENABLED": "true",
            "NODE_ENV": "production",
            "PORT": "3000",
        }
    # Giữ TTS key từ state nếu cũ thiếu
    try:
        tts_key_path = _state_dir() / "openmaic_tts_proxy.key"
        if tts_key_path.is_file() and not old.get("TTS_OPENAI_API_KEY"):
            old["TTS_OPENAI_API_KEY"] = tts_key_path.read_text(encoding="utf-8").strip()
            old.setdefault("TTS_OPENAI_BASE_URL", "http://host.docker.internal:7777/v1")
            old["TTS_OPENAI_ENABLED"] = "true"
    except Exception:
        pass

    env = _merge_env_for_provider(old, prov, mdl, api_key)

    env_file: Path | None = None
    host_dir = _host_openmaic_dir()
    if host_dir:
        env_file = host_dir / ".env.local"
        _write_env_file(env_file, env)
        # defaultModel trong server-providers
        sp = host_dir / "server-providers.yml"
        try:
            text = sp.read_text(encoding="utf-8") if sp.is_file() else "tts:\n  browser-native-tts:\n    enabled: false\n"
            if re.search(r"(?m)^\s*defaultModel:", text):
                text = re.sub(
                    r"(?m)^(\s*defaultModel:).*$",
                    f'\\1 "{dm}"',
                    text,
                )
            else:
                text = text.rstrip() + f'\n\ndefaultModel: "{dm}"\n'
            sp.write_text(text, encoding="utf-8")
        except Exception:
            pass

    # Trong container Javis: luôn truyền -e (tránh --env-file cần path HOST).
    ok, detail = _recreate_openmaic_container(env, env_file=None)
    last = {
        "ok": ok,
        "mode": "docker_recreate",
        "default_model": dm,
        "detail": detail if ok else detail,
        "provider": prov,
        "model": mdl,
    }
    save_config(prov, mdl, last_apply=last)
    if not ok:
        return {"ok": False, "error": f"Recreate OpenMAIC thất bại: {detail}", "config": cfg}
    return {
        "ok": True,
        "applied": True,
        "config": load_config(),
        "default_model": dm,
        "container": detail,
        "message": f"OpenMAIC đang dùng {dm}. Key lấy từ Models ({PROVIDERS[prov]['label']}).",
    }


def status_payload() -> dict[str, Any]:
    cfg = load_config()
    return {
        "ok": True,
        "config": cfg,
        "default_model": default_model_string(cfg["provider"], cfg["model"]),
        "providers": key_status(),
        "docker": docker_available(),
        "host_dir_mounted": _host_openmaic_dir() is not None,
    }
