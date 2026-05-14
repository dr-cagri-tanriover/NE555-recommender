from __future__ import annotations

import json
import re
import sys

from config import settings
from llm_client import generate
from models import Circuit, SearchResult

_SYSTEM = """\
You are an expert electronics engineer extracting structured NE555 circuit data from web page content.
You MUST return valid JSON only — no markdown fences, no commentary outside the JSON object.

BOM extraction rules:
1. Include EVERY distinct component you can identify (resistors, capacitors, ICs, diodes, etc.).
2. Use standard schematic reference prefixes: R for resistors, C for capacitors, D for diodes,
   U or IC for ICs, Q for transistors, L for inductors, SW for switches.
3. If a reference designator is not stated, assign one sequentially (R1, R2...).
4. Values must include units (kΩ, nF, V, etc.).
5. If no BOM is present but component values appear in the text, extract them and set is_complete to false.
6. If you cannot extract ANY component data, return an empty components list and set is_complete to false.

key_specs rules:
- Extract measurable electrical parameters: frequency, duty cycle, voltage, current, pulse width, timing period, etc.
- Add a relevance sentence only when you can directly connect the spec to the user requirement text.

Do NOT fabricate data. If information is missing, omit optional fields or use null.\
"""

_USER_TEMPLATE = """\
User requirement: {user_prompt}
Source URL: {url}
Source title: {title}

Page content:
{page_content}

Return ONLY this JSON (no markdown fences):
{{
  "name": "...",
  "description": "...",
  "circuit_type": "astable|monostable|bistable|schmitt-trigger|pwm|other",
  "key_specs": [
    {{"name": "...", "value": "...", "relevance": "..."}}
  ],
  "match_explanation": "...",
  "bom": {{
    "components": [
      {{"reference": "...", "part_name": "...", "value": "...", "quantity": 1, "notes": null}}
    ],
    "is_complete": true,
    "completeness_note": null
  }},
  "source_url": "{url}",
  "source_title": "{title}"
}}\
"""


def _strip_fences(text: str) -> str:
    return re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())


def extract_circuit(result: SearchResult, user_prompt: str) -> Circuit | None:
    """Call the LLM to extract a Circuit from one SearchResult. Returns None on any failure."""
    user_msg = _USER_TEMPLATE.format(
        user_prompt=user_prompt,
        url=result.url,
        title=result.title,
        page_content=result.raw_content,
    )

    for attempt in range(2):
        try:
            raw = generate(system=_SYSTEM, user_msg=user_msg, max_tokens=2048)
        except Exception as exc:
            print(f"[extractor] LLM error for {result.url}: {exc}", file=sys.stderr)
            return None

        cleaned = _strip_fences(raw)
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            if attempt == 0:
                print(f"[extractor] JSON parse failed for {result.url}, retrying", file=sys.stderr)
                continue
            print(f"[extractor] JSON parse failed twice for {result.url}, skipping", file=sys.stderr)
            return None

        try:
            circuit = Circuit.model_validate(data)
            circuit.search_query_used = result.url
            return circuit
        except Exception as exc:
            print(f"[extractor] Pydantic validation failed for {result.url}: {exc}", file=sys.stderr)
            return None

    return None
