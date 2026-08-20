import requests
import json
import math
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from utils.config import OPENROUTESERVICE_API_KEY

# ======================================================
# Cache Setup
# ======================================================
CACHE_FILE = Path("data/routes_cache.json")
CACHE_FILE.parent.mkdir(exist_ok=True)

try:
    if CACHE_FILE.exists() and CACHE_FILE.read_text().strip():
        ROUTE_CACHE = json.loads(CACHE_FILE.read_text())
    else:
        ROUTE_CACHE = {}
except Exception:
    ROUTE_CACHE = {}

SESSION = requests.Session()


def _save_cache():
    try:
        CACHE_FILE.write_text(json.dumps(ROUTE_CACHE, indent=2))
    except Exception:
        pass


# ======================================================
# Normalize Cache Key
# ======================================================
def _normalize_key(p1: Dict, p2: Dict) -> Tuple[str, bool]:

    a = f"{round(p1['lat'],5)},{round(p1['lon'],5)}"
    b = f"{round(p2['lat'],5)},{round(p2['lon'],5)}"

    if a < b:
        return f"{a}__{b}", False
    else:
        return f"{b}__{a}", True


# ======================================================
# Haversine Distance
# ======================================================
def _haversine_km(p1: Dict, p2: Dict) -> float:

    R = 6371

    lat1 = math.radians(p1["lat"])
    lon1 = math.radians(p1["lon"])
    lat2 = math.radians(p2["lat"])
    lon2 = math.radians(p2["lon"])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return round(R * c, 2)


# ======================================================
# Polyline Cleaner (Map Stability)
# ======================================================
def _clean_polyline(polyline: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """
    Removes duplicate coordinates to prevent map blinking
    """

    cleaned = []

    for p in polyline:
        if not cleaned or cleaned[-1] != p:
            cleaned.append(p)

    return cleaned


# ======================================================
# Route Validation
# ======================================================
def _validate_route(route: Dict, p1: Dict, p2: Dict) -> bool:

    if not route:
        return False

    if route.get("distance_km") is None:
        return False

    if route["distance_km"] <= 0:
        return False

    if not route.get("polyline"):
        return False

    straight = _haversine_km(p1, p2)

    if route["distance_km"] < straight * 0.5:
        return False

    if route["distance_km"] > straight * 5:
        return False

    return True


# ======================================================
# Public API
# ======================================================
def get_route(p1: Dict, p2: Dict) -> Optional[Dict]:

    if not p1 or not p2:
        return None

    # Same location
    if abs(p1["lat"] - p2["lat"]) < 0.0001 and abs(p1["lon"] - p2["lon"]) < 0.0001:
        return {
            "distance_km": 0.0,
            "time_min": 0.0,
            "polyline": [(p1["lat"], p1["lon"])],
            "source": "self"
        }

    key, reversed_flag = _normalize_key(p1, p2)

    # ==================================================
    # CACHE CHECK
    # ==================================================
    if key in ROUTE_CACHE:

        cached = ROUTE_CACHE[key]

        polyline = (
            list(reversed(cached["polyline"]))
            if reversed_flag
            else cached["polyline"]
        )

        return {
            "distance_km": cached["distance_km"],
            "time_min": cached["time_min"],
            "polyline": polyline,
            "source": cached["source"]
        }

    # ==================================================
    # TRY OPENROUTESERVICE
    # ==================================================
    if OPENROUTESERVICE_API_KEY:

        route = _get_ors_route(p1, p2)

        if _validate_route(route, p1, p2):
            ROUTE_CACHE[key] = route
            _save_cache()
            return route

    # ==================================================
    # OSRM FALLBACK
    # ==================================================
    route = _get_osrm_route(p1, p2)

    if _validate_route(route, p1, p2):
        ROUTE_CACHE[key] = route
        _save_cache()
        return route

    # ==================================================
    # FINAL HAVERSINE FALLBACK
    # ==================================================
    straight_km = _haversine_km(p1, p2)

    fallback = {
        "distance_km": straight_km,
        "time_min": round(straight_km / 40 * 60, 1),
        "polyline": [
            (p1["lat"], p1["lon"]),
            (p2["lat"], p2["lon"])
        ],
        "source": "fallback"
    }

    ROUTE_CACHE[key] = fallback
    _save_cache()

    return fallback


# ======================================================
# OpenRouteService
# ======================================================
def _get_ors_route(p1: Dict, p2: Dict) -> Optional[Dict]:

    url = "https://api.openrouteservice.org/v2/directions/driving-car"

    headers = {
        "Authorization": OPENROUTESERVICE_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "coordinates": [
            [p1["lon"], p1["lat"]],
            [p2["lon"], p2["lat"]]
        ]
    }

    try:

        res = SESSION.post(
            url,
            json=payload,
            headers=headers,
            timeout=10
        )

        res.raise_for_status()

        data = res.json()

        feature = data["features"][0]
        segment = feature["properties"]["segments"][0]
        coords = feature["geometry"]["coordinates"]

        polyline = [(lat, lon) for lon, lat in coords]

        polyline = _clean_polyline(polyline)

        return {
            "distance_km": round(segment["distance"]/1000, 2),
            "time_min": round(segment["duration"]/60, 1),
            "polyline": polyline,
            "source": "openrouteservice"
        }

    except Exception:
        return None


# ======================================================
# OSRM FALLBACK
# ======================================================
def _get_osrm_route(p1: Dict, p2: Dict) -> Optional[Dict]:

    url = (
        f"http://router.project-osrm.org/route/v1/driving/"
        f"{p1['lon']},{p1['lat']};{p2['lon']},{p2['lat']}"
    )

    params = {
        "overview": "full",
        "geometries": "geojson"
    }

    try:

        res = SESSION.get(
            url,
            params=params,
            timeout=8
        )

        res.raise_for_status()

        data = res.json()

        if not data.get("routes"):
            return None

        route = data["routes"][0]

        coords = route["geometry"]["coordinates"]
        polyline = [(lat, lon) for lon, lat in coords]

        polyline = _clean_polyline(polyline)

        return {
            "distance_km": round(route["distance"]/1000, 2),
            "time_min": round(route["duration"]/60, 1),
            "polyline": polyline,
            "source": "osrm"
        }

    except Exception:
        return None