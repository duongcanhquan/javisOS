"""Kho khóa API cho skill / video / ảnh / tìm web / giọng.

Models (OpenRouter, Gemini...) nằm trang Models. Token Telegram / Zalo nằm Kênh.
Kết nối MCP (Pancake, Google...) nằm trang Kết nối. Khối này là chỗ dán khóa
DỊCH VỤ NGOÀI để skill/CLI gọi API: Atlas, Kling, Tavily, Firecrawl, ElevenLabs...
và khóa tự thêm. Giá trị lưu settings.json (mã hoá), rồi bơm vào os.environ.

Ghi chú: KHÔNG dùng ký tự em dash.
"""
from __future__ import annotations

import os
import re

# id catalog -> biến môi trường + nhãn. Thêm mục mới = thêm một dict. UI tự vẽ.
CATALOG = (
    {
        "id": "atlascloud",
        "env": "ATLASCLOUD_API_KEY",
        "group": "video",
        "kind": "secret",
        "label": "Atlas Cloud",
        "label_en": "Atlas Cloud",
        "dung_de": "Collage giấy (paperdesign): poster cắt giấy, hoạt họa Omni, giọng xAI.",
        "dung_de_en": "Paper collage (paperdesign): paper posters, Omni motion, xAI voices.",
        "where": "https://www.atlascloud.ai/console/api-keys",
    },
    {
        "id": "xai",
        "env": "XAI_API_KEY",
        "group": "video",
        "kind": "secret",
        "label": "xAI (Grok / giọng)",
        "label_en": "xAI (Grok / voice)",
        "dung_de": "Grok CLI và giọng xAI khi làm video collage. Không thay khóa model trang Models.",
        "dung_de_en": "Grok CLI and xAI voices for collage video. Does not replace Models page keys.",
        "where": "https://console.x.ai",
    },
    {
        "id": "pixelle_base",
        "env": "PIXELLE_API_BASE",
        "group": "video",
        "kind": "url",
        "label": "Pixelle-Video",
        "label_en": "Pixelle-Video",
        "dung_de": "Địa chỉ máy Pixelle (tab Có lời đọc). Ví dụ http://127.0.0.1:8000",
        "dung_de_en": "Pixelle host URL (Spoken video tab). Example: http://127.0.0.1:8000",
        "where": "",
    },
    {
        "id": "video_kling",
        "env": "VIDEO_KLING_API_KEY",
        "group": "video",
        "kind": "secret",
        "label": "Kling",
        "label_en": "Kling",
        "dung_de": "Bài giảng / OpenMAIC: tạo video ngắn. Chỉ cần một khóa trong nhóm video này.",
        "dung_de_en": "Lessons / OpenMAIC: short video. Any one key in this video group is enough.",
        "where": "https://app.klingai.com",
    },
    {
        "id": "video_seedance",
        "env": "VIDEO_SEEDANCE_API_KEY",
        "group": "video",
        "kind": "secret",
        "label": "Seedance",
        "label_en": "Seedance",
        "dung_de": "Bài giảng / OpenMAIC: tạo video ngắn (ByteDance Seedance).",
        "dung_de_en": "Lessons / OpenMAIC: short video (ByteDance Seedance).",
        "where": "https://www.volcengine.com/experience/ark",
    },
    {
        "id": "video_veo",
        "env": "VIDEO_VEO_API_KEY",
        "group": "video",
        "kind": "secret",
        "label": "Google Veo",
        "label_en": "Google Veo",
        "dung_de": "Bài giảng / OpenMAIC: tạo video ngắn bằng Veo.",
        "dung_de_en": "Lessons / OpenMAIC: short video with Veo.",
        "where": "https://aistudio.google.com/apikey",
    },
    {
        "id": "video_sora",
        "env": "VIDEO_SORA_API_KEY",
        "group": "video",
        "kind": "secret",
        "label": "OpenAI Sora",
        "label_en": "OpenAI Sora",
        "dung_de": "Bài giảng / OpenMAIC: tạo video ngắn bằng Sora.",
        "dung_de_en": "Lessons / OpenMAIC: short video with Sora.",
        "where": "https://platform.openai.com/api-keys",
    },
    {
        "id": "image_seedream",
        "env": "IMAGE_SEEDREAM_API_KEY",
        "group": "image",
        "kind": "secret",
        "label": "Seedream",
        "label_en": "Seedream",
        "dung_de": "Bài giảng / OpenMAIC: tạo ảnh slide. Chỉ cần một khóa trong nhóm ảnh này.",
        "dung_de_en": "Lessons / OpenMAIC: slide images. Any one key in this image group is enough.",
        "where": "https://www.volcengine.com/experience/ark",
    },
    {
        "id": "image_qwen",
        "env": "IMAGE_QWEN_IMAGE_API_KEY",
        "group": "image",
        "kind": "secret",
        "label": "Qwen Image",
        "label_en": "Qwen Image",
        "dung_de": "Bài giảng / OpenMAIC: tạo ảnh slide bằng Qwen.",
        "dung_de_en": "Lessons / OpenMAIC: slide images with Qwen.",
        "where": "https://dashscope.console.aliyun.com",
    },
    {
        "id": "image_nano_banana",
        "env": "IMAGE_NANO_BANANA_API_KEY",
        "group": "image",
        "kind": "secret",
        "label": "Nano Banana",
        "label_en": "Nano Banana",
        "dung_de": "Bài giảng / OpenMAIC: tạo ảnh slide (Nano Banana).",
        "dung_de_en": "Lessons / OpenMAIC: slide images (Nano Banana).",
        "where": "https://www.atlascloud.ai/console/api-keys",
    },
    {
        "id": "tavily",
        "env": "TAVILY_API_KEY",
        "group": "search",
        "kind": "secret",
        "label": "Tavily",
        "label_en": "Tavily",
        "dung_de": "Tìm web thật cho nghiên cứu / bài giảng / OpenMAIC.",
        "dung_de_en": "Live web search for research, lessons and OpenMAIC.",
        "where": "https://www.tavily.com",
    },
    {
        "id": "exa",
        "env": "EXA_API_KEY",
        "group": "search",
        "kind": "secret",
        "label": "Exa",
        "label_en": "Exa",
        "dung_de": "Tìm web thay Tavily khi bạn có khóa Exa.",
        "dung_de_en": "Web search instead of Tavily when you have an Exa key.",
        "where": "https://exa.ai",
    },
    {
        "id": "firecrawl",
        "env": "FIRECRAWL_KEY",
        "also_env": ("FIRECRAWL_API_KEY",),
        "group": "search",
        "kind": "secret",
        "label": "Firecrawl",
        "label_en": "Firecrawl",
        "dung_de": "Đọc và trích trang web cho nghiên cứu sâu (skill deep-research).",
        "dung_de_en": "Read and extract web pages for deep research.",
        "where": "https://www.firecrawl.dev",
    },
    {
        "id": "tts_azure",
        "env": "TTS_AZURE_API_KEY",
        "group": "voice",
        "kind": "secret",
        "label": "Azure TTS",
        "label_en": "Azure TTS",
        "dung_de": "Bài giảng / OpenMAIC: đọc lời (một khóa TTS là đủ).",
        "dung_de_en": "Lessons / OpenMAIC: narration (any one TTS key is enough).",
        "where": "https://portal.azure.com",
    },
    {
        "id": "tts_glm",
        "env": "TTS_GLM_API_KEY",
        "group": "voice",
        "kind": "secret",
        "label": "GLM TTS",
        "label_en": "GLM TTS",
        "dung_de": "Bài giảng / OpenMAIC: đọc lời bằng GLM.",
        "dung_de_en": "Lessons / OpenMAIC: narration with GLM.",
        "where": "https://open.bigmodel.cn",
    },
    {
        "id": "tts_qwen",
        "env": "TTS_QWEN_API_KEY",
        "group": "voice",
        "kind": "secret",
        "label": "Qwen TTS",
        "label_en": "Qwen TTS",
        "dung_de": "Bài giảng / OpenMAIC: đọc lời bằng Qwen.",
        "dung_de_en": "Lessons / OpenMAIC: narration with Qwen.",
        "where": "https://dashscope.console.aliyun.com",
    },
    {
        "id": "tts_voxcpm",
        "env": "TTS_VOXCPM_BASE_URL",
        "group": "voice",
        "kind": "url",
        "label": "VoxCPM (địa chỉ)",
        "label_en": "VoxCPM (URL)",
        "dung_de": "Máy clone giọng VoxCPM tự chạy. Ví dụ http://127.0.0.1:8000/v1",
        "dung_de_en": "Self-hosted VoxCPM voice clone. Example: http://127.0.0.1:8000/v1",
        "where": "",
    },
    {
        "id": "google_maps",
        "env": "REMOTION_GOOGLE_MAPS_API_KEY",
        "also_env": ("GOOGLE_MAPS_API_KEY",),
        "group": "maps",
        "kind": "secret",
        "label": "Google Maps",
        "label_en": "Google Maps",
        "dung_de": "Bản đồ trong video Remotion (skill remotion-maps).",
        "dung_de_en": "Maps in Remotion video (remotion-maps skill).",
        "where": "https://console.cloud.google.com/google/maps-apis",
    },
)

GROUPS = (
    {"id": "video", "label": "Video", "label_en": "Video"},
    {"id": "image", "label": "Ảnh", "label_en": "Images"},
    {"id": "search", "label": "Tìm trên web", "label_en": "Web search"},
    {"id": "voice", "label": "Giọng đọc", "label_en": "Voice"},
    {"id": "maps", "label": "Bản đồ", "label_en": "Maps"},
    {"id": "custom", "label": "Khóa tự thêm", "label_en": "Custom keys"},
)

_BY_ID = {x["id"]: x for x in CATALOG}


def _moi_truong_catalog() -> set[str]:
    s: set[str] = set()
    for x in CATALOG:
        s.add(x["env"])
        for e in x.get("also_env") or ():
            if e:
                s.add(str(e))
    return s


_CATALOG_ENV = _moi_truong_catalog()

# Đã có chỗ dán riêng (Models / Cài đặt / Kênh). Không thêm ô trùng, không bơm đè.
_DA_CO_O_KHAC = frozenset({
    "ELEVENLABS_API_KEY", "TTS_ELEVENLABS_API_KEY",
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY",
    "GROQ_API_KEY", "DEEPSEEK_API_KEY", "OPENROUTER_API_KEY",
    "COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN",
})

_ENV_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,63}$")
_CAM = frozenset({
    "PATH", "HOME", "USER", "USERNAME", "LOGNAME", "SHELL", "PWD", "OLDPWD",
    "LD_PRELOAD", "LD_LIBRARY_PATH", "DYLD_INSERT_LIBRARIES", "DYLD_LIBRARY_PATH",
    "PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "PYTHONEXECUTABLE",
    "COMSPEC", "PATHEXT", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "TMPDIR",
    "JAVIS_ADMIN_PASSWORD", "JAVIS_ADMIN_USER", "JAVIS_HOST", "JAVIS_PORT",
    "JAVIS_REQUIRE_LOGIN", "JAVIS_SECURE_COOKIE", "JAVIS_ALLOWED_HOSTS",
})


class ToolApiError(ValueError):
    pass


def env_hop_le(ten: str) -> str:
    """Chuẩn hoá tên biến. Rỗng = không hợp lệ."""
    t = str(ten or "").strip().upper()
    if not _ENV_RE.match(t):
        return ""
    if t in _CAM or t.startswith("JAVIS_"):
        return ""
    return t


def catalog_item(cid: str):
    return _BY_ID.get(str(cid or "").strip())


def _keys(cfg: dict) -> dict:
    block = cfg.get("tool_apis")
    if not isinstance(block, dict):
        block = {}
        cfg["tool_apis"] = block
    keys = block.get("keys")
    if not isinstance(keys, dict):
        keys = {}
        block["keys"] = keys
    return keys


def _gia_tri(v) -> str:
    s = str(v or "").strip()
    if not s or s.startswith("••••"):
        return ""
    return s


def _suffix(v: str) -> str:
    s = _gia_tri(v)
    return s[-4:] if len(s) >= 4 else ""


def env_cho(kid: str) -> str:
    it = catalog_item(kid)
    if it:
        return it["env"]
    return env_hop_le(kid)


def _alias_env(it: dict) -> tuple[str, ...]:
    extra = it.get("also_env") or ()
    return tuple(str(e) for e in extra if e)


def mutate(cfg: dict, op: str, id: str = "", env: str = "", key: str = "") -> dict:
    """Sửa cfg tại chỗ. Trả cfg. Lỗi -> ToolApiError (chữ tiếng Việt, để UI hiện)."""
    op = str(op or "").strip().lower()
    keys = _keys(cfg)
    if op == "set":
        it = catalog_item(id)
        if not it:
            raise ToolApiError("Không có ô khóa này trong danh sách sẵn.")
        val = _gia_tri(key)
        if not val:
            raise ToolApiError("Dán khóa mới, không gửi lại ô trống hay bản che.")
        keys[it["id"]] = val
        return cfg
    if op == "clear":
        it = catalog_item(id)
        if not it:
            raise ToolApiError("Không có ô khóa này trong danh sách sẵn.")
        keys.pop(it["id"], None)
        return cfg
    if op == "set_custom":
        ten = env_hop_le(env)
        if not ten:
            raise ToolApiError("Tên biến phải dạng FOO_API_KEY, không dùng PATH/HOME/JAVIS_.")
        if ten in _CATALOG_ENV:
            raise ToolApiError("Biến này đã có ô sẵn. Điền ở thẻ phía trên, đừng thêm trùng.")
        if ten in _DA_CO_O_KHAC:
            raise ToolApiError("Biến này đã có chỗ dán (Models / Cài đặt / Kênh). Không thêm trùng.")
        val = _gia_tri(key)
        if not val:
            raise ToolApiError("Dán khóa mới, không gửi lại ô trống hay bản che.")
        keys[ten] = val
        return cfg
    if op == "clear_custom":
        ten = env_hop_le(env)
        if not ten:
            raise ToolApiError("Tên biến không hợp lệ.")
        if catalog_item(ten) or ten in {x["id"] for x in CATALOG}:
            raise ToolApiError("Không xoá ô sẵn bằng đường khóa tự thêm.")
        keys.pop(ten, None)
        for k in list(keys):
            if str(k).upper() == ten:
                keys.pop(k, None)
        return cfg
    raise ToolApiError("Lệnh không hợp lệ.")


def _env_dang_co(it: dict) -> bool:
    if (os.environ.get(it["env"]) or "").strip():
        return True
    for extra in _alias_env(it):
        if (os.environ.get(extra) or "").strip():
            return True
    return False


def view(cfg: dict) -> dict:
    """Dữ liệu cho dashboard. KHÔNG trả khóa đầy đủ."""
    keys = _keys(cfg)
    items = []
    used_env = set(_CATALOG_ENV)
    for it in CATALOG:
        val = _gia_tri(keys.get(it["id"]))
        env = it["env"]
        items.append({
            "id": it["id"],
            "env": env,
            "group": it["group"],
            "kind": it["kind"],
            "label": it["label"],
            "label_en": it["label_en"],
            "dung_de": it["dung_de"],
            "dung_de_en": it["dung_de_en"],
            "where": it["where"],
            "set": bool(val),
            "from_env": _env_dang_co(it),
            "suffix": _suffix(val),
        })
    custom = []
    for kid, raw in list(keys.items()):
        if catalog_item(kid):
            continue
        env = env_hop_le(kid)
        if not env or env in used_env:
            continue
        val = _gia_tri(raw)
        env_now = bool((os.environ.get(env) or "").strip())
        custom.append({
            "env": env,
            "set": bool(val),
            "from_env": env_now,
            "suffix": _suffix(val),
        })
    custom.sort(key=lambda x: x["env"])
    return {"groups": [dict(g) for g in GROUPS], "items": items, "custom": custom}


def _bom_mot(dat: set, env: str, val: str, cho_phep: set) -> None:
    """Đặt env. Không đụng biến đã có sẵn trừ khi chính kho này đã đặt trước đó."""
    if not env or env in _DA_CO_O_KHAC:
        return
    cu = (os.environ.get(env) or "").strip()
    if cu and env not in cho_phep:
        return
    os.environ[env] = val
    dat.add(env)


def inject(cfg: dict, duoc_ghi_de: set | None = None) -> set:
    """Bơm khóa đã lưu vào os.environ. Không ghi đè khóa .env / Docker / Cài đặt đã có.

    Trả tập tên biến vừa đặt (để apply_tool_env gỡ khi xoá). `duoc_ghi_de` = biến kho
    này đã owned, được phép cập nhật.
    """
    dat = set()
    cho_phep = set(duoc_ghi_de or ())
    keys = _keys(cfg)
    for kid, raw in list(keys.items()):
        val = _gia_tri(raw)
        if not val:
            continue
        it = catalog_item(kid)
        if it:
            env = it["env"]
        else:
            env = env_hop_le(kid)
            if env != str(kid).strip().upper():
                continue
        if not env:
            continue
        _bom_mot(dat, env, val, cho_phep)
        if it:
            for extra in _alias_env(it):
                _bom_mot(dat, extra, val, cho_phep)
    return dat
