import datetime
import requests

from wallpaper.weather_codes import WEATHER_CODES


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


def bucket_cloud_cover(percent):
    if percent is None or percent <= 10:
        return "none"
    if percent <= 30:
        return "very_light"
    if percent <= 55:
        return "light"
    if percent <= 75:
        return "medium"
    if percent <= 90:
        return "heavy"
    return "very_heavy"


def bucket_rain(mm_per_hour):
    if not mm_per_hour or mm_per_hour <= 0:
        return "none"
    if mm_per_hour < 0.2:
        return "very_light"
    if mm_per_hour < 1:
        return "light"
    if mm_per_hour < 4:
        return "medium"
    if mm_per_hour < 10:
        return "heavy"
    return "very_heavy"


def bucket_snow(cm_per_hour):
    if not cm_per_hour or cm_per_hour <= 0:
        return "none"
    if cm_per_hour < 0.1:
        return "very_light"
    if cm_per_hour < 0.5:
        return "light"
    if cm_per_hour < 1.5:
        return "medium"
    if cm_per_hour < 4:
        return "heavy"
    return "very_heavy"


def get_weather(lat, lon, units):
    params = {
        "latitude": lat,
        "longitude": lon,

        "current": ",".join([
            "temperature_2m",
            "weather_code",
            "cloud_cover",
            "rain",
            "showers",
            "snowfall",
            "is_day",
        ]),

        "daily": ",".join([
            "sunrise",
            "sunset",
        ]),

        # Makes sunrise/sunset come back in local time.
        "timezone": "auto",

        # Only temperature needs to follow the user's display units.
        # Leave precipitation in metric so our intensity thresholds stay consistent.
        "temperature_unit": "fahrenheit" if units == "imperial" else "celsius",

        "forecast_days": 1,
    }

    response = requests.get(
        OPEN_METEO_URL,
        params=params,
        timeout=10,
    )

    response.raise_for_status()
    return response.json()


def get_air_quality(lat, lon):
    """
    Fetch atmospheric data that the normal weather forecast does not include.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": ",".join([
            "pm2_5",
            "pm10",
            "dust",
            "aerosol_optical_depth",
        ]),
        "timezone": "auto",
    }

    response = requests.get(
        OPEN_METEO_AIR_QUALITY_URL,
        params=params,
        timeout=10,
    )

    response.raise_for_status()
    return response.json()


def get_atmosphere(code_info, air_quality):
    """
    Pick the atmospheric artwork separately from ordinary clouds.

    Fog comes directly from the weather code. Smoke, haze, and dust use
    atmospheric measurements because the basic weather forecast does not
    describe them.
    """
    weather_atmosphere = code_info.get("atmosphere")

    if weather_atmosphere:
        return weather_atmosphere

    current_air = air_quality.get("current", {})

    pm2_5 = current_air.get("pm2_5") or 0
    dust = current_air.get("dust") or 0
    aerosol = current_air.get("aerosol_optical_depth") or 0

    # These are intentionally conservative starting thresholds.
    # They can be tuned after comparing the artwork with real conditions.
    if dust >= 50:
        return "dust"

    if pm2_5 >= 35:
        return "smoke"

    if aerosol >= 0.4:
        return "haze"

    return "none"


def get_unknown_weather_state():
    now = datetime.datetime.now()

    return {
        "weather": {
            "clouds": {
                "type": "normal",
                "coverage": "none",
            },
            "rain": "none",
            "snow": "none",
            "atmosphere": "none",
            "thunderstorm": False,
        },
        "sunrise": now.replace(hour=6, minute=0, second=0, microsecond=0),
        "sunset": now.replace(hour=18, minute=0, second=0, microsecond=0),
        "raw": {},
    }


def get_weather_state(lat, lon, units):
    try:
        weather_data = get_weather(lat, lon, units)

        # Air-quality data adds smoke/haze/dust, but the normal weather should still
        # work if this second source is temporarily unavailable.
        try:
            air_quality = get_air_quality(lat, lon)
        except (
            requests.RequestException,
            KeyError,
            TypeError,
            ValueError,
        ):
            air_quality = {}

        current = weather_data["current"]

        weather_code = int(current["weather_code"])
        code_info = WEATHER_CODES.get(
            weather_code,
            {"description": "Unknown"},
        )

        cloud_cover = current.get("cloud_cover", 0)

        # Open-Meteo separates large-scale rain from convective showers.
        # For the artwork, both are still wet stuff falling from the sky.
        rain_amount = (
            (current.get("rain") or 0)
            + (current.get("showers") or 0)
        )

        snow_amount = current.get("snowfall") or 0

        cloud_type = code_info.get("cloud_type", "normal")

        weather = {
            "clouds": {
                "type": cloud_type,
                "coverage": bucket_cloud_cover(cloud_cover),
            },
            "rain": bucket_rain(rain_amount),
            "snow": bucket_snow(snow_amount),
            "atmosphere": get_atmosphere(code_info, air_quality),
            "thunderstorm": code_info.get("thunderstorm", False),
        }

        sunrise = datetime.datetime.fromisoformat(
            weather_data["daily"]["sunrise"][0]
        )

        sunset = datetime.datetime.fromisoformat(
            weather_data["daily"]["sunset"][0]
        )

        # Keep a small compatibility-shaped raw block for the existing
        # weather overlay until we give that its own cleanup.
        raw = {
            "main": {
                "temp": current.get("temperature_2m"),
            },
            "weather": [
                {
                    "description": code_info["description"],
                }
            ],
            "open_meteo": weather_data,
            "open_meteo_air_quality": air_quality,
        }

        return {
            "weather": weather,
            "sunrise": sunrise,
            "sunset": sunset,
            "raw": raw,
        }

    except (
        requests.RequestException,
        KeyError,
        IndexError,
        TypeError,
        ValueError,
    ):
        return get_unknown_weather_state()