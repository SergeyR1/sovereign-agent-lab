"""
src/week2/edinburgh_apis.py
============================
Week 2, Lab 3: External APIs — geocoding and weather from Open-Meteo (free, no key).
"""

import json
import time
import requests

# ─── WMO Weather Code descriptions ───────────────────────────────────────────

WMO_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Light rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Light snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Light rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with light hail",
    99: "Thunderstorm with heavy hail",
}


def http_get(url: str, params: dict = None, timeout: float = 8.0, max_retries: int = 3) -> dict:
    """
    HTTP GET with exponential backoff on 429/5xx errors.

    Args:
        url: The URL to fetch.
        params: Query parameters.
        timeout: Request timeout in seconds.
        max_retries: Maximum retry attempts.

    Returns:
        dict with success, data (or error).
    """
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, params=params, timeout=timeout)
            if resp.status_code == 200:
                return {"success": True, "data": resp.json()}
            elif resp.status_code in (429, 500, 502, 503, 504):
                wait = 2 ** attempt
                print(f"[HTTP] {resp.status_code} on attempt {attempt + 1}, retrying in {wait}s...")
                time.sleep(wait)
                continue
            else:
                return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        except requests.exceptions.Timeout:
            return {"success": False, "error": f"Timeout after {timeout}s"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    return {"success": False, "error": f"Max retries ({max_retries}) exceeded"}


def geocode_location(location: str) -> dict:
    """
    Geocode a location name using Open-Meteo's free geocoding API.

    Args:
        location: Place name (e.g., "Edinburgh Old Town").

    Returns:
        dict with success, latitude, longitude, name, country.
    """
    result = http_get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": location, "count": 1},
    )

    if not result["success"]:
        return result

    data = result["data"]
    results_list = data.get("results", [])
    if not results_list:
        return {"success": False, "error": f"No geocoding results for '{location}'"}

    loc = results_list[0]
    return {
        "success": True,
        "latitude": loc["latitude"],
        "longitude": loc["longitude"],
        "name": loc.get("name", location),
        "country": loc.get("country", "Unknown"),
    }


def get_current_weather(latitude: float, longitude: float) -> dict:
    """
    Get current weather from Open-Meteo forecast API.

    Args:
        latitude: Geographic latitude.
        longitude: Geographic longitude.

    Returns:
        dict with 5 normalized fields: temp, wind, precipitation, description, outdoor_suitable.
    """
    result = http_get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,weather_code,precipitation,wind_speed_10m",
            "forecast_days": 1,
        },
    )

    if not result["success"]:
        return result

    current = result["data"].get("current", {})
    weather_code = current.get("weather_code", -1)

    return {
        "success": True,
        "temp": current.get("temperature_2m"),
        "wind": current.get("wind_speed_10m"),
        "precipitation": current.get("precipitation"),
        "description": WMO_CODES.get(weather_code, f"WMO code {weather_code}"),
        "outdoor_suitable": weather_code in {0, 1, 2},
    }


# Tool schemas for LLM tool calling
API_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "geocode_location",
            "description": "Geocode a location name to latitude/longitude using Open-Meteo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "Place name to geocode"},
                },
                "required": ["location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get current weather at given coordinates from Open-Meteo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "latitude": {"type": "number", "description": "Geographic latitude"},
                    "longitude": {"type": "number", "description": "Geographic longitude"},
                },
                "required": ["latitude", "longitude"],
            },
        },
    },
]


if __name__ == "__main__":
    print("Edinburgh APIs Demo")
    print("=" * 50)

    geo = geocode_location("Edinburgh Old Town")
    print(f"\n[Geocode] Edinburgh Old Town → {json.dumps(geo, indent=2)}")

    if geo["success"]:
        weather = get_current_weather(geo["latitude"], geo["longitude"])
        print(f"\n[Weather] → {json.dumps(weather, indent=2)}")
