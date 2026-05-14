# NE555 Circuit Recommender — User Guide

## What This Application Does

The NE555 Circuit Recommender takes a plain-English description of the NE555 timer circuit you need, searches the web for real matching designs, and produces a PDF report containing:

- Circuit name, description, and type (astable, monostable, bistable, etc.)
- Key electrical specifications (frequency, duty cycle, pulse width, voltage, etc.)
- A Bill of Materials (BOM) table with reference designators, component values, and quantities
- Clickable hyperlinks to the original source pages
- A cover page with a table of contents

The app makes three LLM calls per run: one to generate targeted search queries, one per result page to extract circuit data, and one final call to rank and select the best matches.

---

## Prerequisites

### 1. Python and uv

- Python 3.12 must be installed
- `uv` must be installed ([https://docs.astral.sh/uv/](https://docs.astral.sh/uv/))

Bootstrap the environment once:

```powershell
uv venv .venv --python "C:\Program Files\Python312\python.exe"
uv sync
```

### 2. LLM Provider

You need either a **Gemini API key** (free, cloud-based) or a running **Ollama server** (local, no API key). See the [LLM Provider Configuration](#llm-provider-configuration) section below.

---

## Configuration — `.env` File

Copy `.env.example` to `.env` and fill in the values that apply to your setup. All settings have defaults; only `GEMINI_API_KEY` is required (when using the Gemini provider).

### LLM Provider Settings

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `gemini` | Which LLM backend to use: `gemini` or `ollama` |
| `GEMINI_API_KEY` | — | **Required when `LLM_PROVIDER=gemini`.** Get a free key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Gemini model ID. Recommended: `gemini-3.1-flash-lite` (confirmed quota-friendly) |
| `OLLAMA_MODEL` | `qwen3:8b` | Ollama model name. Must be pulled locally before use (`ollama pull qwen3:8b`) |
| `OLLAMA_HOST` | `http://localhost:11434` | URL of your Ollama server |

### Search and Scraping Settings

| Variable | Default | Description |
|---|---|---|
| `MAX_SEARCH_RESULTS` | `5` | Number of web results fetched per search query |
| `MAX_PAGE_CHARS` | `12000` | Maximum characters of page content sent to the LLM per page |
| `REQUEST_TIMEOUT_SECONDS` | `20` | HTTP timeout (seconds) when scraping web pages |
| `SERPAPI_API_KEY` | — | Optional. Enables SerpAPI as a fallback if DuckDuckGo search fails |

### Output Settings

| Variable | Default | Description |
|---|---|---|
| `OUTPUT_PDF_PATH` | `ne555_report.pdf` | Default path for the generated PDF report |

### Example `.env` for Gemini

```
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIzaSy...
GEMINI_MODEL=gemini-3.1-flash-lite
OUTPUT_PDF_PATH=ne555_report.pdf
```

### Example `.env` for Ollama

```
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen3:8b
OLLAMA_HOST=http://localhost:11434
OUTPUT_PDF_PATH=ne555_report.pdf
```

---

## LLM Provider Configuration

### Using Gemini (recommended for first-time users)

1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey) and create a free API key
2. Add `GEMINI_API_KEY=AIza...` to your `.env`
3. Set `GEMINI_MODEL=gemini-3.1-flash-lite` to avoid free-tier quota issues

If you hit quota limits (`RESOURCE_EXHAUSTED` error), switch to a different model variant:
- `gemini-3.1-flash-lite` — recommended, confirmed quota-friendly
- `gemini-1.5-flash` — separate quota pool
- `gemini-2.0-flash-lite` — separate quota pool
- **Do not use** `gemini-1.5-flash-8b` — not available on the free API endpoint

### Using Ollama (local, no API key required)

1. Install Ollama from [ollama.com](https://ollama.com)
2. Pull a model (minimum ~3B parameters recommended):
   ```powershell
   ollama pull qwen3:8b
   ```
3. Start the server:
   ```powershell
   ollama serve
   ```
4. Set `LLM_PROVIDER=ollama` in your `.env`

> **Important:** Ollama must be running (`ollama serve`) before you invoke the app.  
> Models under ~1B parameters (e.g. `smollm2:360m`) are too small to produce structured JSON reliably and will cause an error. Use at least a 3B–7B model; `qwen3:8b` is tested and recommended.

---

## Tested Models

The following models have been tested and confirmed working with this app. Results are grouped by output quality.

### Recommended — good output quality

| Provider | Model | Notes |
|---|---|---|
| Gemini | `gemini-3.1-flash-lite` | Confirmed quota-friendly; recommended default |
| Gemini | `gemini-2.0-flash` | Good results; may hit free-tier daily quota |
| Ollama | `qwen3:8b` | Tested and recommended for local inference |
| Ollama | `gemma3:1b` | Tested; produces acceptable results |

### Smoke-test only — poor output quality

| Provider | Model | Notes |
|---|---|---|
| Ollama | `smollm2:360m` | Too small for reliable JSON; may fail mid-run |
| Ollama | `smollm2:135m` | Same as above; pipeline smoke tests only |

### Unavailable / broken

| Provider | Model | Notes |
|---|---|---|
| Gemini | `gemini-1.5-flash-8b` | Not available on the v1beta API endpoint (404) |

> **Why smaller models fail:** Models under ~1B parameters cannot reliably follow structured JSON instructions. They produce empty or malformed responses, which the app catches with a clear `RuntimeError`. Even when they parse successfully, the extracted circuit data is poor quality. Use at least a 3B–7B model for real results.

---

## Command-Line Usage

```
uv run python main.py [OPTIONS] [PROMPT]...
uv run python main.py [OPTIONS] --prompt-file FILE
```

Supply the circuit description either inline as `PROMPT` text or from a file with `--prompt-file`. The two options are mutually exclusive.

`PROMPT` (inline) — quotes are optional; multiple unquoted words are joined automatically.

`--prompt-file` (file) — useful for longer, more detailed descriptions. The file is read as plain UTF-8 text. The full content (including newlines) is used as the prompt.

### Options

| Option | Short | Default | Description |
|---|---|---|---|
| `--prompt-file FILE` | `-f FILE` | — | Read circuit description from a text file instead of the command line |
| `--count N` | `-n N` | `3` | Number of circuits to recommend (1–10) |
| `--output PATH` | `-o PATH` | from `OUTPUT_PDF_PATH` | Output PDF file path |
| `--verbose` | `-v` | off | Print detailed progress to the terminal |
| `--help` | | | Show usage help and exit |

---

## Example Commands

```powershell
# Basic: find 3 astable oscillator circuits, save to ne555_report.pdf
uv run python main.py "astable oscillator 1kHz audio tone" --count 3

# Monostable timer with verbose progress output
uv run python main.py "monostable pulse timer 5 second delay" --count 2 --verbose

# Save report to a custom path
uv run python main.py "PWM motor speed controller" --count 5 --output pwm_report.pdf

# Unquoted prompt (words are joined automatically)
uv run python main.py astable oscillator 1kHz --count 3

# Detailed prompt from a text file
uv run python main.py --prompt-file my_requirements.txt --count 3

# Prompt file with custom output path
uv run python main.py --prompt-file my_requirements.txt --count 5 --output detailed_report.pdf

# Show all available options
uv run python main.py --help
```

**Example prompt file** (`my_requirements.txt`):
```
I need an NE555 astable oscillator that generates a 1kHz square wave for audio
tone generation. The circuit should run on a 9V supply and drive a small 8-ohm
speaker directly. Prefer designs with a simple RC timing network and a duty
cycle close to 50%.
```

### Overriding Settings at Runtime (PowerShell)

If you need to temporarily override a `.env` value without editing the file:

```powershell
# Use a different Gemini model for one run
$env:GEMINI_MODEL = "gemini-1.5-flash"; uv run python main.py "bistable flip-flop" --count 2

# Switch to Ollama for one run
$env:LLM_PROVIDER = "ollama"; uv run python main.py "schmitt trigger" --count 3
```

> **Note:** `KEY=value command` (Bash syntax) does not work in PowerShell. Always use `$env:KEY = "value"; command`.

---

## Output

The generated PDF contains:

1. **Cover page** — your prompt, date, circuits found vs. requested, and a clickable table of contents
2. **One section per circuit** with:
   - Circuit name and type
   - Description paragraph
   - "Match to Requirements" explanation
   - Key Specifications table
   - Bill of Materials table (with a yellow warning if the BOM is incomplete)
   - Clickable source hyperlink(s)

Open the PDF in any PDF viewer. All source links are clickable.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `KeyError: GEMINI_API_KEY` | Missing API key | Add `GEMINI_API_KEY=...` to `.env` |
| `RESOURCE_EXHAUSTED` / 429 error | Gemini free-tier quota hit | Switch to `GEMINI_MODEL=gemini-3.1-flash-lite` or use Ollama |
| `RuntimeError: Ollama model '...' returned an empty response` | Model too small | Use a ≥3B model: `OLLAMA_MODEL=qwen3:8b` |
| `Connection refused` (Ollama) | Ollama server not running | Run `ollama serve` in a separate terminal |
| `No search results were found` | Network issue or DuckDuckGo blocked | Check network; optionally set `SERPAPI_API_KEY` for fallback |
| `Could not extract any circuits` | Prompt too vague or LLM issue | Try a more specific prompt; check API key/Ollama connection |
| Fewer circuits than requested | Not enough matching pages found | Try a broader prompt or increase `MAX_SEARCH_RESULTS` in `.env` |
| `Ω` / `μ` shown as `?` in PDF | Unicode font not found | Install matplotlib (`uv add matplotlib`) — app auto-detects DejaVuSans from it |
