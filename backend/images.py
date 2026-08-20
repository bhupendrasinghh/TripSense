import requests
import json
from pathlib import Path
from typing import Optional
from utils.config import UNSPLASH_API_KEY, PEXELS_API_KEY
from backend.wikipedia import get_wikipedia_data

# ======================================================
# Cache Setup
# ======================================================
CACHE_FILE = Path("data/image_cache.json")
CACHE_FILE.parent.mkdir(exist_ok=True)

PLACEHOLDER_IMAGE = "https://via.placeholder.com/1000x600?text=TripSense"

try:
    if CACHE_FILE.exists() and CACHE_FILE.read_text().strip():
        IMAGE_CACHE = json.loads(CACHE_FILE.read_text())
    else:
        IMAGE_CACHE = {}
except Exception:
    IMAGE_CACHE = {}

SESSION = requests.Session()


def _save_cache():
    try:
        CACHE_FILE.write_text(json.dumps(IMAGE_CACHE, indent=2))
    except Exception:
        pass


# ======================================================
# Public API
# ======================================================
def get_image(query: str, category: str = "place") -> str:
    """
    Image priority:

    1 Wikipedia image
    2 Unsplash
    3 Pexels
    4 Placeholder
    """

    if not query or not query.strip():
        return PLACEHOLDER_IMAGE

    normalized_query = _normalize_query(query, category)

    # =================================================
    # CACHE
    # =================================================
    if normalized_query in IMAGE_CACHE:
        return IMAGE_CACHE[normalized_query]

    # =================================================
    # WIKIPEDIA IMAGE (BEST)
    # =================================================
    wiki = get_wikipedia_data(query)

    if wiki and wiki.get("image"):
        IMAGE_CACHE[normalized_query] = wiki["image"]
        _save_cache()
        return wiki["image"]

    # =================================================
    # UNSPLASH
    # =================================================
    img = _safe_unsplash(normalized_query)

    if img:
        IMAGE_CACHE[normalized_query] = img
        _save_cache()
        return img

    # =================================================
    # PEXELS
    # =================================================
    img = _safe_pexels(normalized_query)

    if img:
        IMAGE_CACHE[normalized_query] = img
        _save_cache()
        return img

    # =================================================
    # FALLBACK
    # =================================================
    IMAGE_CACHE[normalized_query] = PLACEHOLDER_IMAGE
    _save_cache()

    return PLACEHOLDER_IMAGE


# ======================================================
# UNSPLASH
# ======================================================
def _safe_unsplash(query: str) -> Optional[str]:

    if not UNSPLASH_API_KEY:
        return None

    url = "https://api.unsplash.com/search/photos"

    params = {
        "query": query,
        "client_id": UNSPLASH_API_KEY,
        "per_page": 1,
        "orientation": "landscape",
        "content_filter": "high"
    }

    for _ in range(2):

        try:
            res = SESSION.get(url, params=params, timeout=6)

            res.raise_for_status()

            data = res.json()

            if data.get("results"):
                return data["results"][0]["urls"]["regular"]

        except Exception:
            continue

    return None


# ======================================================
# PEXELS
# ======================================================
def _safe_pexels(query: str) -> Optional[str]:

    if not PEXELS_API_KEY:
        return None

    url = "https://api.pexels.com/v1/search"

    headers = {"Authorization": PEXELS_API_KEY}

    params = {
        "query": query,
        "per_page": 1,
        "orientation": "landscape"
    }

    for _ in range(2):

        try:
            res = SESSION.get(
                url,
                headers=headers,
                params=params,
                timeout=6
            )

            res.raise_for_status()

            data = res.json()

            if data.get("photos"):
                return data["photos"][0]["src"]["large"]

        except Exception:
            continue

    return None


# ======================================================
# Query Normalizer
# ======================================================
def _normalize_query(query: str, category: str) -> str:

    q = query.lower().strip()

    remove_words = [
        "near me",
        "location",
        "address",
        "area",
        "best",
        "famous",
        "tourist",
        "place",
        "visit"
    ]

    for w in remove_words:
        q = q.replace(w, "")

    if category == "hotel":
        q = f"{q} hotel exterior building travel"

    elif category == "city":
        q = f"{q} skyline aerial cityscape travel"

    else:
        q = f"{q} landmark travel photography"

    return q.strip()