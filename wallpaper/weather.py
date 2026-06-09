import datetime
import os
import requests

from wallpaper.weather_codes import WEATHER_CODES


def get_weather(api_key, lat, lon, units):
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": units,
    }

    response = requests.get(base_url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def get_unknown_weather_state():
    now_ts = int(datetime.datetime.now().timestamp())

    return {
        "weather": "unknown",
        "sunrise": now_ts + 6 * 3600,
        "sunset": now_ts + 18 * 3600,
        "raw": {},
    }


def get_weather_state(lat, lon, units):
    api_key = os.getenv("OPENWEATHER_API_KEY")

    if not api_key:
        return get_unknown_weather_state()

    try:
        weather_data = get_weather(api_key, lat, lon, units)

        weather = weather_data["weather"][0]
        weather_id = int(weather["id"])

        return {
            "weather": WEATHER_CODES.get(weather_id, "unknown"),
            "sunrise": weather_data["sys"]["sunrise"],
            "sunset": weather_data["sys"]["sunset"],
            "raw": weather_data,
        }

    except (
        requests.RequestException,
        KeyError,
        IndexError,
        TypeError,
        ValueError,
    ):
        return get_unknown_weather_state()


def normalize_weather(weather):
    return weather if weather != "unknown" else "clear"