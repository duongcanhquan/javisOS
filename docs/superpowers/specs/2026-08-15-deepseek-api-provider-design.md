# DeepSeek API Provider — Design

**Date:** 2026-08-15 · **Status:** Approved (approach 1 + full parity) · **Implementing**

## Goal

Add first-class **DeepSeek (API)** provider alongside existing OpenRouter path. Full parity with Groq: chat, MCP tools, skills, main + aux engines, usage tracking, Models UI.

## Identity

| Field | Value |
|-------|-------|
| Provider id | `deepseek` |
| Label | DeepSeek (API) |
| Key | `model.deepseek_api_key` (encrypted) |
| URL | `https://api.deepseek.com/chat/completions` |
| Models list | `https://api.deepseek.com/models` |
| Default models | `deepseek-v4-flash`, `deepseek-v4-pro` |

OpenRouter unchanged (`deepseek/...` models still work there).

## Reasoning

When user reasoning ≠ `off`, send DeepSeek V4 fields: `thinking: {type: enabled}` + `reasoning_effort`.

## Out of scope

- STT (stays Groq Whisper)
- Generic OpenAI-compatible provider UI
- Changing OpenRouter DeepSeek models
