# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## NE555 Circuit Recommender

Python CLI app that accepts a natural-language description of desired NE555 circuit features, searches the web for real matching circuits, and outputs a formatted PDF report with specs, BOM tables, and clickable source hyperlinks.

## Environment

- **Python:** 3.12 at `C:\Program Files\Python312\python.exe`
- **Package manager:** `uv` — never use `pip` directly

```powershell
# Bootstrap (first time only)
uv venv .venv --python "C:\Program Files\Python312\python.exe"
uv sync

# Run the app
uv run python main.py "astable oscillator 1kHz audio" --count 3 --verbose

# Add a dependency
uv add <package>
```

There is no test suite. Verify changes by running the app end-to-end.

## LLM Provider

Set `LLM_PROVIDER` in `.env` to switch backends. All LLM calls are routed through `llm_client.generate(system, user_msg, max_tokens) -> str` — callers never import Gemini or Ollama SDKs directly.

### Gemini (default)

```
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIza...
GEMINI_MODEL=gemini-3.1-flash-lite
```

Get a free key at Google AI Studio (aistudio.google.com/apikey).

**Free-tier quota:** If you hit rate limits, switch `GEMINI_MODEL`:
- `gemini-3.1-flash-lite` — **confirmed working without quota issues** (recommended default)
- `gemini-1.5-flash` or `gemini-2.0-flash-lite` — separate quota pools
- Do not use `gemini-1.5-flash-8b` — not available on the v1beta API endpoint

To list models available to your key:
```powershell
uv run python -c "from config import settings; from google import genai; client = genai.Client(api_key=settings.gemini_api_key); [print(m.name) for m in client.models.list()]"
```

### Ollama (local, no API key required)

```
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen3:8b
OLLAMA_HOST=http://localhost:11434
```

```powershell
ollama pull qwen3:8b   # download model
ollama serve           # must be running before invoking the app
ollama list            # list locally available models
```

**Minimum model size:** Models under ~1B parameters (e.g. `smollm2:360m`, `smollm2:135m`) cannot reliably produce structured JSON. They return empty responses, which the app catches and reports:
```
RuntimeError: Ollama model 'smollm2:360m' returned an empty response. The model may be
too small to follow structured instructions. Try a larger model (e.g. qwen3:8b) by
setting OLLAMA_MODEL in .env.
```
Use at least a 3B–7B model. `qwen3:8b` is the recommended and tested choice.

**PowerShell env var syntax** — `KEY=value command` is Bash-only. Use:
```powershell
$env:GEMINI_API_KEY = "AIza..."; uv run python main.py "..." --count 3
```
Or set keys in `.env` (preferred).

## Configuration (env vars)

| Variable | Default | Description |
|---|---|---|
| `GEMINI_API_KEY` | — | Required when `LLM_PROVIDER=gemini` |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Any Gemini model ID |
| `LLM_PROVIDER` | `gemini` | `"gemini"` or `"ollama"` |
| `OLLAMA_MODEL` | `qwen3:8b` | Must be pulled locally |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `SERPAPI_API_KEY` | — | Optional SerpAPI fallback |
| `MAX_SEARCH_RESULTS` | `5` | Results fetched per query |
| `MAX_PAGE_CHARS` | `12000` | Characters sent to LLM per page |
| `REQUEST_TIMEOUT_SECONDS` | `20` | HTTP timeout for page scraping |
| `OUTPUT_PDF_PATH` | `ne555_report.pdf` | Default output file |

## Architecture

Three LLM calls per run, all through `llm_client.generate()`:

```
get_recommendations(user_prompt, count)          # recommender.py
  1. _generate_queries()   → N search queries    # LLM call 1
  2. search_and_fetch()    → SearchResult list   # web_searcher.py: DDG → SerpAPI fallback
     deduplicate by URL; early-stop at count×3 unique results
  3. extract_circuit()     → Circuit | None      # LLM call 2 (once per page)
     early-stop when valid circuits ≥ count×2
  4. _rank_circuits()      → ordered indices     # LLM call 3
  return circuits[ranked[:count]]

generate_pdf(circuits, ...)                      # pdf_generator.py
```

`config.py` exposes a `Settings` singleton. `gemini_api_key` is a `@property` that raises `KeyError` only when accessed — importing config without `GEMINI_API_KEY` set is safe when `LLM_PROVIDER=ollama`.

Search flow: DuckDuckGo full-page scrape → DDG snippet fallback (≥200 chars) → SerpAPI fallback (if key set).

## Key Conventions and Gotchas

- **JSON fence stripping** — always strip before `json.loads()`:
  `re.sub(r'^```(?:json)?\s*|\s*```$', '', text.strip())`

- **Gemini rate limits** — error class is `google.genai.errors.ClientError`; check `.code == 429` (NOT `.status_code`). `llm_client.py` handles this with a 60s sleep + one retry.

- **Ollama `think=False`** — passed in `llm_client.py` to disable `<think>` mode on qwen3-style reasoning models. Without it, qwen3 exhausts its token budget on internal reasoning and returns empty `content`. Non-reasoning models (smollm2, etc.) ignore this parameter.

- **ReportLab `&` in URLs** — `&` must be encoded as `&amp;` before embedding in `<link href="...">` tags. The `_href()` helper in `pdf_generator.py` does this automatically.

- **`_s()` style helper** — uses `kw.setdefault("fontName", _FONT)` so callers that pass an explicit `fontName` (bold styles) take precedence. Do not hardcode `fontName=_FONT` as a positional keyword — it will conflict and raise `TypeError`.

- **Unicode font** — `pdf_generator.py` auto-detects DejaVuSans (via matplotlib bundle or `C:\Windows\Fonts\`) for Ω, μ, etc. Falls back to Helvetica silently.

- **`[tool.uv] package = false`** — project is not installable as a library; all source files are flat in the project root.
