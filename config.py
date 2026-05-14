from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    llm_provider: str = os.getenv("LLM_PROVIDER", "gemini")   # "gemini" or "ollama"
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen3:8b")
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    serpapi_api_key: str | None = os.getenv("SERPAPI_API_KEY")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    max_search_results: int = int(os.getenv("MAX_SEARCH_RESULTS", "5"))
    max_page_chars: int = int(os.getenv("MAX_PAGE_CHARS", "12000"))
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "20"))
    output_pdf_path: str = os.getenv("OUTPUT_PDF_PATH", "ne555_report.pdf")

    @property
    def gemini_api_key(self) -> str:
        key = os.getenv("GEMINI_API_KEY")
        if key is None:
            raise KeyError("GEMINI_API_KEY")
        return key


settings = Settings()
