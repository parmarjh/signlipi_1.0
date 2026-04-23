"""Thin async client for a local Ollama server.

Ollama exposes an OpenAI-compatible chat API at
    POST {base}/api/chat
with body: { "model": "...", "messages": [...], "stream": false }

We use plain httpx so the project has no heavy SDK dependency and can be
swapped for another local backend (LM Studio, llama.cpp server) by
changing one function.
"""
from __future__ import annotations

from typing import Dict, List, Optional

import httpx

from app.config import get_settings


SIGN_TO_SENTENCE_SYSTEM = (
    "You are a helpful assistant that turns sequences of sign-language tokens "
    "or single letters into a grammatical, short natural-language sentence. "
    "Keep the original meaning. Return ONLY the sentence, no preface."
)

GRAMMAR_SYSTEM = (
    "You fix grammar and spelling in accessibility-assistive text. "
    "Preserve meaning and brevity. Return ONLY the corrected text."
)

CHAT_SYSTEM = (
    "You are SignLipi, an accessibility assistant that helps users who "
    "communicate via sign language, Braille, or BCI. Be concise, warm, and clear."
)


async def _chat(messages: List[Dict[str, str]], model: Optional[str] = None, temperature: float = 0.3) -> str:
    settings = get_settings()
    url = f"{settings.ollama_base_url.rstrip('/')}/api/chat"
    payload = {
        "model": model or settings.ollama_model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature},
    }
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(url, json=payload)
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPError as exc:
        raise RuntimeError(
            f"Ollama request failed: {exc}. "
            f"Is Ollama running at {settings.ollama_base_url}? "
            f"Try: `ollama run {settings.ollama_model}` once to pull the model."
        ) from exc
    # Ollama returns {"message": {"role": "assistant", "content": "..."}}
    msg = data.get("message", {})
    return (msg.get("content") or "").strip()


async def sign_to_sentence(tokens: List[str], mode: str = "ASL") -> str:
    if not tokens:
        return ""
    user = f"Mode: {mode}. Tokens: {tokens}. Compose a short natural sentence."
    return await _chat(
        [
            {"role": "system", "content": SIGN_TO_SENTENCE_SYSTEM},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
    )


async def correct_text(text: str) -> str:
    if not text.strip():
        return ""
    return await _chat(
        [
            {"role": "system", "content": GRAMMAR_SYSTEM},
            {"role": "user", "content": text},
        ],
        temperature=0.1,
    )


async def chat(messages: List[Dict[str, str]]) -> str:
    # Prepend system prompt if absent
    if not messages or messages[0].get("role") != "system":
        messages = [{"role": "system", "content": CHAT_SYSTEM}, *messages]
    return await _chat(messages, temperature=0.4)
