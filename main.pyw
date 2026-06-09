# ~~~~~ IMPORTS ~~~~~
from calendar import month
import ctypes
import datetime
from multiprocessing.util import debug
import json

try:
    import comtypes
    import comtypes.client
    from comtypes import GUID, COMMETHOD, HRESULT
    from ctypes import POINTER, c_uint
    from ctypes.wintypes import LPWSTR, RECT
except ImportError:
    comtypes = None

from pathlib import Path 

# ~~~~~ END IMPORTS ~~~~~


# ~~~~~ CONSTANTS ~~~~~
BASE_DIR = Path(__file__).resolve().parent

CONFIG_PATH = BASE_DIR / "config.json"
STATE_PATH = BASE_DIR / "state.json"
LOG_PATH = BASE_DIR / "debug_log.txt"

ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR = BASE_DIR / "output"

DEBUG_HOUR_OVERRIDE = None # int from 0-23, or None to disable 
DEBUG_TIME_OVERRIDE = None # time of day like 'dawn', 'noon', 'dusk', etc., or None to disable
DEBUG_WEATHER_OVERRIDE = None # weather code like 'clear', 'rain', 'snow', etc., or None to disable
DEBUG_SEASON_OVERRIDE = None # 'early_spring', 'mid_summer', 'late_autumn', 'mid_winter', etc., or None to disable
DEBUG_HOLIDAY_OVERRIDE = None # 'valentines', 'halloween', 'thanksgiving', 'christmas_eve', 'christmas_day', etc., or None to disable

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

DEBUG = config.get("debug", False)

LAT = config["lat"]
LON = config["lon"]
UNITS = config["units"]  
# ~~~~~ END CONSTANTS ~~~~~


# ~~~~~ FUNCTIONS ~~~~~
from wallpaper.logging import debug_log as _debug_log
def debug_log(message):
    _debug_log(message, debug=DEBUG, log_path=LOG_PATH)


from wallpaper.state import load_state as _load_state, save_state as _save_state
def load_state():
    return _load_state(STATE_PATH)
def save_state(state):
    _save_state(state, STATE_PATH)  

from wallpaper.image_composer import compose_wallpaper
from wallpaper.time_buckets import get_time_bucket_by_sun, get_shade_by_bucket, get_star_bucket
from wallpaper.seasons import get_season
from wallpaper.holidays import get_holiday
from wallpaper.weather import get_weather_state, normalize_weather
from wallpaper.overlay import add_weather_overlay


def optional_layer(path):
    """Return a layer path only when the file exists, otherwise skip it."""
    return path if path and path.exists() else None


def get_layer_paths(bucket, stars, season, holiday, weather, shade, layout="one_monitor"):
    layers = []

    sky_path = ASSETS_DIR / "sky" / layout / f"{bucket}.png"
    stars_path = ASSETS_DIR / "stars" / layout / f"{stars}.png"
    weather_path = ASSETS_DIR / "weather" / layout / f"{weather}.png"

    layers.append(optional_layer(sky_path))
    layers.append(optional_layer(stars_path))

    if layout == "vertical":
        holiday_path = ASSETS_DIR / "holiday" / "vertical" / f"{holiday}.png" if holiday != "none" else None

        layers.extend([
            optional_layer(weather_path),
            optional_layer(holiday_path),
            # moon later
            # ui overlay later
        ])

    else:
        season_path = ASSETS_DIR / "season" / layout / f"{season}.png"
        holiday_path = ASSETS_DIR / "holiday" / layout / f"{holiday}.png" if holiday != "none" else None
        shade_path = ASSETS_DIR / "shade" / layout / f"{shade}.png" if shade != "none" else None
        holiday_lights_path = ASSETS_DIR / "holiday_lights" / layout / f"{holiday}.png" if holiday != "none" else None

        layers.extend([
            optional_layer(season_path),
            optional_layer(holiday_path),
            optional_layer(weather_path),
            optional_layer(shade_path),
            optional_layer(holiday_lights_path),
        ])

    return layers


class IDesktopWallpaper(comtypes.IUnknown if comtypes is not None else object):
    if comtypes is not None:
        _iid_ = GUID("{B92B56A9-8B55-4E14-9A89-0199BBB6F93B}")
        _methods_ = [
            COMMETHOD([], HRESULT, "SetWallpaper",
                      (["in"], LPWSTR, "monitorID"),
                      (["in"], LPWSTR, "wallpaper")),
            COMMETHOD([], HRESULT, "GetWallpaper",
                      (["in"], LPWSTR, "monitorID"),
                      (["out"], POINTER(LPWSTR), "wallpaper")),
            COMMETHOD([], HRESULT, "GetMonitorDevicePathAt",
                      (["in"], c_uint, "monitorIndex"),
                      (["out"], POINTER(LPWSTR), "monitorID")),
            COMMETHOD([], HRESULT, "GetMonitorDevicePathCount",
                      (["out"], POINTER(c_uint), "count")),
            COMMETHOD([], HRESULT, "GetMonitorRECT",
                      (["in"], LPWSTR, "monitorID"),
                      (["out"], POINTER(RECT), "displayRect")),
        ]


def get_desktop_wallpaper_object():
    if comtypes is None:
        raise RuntimeError("Missing dependency: pip install comtypes")

    return comtypes.client.CreateObject(
        GUID("{C2CF3110-460E-4FC1-B9D0-8A1C0C9CC4BD}"),
        interface=IDesktopWallpaper,
    )


def debug_monitor_ids():
    wallpaper = get_desktop_wallpaper_object()
    count = wallpaper.GetMonitorDevicePathCount()
    debug_log(f"Detected {count} monitor(s).")
    for i in range(count):
        monitor_id = wallpaper.GetMonitorDevicePathAt(i)
        rect = wallpaper.GetMonitorRECT(monitor_id)
        debug_log(f"Monitor {i}: {monitor_id} rect={rect}")


def set_wallpapers_per_monitor(bottom_path, top_path, top_monitor_index):
    wallpaper = get_desktop_wallpaper_object()
    count = wallpaper.GetMonitorDevicePathCount()

    if top_monitor_index is None or top_monitor_index < 0 or top_monitor_index >= count:
        debug_log(
            f"Invalid top_monitor.monitor_index={top_monitor_index}; "
            f"expected 0 through {count - 1}. Falling back to single wallpaper."
        )
        set_wallpaper(bottom_path)
        return

    for i in range(count):
        monitor_id = wallpaper.GetMonitorDevicePathAt(i)
        wallpaper.SetWallpaper(monitor_id, top_path if i == top_monitor_index else bottom_path)


def set_wallpaper(path):
    SPI_SETDESKWALLPAPER = 20
    ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, path, 3)
# ~~~~~ END FUNCTIONS ~~~~~


# ~~~~~ MAIN ~~~~~
def main():

    weather_state = get_weather_state(LAT, LON, UNITS)

    if DEBUG and DEBUG_WEATHER_OVERRIDE is not None:
        debug_log(f"Overriding weather with ID {DEBUG_WEATHER_OVERRIDE}")
        weather = DEBUG_WEATHER_OVERRIDE
    else:
        weather = normalize_weather(weather_state["weather"])

    sunrise = datetime.datetime.fromtimestamp(weather_state["sunrise"])
    sunset = datetime.datetime.fromtimestamp(weather_state["sunset"])

    now = datetime.datetime.now()
    if DEBUG_HOUR_OVERRIDE is not None:
        now = now.replace(hour=DEBUG_HOUR_OVERRIDE)
    year = now.year
    month = now.month
    day = now.day
    hour = now.hour

    if DEBUG and DEBUG_SEASON_OVERRIDE is not None:
        debug_log(f"Overriding season for month {month}")
        season = DEBUG_SEASON_OVERRIDE
    else:   
        season = get_season(month)

    # Debug override
    if DEBUG and DEBUG_HOLIDAY_OVERRIDE is not None:
        debug_log(f"Overriding holiday for {day}-{month}-{year}")
        holiday = DEBUG_HOLIDAY_OVERRIDE
    else:
        holiday = get_holiday(day, month, year)

    if DEBUG and DEBUG_TIME_OVERRIDE is not None:
        debug_log(f"Overriding time of day to {DEBUG_TIME_OVERRIDE}")
        bucket = DEBUG_TIME_OVERRIDE
    else:
        bucket = get_time_bucket_by_sun(now, sunrise, sunset)
    star_bucket = get_star_bucket(bucket)
    shade = get_shade_by_bucket(bucket)

    if DEBUG:
        debug_log(f"Now: {now}")
        debug_log(f"Sunrise: {sunrise}")
        debug_log(f"Sunset: {sunset}")
        debug_log(f"Minutes after sunset: {(now - sunset).total_seconds() / 60:.1f}")
        debug_log(f"Bucket: {bucket}")

    current_state = {
        "weather": weather,
        "bucket": bucket,
        "season": season,
        "holiday": holiday,
        "shade": shade
    }

    previous_state = load_state()

    if current_state == previous_state:
        if DEBUG:
            debug_log("No wallpaper update needed.")
        return

    save_state(current_state)

    top_monitor_config = config.get("top_monitor", {})
    top_monitor_enabled = bool(top_monitor_config.get("enabled", False))

    if top_monitor_enabled:
        bottom_output_path = OUTPUT_DIR / "current_wallpaper_bottom.png"
        top_output_path = OUTPUT_DIR / "current_wallpaper_top.png"
        top_overlay_output_path = OUTPUT_DIR / "current_wallpaper_top_overlay.png"

        bottom_layers = get_layer_paths(bucket, star_bucket, season, holiday, weather, shade, "horizontal")
        top_layers = get_layer_paths(bucket, star_bucket, season, holiday, weather, shade, "vertical")

        bottom_wallpaper = compose_wallpaper(bottom_layers, bottom_output_path)
        top_wallpaper = compose_wallpaper(top_layers, top_output_path)

        if top_monitor_config.get("show_weather_overlay", False):
            top_wallpaper = add_weather_overlay(
                top_wallpaper,
                weather_state.get("raw", {}),
                top_overlay_output_path,
            )

        final_wallpaper = bottom_wallpaper
    else:
        output_path = OUTPUT_DIR / "current_wallpaper.png"
        layers = get_layer_paths(bucket, star_bucket, season, holiday, weather, shade, "one_monitor")
        final_wallpaper = compose_wallpaper(layers, output_path)

    if DEBUG:
        debug_log(f"Hour: {hour}")
        debug_log(f"Stars: {star_bucket}")
        debug_log(f"Season: {season}")
        debug_log(f"Holiday: {holiday}")
        debug_log(f"Weather: {weather}")
        debug_log(f"Shade: {shade}")

    if config.get("top_monitor", {}).get("enabled", False):
        if DEBUG:
            try:
                debug_monitor_ids()
            except Exception as e:
                debug_log(f"Could not read monitor IDs: {e}")

        set_wallpapers_per_monitor(
            bottom_path=str(OUTPUT_DIR / "current_wallpaper_bottom.png"),
            top_path=str(OUTPUT_DIR / "current_wallpaper_top_overlay.png" if config.get("top_monitor", {}).get("show_weather_overlay", False) else OUTPUT_DIR / "current_wallpaper_top.png"),
            top_monitor_index=config.get("top_monitor", {}).get("monitor_index"),
        )
    else:
        set_wallpaper(str(final_wallpaper))
# ~~~~~ END MAIN ~~~~~

if __name__ == "__main__":
    main()
