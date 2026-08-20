import requests
import json
from pathlib import Path
from typing import List, Dict, Optional
from utils.config import OPENTRIPMAP_API_KEY

# ======================================================
# Cache Setup
# ======================================================
CACHE_FILE = Path("data/pois_cache.json")
CACHE_FILE.parent.mkdir(exist_ok=True)

try:
    if CACHE_FILE.exists() and CACHE_FILE.read_text().strip():
        POI_CACHE = json.loads(CACHE_FILE.read_text())
    else:
        POI_CACHE = {}
except Exception:
    POI_CACHE = {}

SESSION = requests.Session()


def _save_cache():
    try:
        CACHE_FILE.write_text(json.dumps(POI_CACHE, indent=2))
    except Exception:
        pass


# ======================================================
# Public API
# ======================================================
def get_pois(
    lat: float,
    lon: float,
    radius: int = 5000,
    limit: int = 10,
    kinds: Optional[str] = None
) -> List[Dict]:

    if lat is None or lon is None:
        return []

    cache_key = f"{round(lat,4)}_{round(lon,4)}_{radius}_{limit}"

    if cache_key in POI_CACHE:
        return POI_CACHE[cache_key]

    if not OPENTRIPMAP_API_KEY:
        return []

    # --------------------------------------------------
    # Tourist categories
    # --------------------------------------------------
    if not kinds:
        kinds = (
            "interesting_places,"
            "historic,"
            "architecture,"
            "cultural,"
            "religion,"
            "monuments_and_memorials,"
            "natural"
        )

    # --------------------------------------------------
    # Progressive radius search
    # --------------------------------------------------
    search_radii = [radius, radius * 2, radius * 3, radius * 5]

    all_results: List[Dict] = []

    for r in search_radii:

        raw_places = _fetch_pois(lat, lon, r, limit * 6, kinds)

        filtered = _filter_and_rank(raw_places)

        all_results.extend(filtered)

        if len(all_results) >= limit * 2:
            break

    # --------------------------------------------------
    # Deduplicate places
    # --------------------------------------------------
    unique = {}

    for p in all_results:

        key = p["name"].lower()

        if key not in unique:
            unique[key] = p

        else:
            # keep higher importance
            if p["importance"] > unique[key]["importance"]:
                unique[key] = p

    final = list(unique.values())

    # --------------------------------------------------
    # Ranking logic
    # --------------------------------------------------
    final.sort(
        key=lambda x: (
            -x["importance"],
            x["distance_m"] if isinstance(x.get("distance_m"), (int, float)) else float("inf")
        )
    )

    final = final[:limit]

    POI_CACHE[cache_key] = final
    _save_cache()

    return final


# ======================================================
# Fetch POIs from OpenTripMap
# ======================================================
def _fetch_pois(lat, lon, radius, limit, kinds):

    url = "https://api.opentripmap.com/0.1/en/places/radius"

    params = {
        "lat": lat,
        "lon": lon,
        "radius": radius,
        "limit": limit,
        "kinds": kinds,
        "format": "json",
        "apikey": OPENTRIPMAP_API_KEY
    }

    try:

        res = SESSION.get(
            url,
            params=params,
            timeout=8
        )

        res.raise_for_status()

        return res.json()

    except Exception:
        return []


# ======================================================
# Filter + Rank POIs
# ======================================================
def _filter_and_rank(raw_places):

    results: List[Dict] = []

    for item in raw_places:

        name = item.get("name")

        if not name:
            continue

        name = name.strip()

        # ---------------------------------------------
        # Remove junk
        # ---------------------------------------------
        if len(name) < 3:
            continue

        if name.lower() in ["unknown", "yes", "no name"]:
            continue

        if "shop" in name.lower():
            continue

        if "hotel" in name.lower():
            continue

        if "restaurant" in name.lower():
            continue

        point = item.get("point", {})

        p_lat = point.get("lat")
        p_lon = point.get("lon")

        if not p_lat or not p_lon:
            continue

        dist = item.get("dist")

        # Importance score from API
        importance = item.get("rate", 0)

        results.append({
            "name": name,
            "lat": float(p_lat),
            "lon": float(p_lon),
            "distance_m": dist,
            "importance": importance
        })

    return results