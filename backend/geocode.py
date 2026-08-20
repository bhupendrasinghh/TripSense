import requests
import json
import time
from pathlib import Path
from typing import Optional, Dict, List

# ======================================================
# Cache Setup
# ======================================================
CACHE_FILE = Path("data/geocode_cache.json")
CACHE_FILE.parent.mkdir(exist_ok=True)

try:
    if CACHE_FILE.exists() and CACHE_FILE.read_text().strip():
        GEO_CACHE = json.loads(CACHE_FILE.read_text())
    else:
        GEO_CACHE = {}
except Exception:
    GEO_CACHE = {}

SESSION = requests.Session()


def _save_cache():
    try:
        CACHE_FILE.write_text(json.dumps(GEO_CACHE, indent=2))
    except Exception:
        pass


# ======================================================
# Query Cleaning
# ======================================================
def _normalize_query(query: str) -> str:

    q = query.lower().strip()

    remove_words = [
        "tourist place",
        "famous place",
        "location",
        "near me",
        "visit"
    ]

    for w in remove_words:
        q = q.replace(w, "")

    return q.strip()


# ======================================================
# Result Scoring
# ======================================================
def _score_result(result: dict, query: str) -> float:

    score = 0

    display = result.get("display_name", "").lower()
    q = query.lower()

    # Exact name match
    if q == result.get("name", "").lower():
        score += 50

    if q in display:
        score += 20

    # City / town boost
    if result.get("type") in [
        "city",
        "town",
        "village",
        "administrative"
    ]:
        score += 15

    # Importance weight
    importance = result.get("importance")

    if importance:
        score += importance * 10

    # Tourism objects boost
    if result.get("class") == "tourism":
        score += 15

    # Penalize weird results
    if len(display) > 180:
        score -= 5

    return score


# ======================================================
# Select Best Result
# ======================================================
def _select_best(results: List[dict], query: str):

    if not results:
        return None

    ranked = sorted(
        results,
        key=lambda r: _score_result(r, query),
        reverse=True
    )

    return ranked[0]


# ======================================================
# Public API
# ======================================================
def geocode_place(
    query: str,
    country_codes: Optional[str] = None,
    limit: int = 8
) -> Optional[Dict]:
    """
    Smart geocode with:
    - ranking
    - caching
    - retry
    - better place matching
    """

    if not query or not query.strip():
        return None

    query = _normalize_query(query)

    cache_key = f"{query}|{country_codes}"

    # ==================================================
    # CACHE CHECK
    # ==================================================
    if cache_key in GEO_CACHE:
        return GEO_CACHE[cache_key]

    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": query,
        "format": "json",
        "limit": limit,
        "addressdetails": 1
    }

    if country_codes:
        params["countrycodes"] = country_codes

    headers = {
        "User-Agent": "TripSense Travel Planner (AI App)"
    }

    data = []

    # ==================================================
    # Retry system
    # ==================================================
    for _ in range(2):

        try:

            res = SESSION.get(
                url,
                params=params,
                headers=headers,
                timeout=8
            )

            res.raise_for_status()

            data = res.json()

            if data:
                break

        except Exception:
            time.sleep(1)

    if not data:
        return None

    # ==================================================
    # Pick best result
    # ==================================================
    best = _select_best(data, query)

    if not best:
        return None

    try:

        result = {
            "name": best.get("display_name", query).split(",")[0],
            "lat": float(best["lat"]),
            "lon": float(best["lon"]),
            "display_name": best.get("display_name", ""),
            "type": best.get("type", ""),
            "importance": best.get("importance", 0)
        }

        GEO_CACHE[cache_key] = result
        _save_cache()

        return result

    except Exception:
        return None