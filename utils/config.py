import os
from dotenv import load_dotenv
from typing import Dict, List, Optional

# ======================================================
# Load Environment Variables
# ======================================================
load_dotenv()


# ======================================================
# Helper: Clean ENV
# ======================================================
def _clean_env(key: str) -> Optional[str]:

    value = os.getenv(key)

    if value:
        value = value.strip()
        return value if value else None

    return None


# ======================================================
# Environment Mode
# ======================================================
APP_ENV = os.getenv("APP_ENV", "development").lower()

VALID_ENVS = {"development", "staging", "production"}

if APP_ENV not in VALID_ENVS:
    APP_ENV = "development"


# ======================================================
# API KEYS
# ======================================================
GROQ_API_KEY = _clean_env("GROQ_API_KEY")

OPENROUTESERVICE_API_KEY = _clean_env("OPENROUTESERVICE_API_KEY")

OPENTRIPMAP_API_KEY = _clean_env("OPENTRIPMAP_API_KEY")

FOURSQUARE_API_KEY = _clean_env("FOURSQUARE_API_KEY")

UNSPLASH_API_KEY = _clean_env("UNSPLASH_API_KEY")

PEXELS_API_KEY = _clean_env("PEXELS_API_KEY")


# ======================================================
# Feature Flags
# ======================================================
ENABLE_LLM = bool(GROQ_API_KEY)

ENABLE_ROUTING = bool(OPENROUTESERVICE_API_KEY)

ENABLE_POIS = bool(OPENTRIPMAP_API_KEY)

ENABLE_HOTELS = bool(FOURSQUARE_API_KEY)

ENABLE_IMAGES = bool(UNSPLASH_API_KEY or PEXELS_API_KEY)

ENABLE_WIKIPEDIA = True


# ======================================================
# Required Keys
# ======================================================
REQUIRED_KEYS: Dict[str, Optional[str]] = {
    "GROQ_API_KEY": GROQ_API_KEY,
    "OPENROUTESERVICE_API_KEY": OPENROUTESERVICE_API_KEY,
    "FOURSQUARE_API_KEY": FOURSQUARE_API_KEY,
}

OPTIONAL_KEYS: Dict[str, Optional[str]] = {
    "OPENTRIPMAP_API_KEY": OPENTRIPMAP_API_KEY,
    "UNSPLASH_API_KEY": UNSPLASH_API_KEY,
    "PEXELS_API_KEY": PEXELS_API_KEY,
}


# ======================================================
# Config Utilities
# ======================================================
def check_missing_keys(strict: bool = False) -> List[str]:

    missing = [k for k, v in REQUIRED_KEYS.items() if not v]

    if strict and missing:
        raise RuntimeError(
            "Missing required API keys: " + ", ".join(missing)
        )

    return missing


def get_config_status() -> Dict[str, bool]:

    return {
        k: bool(v)
        for k, v in {**REQUIRED_KEYS, **OPTIONAL_KEYS}.items()
    }


# ======================================================
# Mask API Keys
# ======================================================
def mask_key(value: Optional[str]) -> str:

    if not value:
        return "None"

    if len(value) <= 8:
        return "****"

    return f"{value[:4]}...{value[-4:]}"


# ======================================================
# Pretty Config Printer
# ======================================================
def print_config_status() -> None:

    print("\n🔍 TripSense Configuration")
    print("=" * 60)

    print("\n🔑 API Keys")

    for key, value in REQUIRED_KEYS.items():
        status = "✅" if value else "❌ REQUIRED"
        print(f"{key:<30} {status} {mask_key(value)}")

    for key, value in OPTIONAL_KEYS.items():
        status = "✅" if value else "⚠️ OPTIONAL"
        print(f"{key:<30} {status} {mask_key(value)}")

    print("\n⚙️ Feature Flags")
    print("-" * 60)

    print(f"LLM Enabled:        {ENABLE_LLM}")
    print(f"Routing Enabled:    {ENABLE_ROUTING}")
    print(f"POIs Enabled:       {ENABLE_POIS}")
    print(f"Hotels Enabled:     {ENABLE_HOTELS}")
    print(f"Images Enabled:     {ENABLE_IMAGES}")
    print(f"Wikipedia Enabled:  {ENABLE_WIKIPEDIA}")

    print("\n🌍 Environment:", APP_ENV)

    print("=" * 60)


# ======================================================
# Runtime Validation
# ======================================================
def validate_required_keys():

    if APP_ENV == "production":
        check_missing_keys(strict=True)


# ======================================================
# Health Check
# ======================================================
def health_check() -> Dict[str, str]:

    return {
        "environment": APP_ENV,
        "llm": "ok" if ENABLE_LLM else "disabled",
        "routing": "ok" if ENABLE_ROUTING else "disabled",
        "pois": "ok" if ENABLE_POIS else "disabled",
        "hotels": "ok" if ENABLE_HOTELS else "disabled",
        "images": "ok" if ENABLE_IMAGES else "disabled",
        "wikipedia": "ok" if ENABLE_WIKIPEDIA else "disabled"
    }


# ======================================================
# Development Warning
# ======================================================
if APP_ENV == "development":

    missing = check_missing_keys()

    if missing:

        print("\n⚠️ Missing API keys (development mode):")

        for key in missing:
            print(" -", key)

        print()