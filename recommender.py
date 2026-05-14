from __future__ import annotations

import json
import re
import sys

from config import settings
from extractor import extract_circuit
from llm_client import generate
from models import Circuit, SearchResult
from web_searcher import WebSearchError, search_and_fetch


class RecommenderError(Exception):
    pass


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _generate_queries(user_prompt: str, num_queries: int) -> list[str]:
    system = (
        "You are an electronics expert specialising in NE555 timer circuits. "
        "Generate targeted web search queries to find real NE555 designs matching user requirements. "
        "Rules: include 'NE555' or '555 timer' in every query; vary style (tutorials, schematics, "
        "calculators, EE forums); no conversational language. Return ONLY a JSON object."
    )
    user_msg = (
        f'User requirement: "{user_prompt}"\n'
        f"Generate {num_queries} distinct search queries.\n"
        'Return format: {"queries": ["query 1", "query 2", ...]}'
    )
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", generate(system=system, user_msg=user_msg).strip())
    data = json.loads(raw)
    queries = data.get("queries", [])
    if not isinstance(queries, list) or not queries:
        raise RecommenderError("LLM returned no search queries.")
    return [str(q) for q in queries]


def _deduplicate_results(results: list[SearchResult]) -> list[SearchResult]:
    seen: set[str] = set()
    unique: list[SearchResult] = []
    for r in results:
        if r.url not in seen:
            seen.add(r.url)
            unique.append(r)
    return unique


def _rank_circuits(circuits: list[Circuit], user_prompt: str) -> list[int]:
    if len(circuits) <= 1:
        return list(range(len(circuits)))

    lines = "\n".join(
        f"{i}. {c.name} — {c.match_explanation}" for i, c in enumerate(circuits)
    )
    system = (
        "You are an electronics expert. Rank NE555 circuit options from most to least relevant "
        "to the user's requirement. Prefer diversity of circuit type when relevance is similar. "
        "Return ONLY a JSON list of integer indices (0-based), most relevant first."
    )
    user_msg = f'Requirement: "{user_prompt}"\n\nCircuits:\n{lines}\n\nReturn format: [0, 3, 1, ...]'
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", generate(system=system, user_msg=user_msg, max_tokens=256).strip())
    try:
        indices = json.loads(raw)
        if isinstance(indices, list):
            valid = [i for i in indices if isinstance(i, int) and 0 <= i < len(circuits)]
            missing = [i for i in range(len(circuits)) if i not in valid]
            return valid + missing
    except Exception:
        pass
    return list(range(len(circuits)))


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def get_recommendations(user_prompt: str, count: int) -> list[Circuit]:
    """Orchestrate the full pipeline and return up to `count` Circuit objects."""
    num_queries = max(count * 2, count + 3)
    print(f"[recommender] Generating {num_queries} search queries…", file=sys.stderr)

    try:
        queries = _generate_queries(user_prompt, num_queries)
    except Exception as exc:
        raise RecommenderError(f"Query generation failed: {exc}") from exc

    # Search and deduplicate
    all_results: list[SearchResult] = []
    target_pool = count * 3
    for i, query in enumerate(queries):
        print(f"[recommender] Searching ({i + 1}/{len(queries)}): {query}", file=sys.stderr)
        try:
            results = search_and_fetch(query)
            all_results.extend(results)
        except WebSearchError as exc:
            print(f"[recommender] Search failed: {exc}", file=sys.stderr)

        unique_so_far = len(_deduplicate_results(all_results))
        if unique_so_far >= target_pool:
            break

    unique_results = _deduplicate_results(all_results)
    print(f"[recommender] {len(unique_results)} unique pages found", file=sys.stderr)

    if not unique_results:
        raise RecommenderError(
            "No search results were found. Try rephrasing your prompt or check your API keys."
        )

    # Extract circuits
    circuits: list[Circuit] = []
    target_extracted = count * 2
    for i, result in enumerate(unique_results):
        print(f"[recommender] Extracting circuit from: {result.url}", file=sys.stderr)
        circuit = extract_circuit(result, user_prompt)
        if circuit:
            circuits.append(circuit)
        if len(circuits) >= target_extracted:
            break

    if not circuits:
        raise RecommenderError(
            "Could not extract any circuits from the search results. "
            "Try a more specific prompt or check your API key / Ollama connection."
        )

    if len(circuits) < count:
        print(
            f"[recommender] Warning: only {len(circuits)} circuits found (requested {count})",
            file=sys.stderr,
        )

    # Rank and select
    print("[recommender] Ranking circuits…", file=sys.stderr)
    ranked = _rank_circuits(circuits, user_prompt)
    return [circuits[i] for i in ranked[:count]]
