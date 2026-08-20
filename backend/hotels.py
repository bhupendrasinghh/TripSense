import requests
import json
from pathlib import Path
from typing import List, Dict

from utils.config import FOURSQUARE_API_KEY
from backend.geocode import geocode_place
from backend.images import get_image

# ======================================================
# Cache Setup
# ======================================================
CACHE_FILE = Path("data/hotels_cache.json")
CACHE_FILE.parent.mkdir(exist_ok=True)

try:
    if CACHE_FILE.exists() and CACHE_FILE.read_text().strip():
        HOTELS_CACHE = json.loads(CACHE_FILE.read_text())
    else:
        HOTELS_CACHE = {}
except Exception:
    HOTELS_CACHE = {}

SESSION = requests.Session()


def _save_cache():
    try:
        CACHE_FILE.write_text(json.dumps(HOTELS_CACHE, indent=2))
    except Exception:
        pass


# ======================================================
# Hotel Classification
# ======================================================
BUDGET_KEYWORDS = [
    "oyo", "fab", "treebo", "ginger",
    "budget", "guest", "lodge", "inn"
]


def _classify_hotel(name: str) -> str:

    lname = name.lower()

    for k in BUDGET_KEYWORDS:
        if k in lname:
            return "🟢 Budget"

    return "🔵 Standard / Premium"


# ======================================================
# Ranking Score
# ======================================================
def _score_hotel(hotel: Dict) -> float:

    score = 0

    dist = hotel.get("distance_m")

    if isinstance(dist, (int, float)):
        score += max(0, 5000 - dist) / 400

    if "hotel" in hotel["name"].lower():
        score += 1.5

    if hotel["type"].startswith("🔵"):
        score += 1

    return score


# ======================================================
# Fallback hotels
# ======================================================
def _fallback_hotels(city: str, lat: float, lon: float) -> List[Dict]:

    hotels = [
        {
            "name": f"{city.title()} Grand Hotel",
            "address": f"{city.title()} City Center",
            "lat": lat,
            "lon": lon,
            "distance_m": None,
            "type": "🔵 Standard / Premium"
        },
        {
            "name": f"{city.title()} Budget Inn",
            "address": f"{city.title()} Downtown",
            "lat": lat,
            "lon": lon,
            "distance_m": None,
            "type": "🟢 Budget"
        }
    ]

    for h in hotels:
        h["image"] = get_image(h["name"], "hotel")

    return hotels


# ======================================================
# Public API
# ======================================================
def get_hotels(city: str, limit: int = 6) -> List[Dict]:

    if not city or not city.strip():
        return []

    city = city.strip().lower()

    # ==================================================
    # Cache check
    # ==================================================
    if city in HOTELS_CACHE:
        return HOTELS_CACHE[city][:limit]

    hotels: List[Dict] = []

    # ==================================================
    # Geocode city
    # ==================================================
    city_geo = geocode_place(city)

    if not city_geo:
        return []

    lat = city_geo["lat"]
    lon = city_geo["lon"]

    # ==================================================
    # Foursquare API
    # ==================================================
    if FOURSQUARE_API_KEY:

        try:

            url = "https://api.foursquare.com/v3/places/search"

            headers = {
                "Authorization": FOURSQUARE_API_KEY,
                "Accept": "application/json"
            }

            params = {
                "ll": f"{lat},{lon}",
                "radius": 6000,
                "categories": "19014",
                "limit": 30,
                "sort": "RELEVANCE"
            }

            res = SESSION.get(
                url,
                headers=headers,
                params=params,
                timeout=10
            )

            res.raise_for_status()

            data = res.json()

            for h in data.get("results", []):

                name = h.get("name")

                if not name:
                    continue

                location = h.get("location", {})
                geocodes = h.get("geocodes", {}).get("main", {})

                hotel = {
                    "name": name,
                    "address": location.get("formatted_address", city),
                    "lat": geocodes.get("latitude"),
                    "lon": geocodes.get("longitude"),
                    "distance_m": h.get("distance"),
                    "type": _classify_hotel(name)
                }

                hotels.append(hotel)

        except Exception:
            pass

    # ==================================================
    # Remove duplicates
    # ==================================================
    unique = {}

    for h in hotels:
        unique[h["name"]] = h

    hotels = list(unique.values())

    # ==================================================
    # Ranking
    # ==================================================
    hotels.sort(
        key=lambda x: _score_hotel(x),
        reverse=True
    )

    # ==================================================
    # Add hotel images
    # ==================================================
    for h in hotels:
        h["image"] = get_image(h["name"], "hotel")

    # ==================================================
    # Safe fallback
    # ==================================================
    if not hotels:
        hotels = _fallback_hotels(city, lat, lon)

    HOTELS_CACHE[city] = hotels
    _save_cache()

    return hotels[:limit]