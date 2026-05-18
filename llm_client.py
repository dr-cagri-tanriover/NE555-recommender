"""LLM provider abstraction.

Routes calls to either Gemini (google-genai SDK) or Ollama based on
``settings.llm_provider``.  Both providers expose a single function::

    generate(system, user_msg, max_tokens) -> str
"""
from __future__ import annotations

import sys
import time

from config import settings

_total_llm_seconds: float = 0.0


def get_total_llm_time() -> float:
    """Return cumulative seconds spent waiting for LLM responses (excludes rate-limit sleeps)."""
    return _total_llm_seconds


def generate(system: str, user_msg: str, max_tokens: int = 2048) -> str:
    """Return LLM text completion, routing to Gemini or Ollama per settings."""
    if settings.llm_provider == "ollama":
        return _generate_ollama(system, user_msg, max_tokens)
    # Default: gemini
    return _generate_gemini(system, user_msg, max_tokens)


# ---------------------------------------------------------------------------
# Gemini backend
# ---------------------------------------------------------------------------

def _generate_gemini(system: str, user_msg: str, max_tokens: int) -> str:
    global _total_llm_seconds
    from google import genai
    from google.genai import errors as genai_errors
    from google.genai import types

    client = genai.Client(api_key=settings.gemini_api_key)

    def _invoke() -> str:
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=user_msg,
            config=types.GenerateContentConfig(
                system_instruction=system,
                temperature=0.0,
                max_output_tokens=max_tokens,
            ),
        )
        return response.text

    try:
        t0 = time.perf_counter()
        result = _invoke()
        _total_llm_seconds += time.perf_counter() - t0
        return result
    except genai_errors.ClientError as exc:
        if exc.code != 429:
            raise
        print("[llm_client] Gemini rate limited — sleeping 60s", file=sys.stderr)
        time.sleep(60)
        t0 = time.perf_counter()
        result = _invoke()  # raises naturally on second failure
        _total_llm_seconds += time.perf_counter() - t0
        return result


# ---------------------------------------------------------------------------
# Ollama backend
# ---------------------------------------------------------------------------

def _generate_ollama(system: str, user_msg: str, max_tokens: int) -> str:
    global _total_llm_seconds
    try:
        import ollama  # type: ignore[import]
    except ImportError as exc:
        raise RuntimeError(
            "The 'ollama' package is not installed. Run: uv add ollama"
        ) from exc

    client = ollama.Client(host=settings.ollama_host)
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_msg},
    ]
    try:
        t0 = time.perf_counter()
        response = client.chat(
            model=settings.ollama_model,
            messages=messages,
            think=False,  # disable extended-thinking / <think> mode (e.g. qwen3)
            options={"num_predict": max_tokens},
        )
        _total_llm_seconds += time.perf_counter() - t0
        content = response.message.content
        if not content or not content.strip():
            raise RuntimeError(
                f"Ollama model '{settings.ollama_model}' returned an empty response. "
                "The model may be too small to follow structured instructions. "
                "Try a larger model (e.g. qwen3:8b) by setting OLLAMA_MODEL in .env."
            )
        return content
    except Exception as exc:
        print(f"[llm_client] Ollama error: {exc}", file=sys.stderr)
        raise
