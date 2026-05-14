from __future__ import annotations

import sys
import time

import requests
from bs4 import BeautifulSoup
from ddgs import DDGS

from config import settings
from models import SearchResult


class WebSearchError(Exception):
    pass


def search_and_fetch(query: str) -> list[SearchResult]:
    """Return a list of SearchResult objects for the given query.

    Uses DuckDuckGo (no API key required) as the primary source.
    Falls back to SerpAPI if SERPAPI_API_KEY is set and DDG fails.
    """
    try:
        return _ddg_search(query)
    except Exception as exc:
        print(f"[web_searcher] DuckDuckGo failed ({exc})", file=sys.stderr)

    if settings.serpapi_api_key:
        print("[web_searcher] Falling back to SerpAPI", file=sys.stderr)
        try:
            return _serpapi_search(query)
        except Exception as exc:
            print(f"[web_searcher] SerpAPI also failed ({exc})", file=sys.stderr)

    raise WebSearchError(
        f"No results for query '{query}': DuckDuckGo search failed. "
        "Check your network connection or set SERPAPI_API_KEY as a fallback."
    )


def _ddg_search(query: str) -> list[SearchResult]:
    results: list[SearchResult] = []

    with DDGS() as ddgs:
        hits = list(ddgs.text(query, max_results=settings.max_search_results))

    for hit in hits:
        url = hit.get("href", "")
        title = hit.get("title", url)
        snippet = hit.get("body", "")

        # Try to fetch the full page; fall back to the DDG snippet
        full = _scrape_url(url)
        if full:
            results.append(full)
        elif len(snippet) >= 200:
            results.append(
                SearchResult(
                    url=url,
                    title=title,
                    raw_content=snippet[: settings.max_page_chars],
                    fetch_method="ddg_snippet",
                )
            )

    return results


def _serpapi_search(query: str) -> list[SearchResult]:
    resp = requests.get(
        "https://serpapi.com/search",
        params={"q": query, "api_key": settings.serpapi_api_key, "num": settings.max_search_results},
        timeout=settings.request_timeout,
    )
    resp.raise_for_status()
    links = [r["link"] for r in resp.json().get("organic_results", [])]

    results: list[SearchResult] = []
    for url in links:
        result = _scrape_url(url)
        if result:
            results.append(result)
        time.sleep(1)
    return results


def _scrape_url(url: str) -> SearchResult | None:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=settings.request_timeout)
        resp.raise_for_status()
    except Exception as exc:
        print(f"[web_searcher] Skipping {url}: {exc}", file=sys.stderr)
        return None

    soup = BeautifulSoup(resp.text, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title and soup.title.string else url
    text = soup.get_text(separator=" ", strip=True)

    if len(text) < 200:
        return None

    return SearchResult(
        url=url,
        title=title,
        raw_content=text[: settings.max_page_chars],
        fetch_method="ddg+scrape",
    )
