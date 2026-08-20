from groq import Groq
from typing import List, Optional, Dict, Any
from utils.config import GROQ_API_KEY
import json
import re

# =====================================================
# Client Init
# =====================================================
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


# =====================================================
# Cost Estimator
# =====================================================
def _estimate_cost(days: int, hotel_pref: Optional[str]) -> Dict:

    hotel_price = {
        "Budget / Hostel": 1200,
        "3 Star": 3000,
        "4 Star": 6000,
        "5 Star": 12000
    }

    stay = hotel_price.get(hotel_pref, 3000) * days
    food = 800 * days
    transport = 500 * days
    attraction = 300 * days

    total = stay + food + transport + attraction

    return {
        "stay": stay,
        "food": food,
        "transport": transport,
        "tickets": attraction,
        "total": total
    }


# =====================================================
# Public API
# =====================================================
def generate_itinerary(
    city: str,
    days: int,
    places: Optional[List[str]] = None,
    user_places: Optional[List[str]] = None,
    hotel_pref: Optional[str] = None,
    max_places: int = 12
) -> Dict[str, Any]:

    if not client:
        return _error_response(city, days, "GROQ_API_KEY missing")

    if not city or not city.strip():
        return _error_response(city, days, "City not provided")

    city = city.strip()
    days = max(1, int(days))

    # --------------------------------------------------
    # Merge places
    # --------------------------------------------------
    final_places: List[str] = []

    if user_places:
        final_places.extend([p.strip() for p in user_places if p.strip()])

    if places:
        final_places.extend([p.strip() for p in places if p.strip()])

    seen = set()
    final_places = [p for p in final_places if not (p in seen or seen.add(p))]

    final_places = final_places[:max_places]

    if final_places:
        places_text = "\n".join(f"- {p}" for p in final_places)
    else:
        places_text = f"Choose the most famous real attractions inside {city}"

    hotel_text = hotel_pref if hotel_pref else "Not specified"

    # --------------------------------------------------
    # Strict Prompt
    # --------------------------------------------------
    prompt = f"""
You are an expert travel planner.

STRICT RULES:

1. Only suggest places inside {city}.
2. Never suggest places from another city.
3. Only real tourist attractions.
4. Each day must contain exactly 3 activities.
5. Activities must have time slots.
6. Places should be geographically close.

TIME FORMAT:

Morning (09:00–11:30)
Afternoon (12:30–15:30)
Evening (16:30–19:30)

City: {city}
Trip Duration: {days} days
Hotel Preference: {hotel_text}

Places to prioritize:
{places_text}

Return STRICT JSON ONLY.

FORMAT:

{{
 "itinerary":[
  {{
   "day":1,
   "activities":[
    {{
     "time":"09:00–11:30",
     "place":"Place name",
     "description":"Short sentence"
    }}
   ]
  }}
 ]
}}
"""

    # --------------------------------------------------
    # LLM Retry
    # --------------------------------------------------
    for attempt in range(2):

        try:

            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=1200
            )

            content = response.choices[0].message.content.strip()

            parsed = _extract_json(content)

            if not parsed:
                continue

            validated = _validate_itinerary(parsed, days)

            cost = _estimate_cost(days, hotel_pref)

            return {
                "city": city,
                "days": days,
                "itinerary": validated,
                "estimated_cost": cost
            }

        except Exception:
            continue

    return _fallback_itinerary(city, days, hotel_pref)


# =====================================================
# Extract JSON
# =====================================================
def _extract_json(text: str) -> Optional[List[Dict]]:

    try:

        text = text.replace("```json", "").replace("```", "")

        match = re.search(r"\{.*\}", text, re.DOTALL)

        if not match:
            return None

        parsed = json.loads(match.group())

        return parsed.get("itinerary")

    except Exception:
        return None


# =====================================================
# Validate Structure
# =====================================================
def _validate_itinerary(itinerary: List[Dict], days: int) -> List[Dict]:

    clean_days = []

    for i, day in enumerate(itinerary):

        activities = []

        for act in day.get("activities", []):

            place = act.get("place")

            if not place:
                continue

            activities.append({
                "time": act.get("time", "09:00–11:30"),
                "place": place.strip(),
                "description": act.get("description", "")
            })

        clean_days.append({
            "day": i + 1,
            "activities": activities[:3]
        })

    if len(clean_days) < days:
        for i in range(len(clean_days), days):
            clean_days.append({
                "day": i + 1,
                "activities": []
            })

    return clean_days[:days]


# =====================================================
# Fallback
# =====================================================
def _fallback_itinerary(city: str, days: int, hotel_pref: Optional[str]) -> Dict:

    plan = []

    for d in range(1, days + 1):

        plan.append({
            "day": d,
            "activities": [
                {
                    "time": "09:00–11:30",
                    "place": f"{city} city center",
                    "description": "Explore major landmarks"
                },
                {
                    "time": "12:30–15:30",
                    "place": f"{city} museum district",
                    "description": "Visit cultural museums"
                },
                {
                    "time": "16:30–19:30",
                    "place": f"{city} local market",
                    "description": "Enjoy local food and shopping"
                }
            ]
        })

    return {
        "city": city,
        "days": days,
        "itinerary": plan,
        "estimated_cost": _estimate_cost(days, hotel_pref),
        "fallback": True
    }


# =====================================================
# Error Response
# =====================================================
def _error_response(city: str, days: int, message: str) -> Dict:

    return {
        "city": city,
        "days": days,
        "itinerary": [],
        "error": message
    }