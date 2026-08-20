import requests
import json
from pathlib import Path
from typing import Optional, Dict

# ======================================================
# Cache Setup
# ======================================================
CACHE_FILE = Path("data/wiki_cache.json")
CACHE_FILE.parent.mkdir(exist_ok=True)

try:
    if CACHE_FILE.exists() and CACHE_FILE.read_text().strip():
        WIKI_CACHE = json.loads(CACHE_FILE.read_text())
    else:
        WIKI_CACHE = {}
except Exception:
    WIKI_CACHE = {}

SESSION = requests.Session()


def _save_cache():
    try:
        CACHE_FILE.write_text(json.dumps(WIKI_CACHE, indent=2))
    except Exception:
        pass


# ======================================================
# Public API
# ======================================================
def get_wikipedia_data(place: str) -> Optional[Dict]:
    """
    Returns clean Wikipedia info for TripSense.

    {
        "title": str
        "summary": str
        "image": str
        "url": str
        "lat": float | None
        "lon": float | None
    }
    """

    if not place or not place.strip():
        return None

    place = place.strip()
    cache_key = place.lower()

    # ==================================================
    # CACHE
    # ==================================================
    if cache_key in WIKI_CACHE:
        return WIKI_CACHE[cache_key]

    # ==================================================
    # DIRECT PAGE
    # ==================================================
    data = _fetch_summary(place)

    # ==================================================
    # SEARCH IF PAGE NOT FOUND
    # ==================================================
    if not data:
        title = _search_page(place)

        if title:
            data = _fetch_summary(title)

    if not data:
        return None

    # ==================================================
    # CLEAN RESULT
    # ==================================================
    summary = data.get("extract", "")

    if summary:
        summary = summary.split(". ")[0:2]
        summary = ". ".join(summary) + "."

    image = None

    if data.get("originalimage"):
        image = data["originalimage"]["source"]

    elif data.get("thumbnail"):
        image = data["thumbnail"]["source"]

    coordinates = data.get("coordinates")

    result = {
        "title": data.get("title"),
        "summary": summary,
        "image": image,
        "url": data.get("content_urls", {})
            .get("desktop", {})
            .get("page"),
        "lat": coordinates.get("lat") if coordinates else None,
        "lon": coordinates.get("lon") if coordinates else None
    }

    # ==================================================
    # CACHE SAVE
    # ==================================================
    WIKI_CACHE[cache_key] = result
    _save_cache()

    return result


# ======================================================
# Fetch Page Summary
# ======================================================
def _fetch_summary(title: str) -> Optional[Dict]:

    title = title.replace(" ", "_")

    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"

    headers = {
        "User-Agent": "TripSense AI Travel Planner"
    }

    for _ in range(2):

        try:
            res = SESSION.get(
                url,
                headers=headers,
                timeout=8
            )

            if res.status_code != 200:
                return None

            return res.json()

        except Exception:
            continue

    return None


# ======================================================
# Wikipedia Search
# ======================================================
def _search_page(query: str) -> Optional[str]:

    url = "https://en.wikipedia.org/w/api.php"

    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": 1,
        "format": "json"
    }

    try:

        res = SESSION.get(
            url,
            params=params,
            timeout=8
        )

        data = res.json()

        results = data.get("query", {}).get("search")

        if results:
            return results[0]["title"]

    except Exception:
        pass

    return None