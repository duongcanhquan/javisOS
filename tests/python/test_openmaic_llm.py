"""OpenMAIC LLM module — merge env + default model string."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))

from openmaic_llm import (  # noqa: E402
    PROVIDERS,
    default_model_string,
    _merge_env_for_provider,
)


def test_providers():
    assert set(PROVIDERS) >= {"google", "openai", "deepseek"}


def test_default_model_string():
    assert default_model_string("deepseek", "deepseek-chat") == "deepseek:deepseek-chat"
    assert default_model_string("google", "gemini-3.6-flash") == "google:gemini-3.6-flash"


def test_merge_keeps_tts_swaps_llm():
    old = {
        "GOOGLE_API_KEY": "old-g",
        "DEFAULT_MODEL": "google:gemini-2.5-flash",
        "TTS_OPENAI_API_KEY": "tts-secret",
        "TTS_OPENAI_BASE_URL": "http://host.docker.internal:7777/v1",
        "TTS_OPENAI_ENABLED": "true",
    }
    env = _merge_env_for_provider(old, "deepseek", "deepseek-chat", "ds-key")
    assert env["DEEPSEEK_API_KEY"] == "ds-key"
    assert env["DEFAULT_MODEL"] == "deepseek:deepseek-chat"
    assert "GOOGLE_API_KEY" not in env
    assert env["TTS_OPENAI_API_KEY"] == "tts-secret"


if __name__ == "__main__":
    test_providers()
    test_default_model_string()
    test_merge_keeps_tts_swaps_llm()
    print("ok")
