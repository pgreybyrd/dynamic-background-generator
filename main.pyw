# ~~~~~ IMPORTS ~~~~~
import datetime
from multiprocessing.util import debug
import json

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
from wallpaper.time_buckets import get_moon_bucket, get_time_bucket_by_sun, get_shade_by_bucket, get_star_bucket
from wallpaper.moon import get_moon_global_position
from wallpaper.image_composer import add_floating_image
from wallpaper.seasons import get_season
from wallpaper.holidays import get_holiday
from wallpaper.weather import get_weather_state, normalize_weather
from wallpaper.overlay import add_weather_overlay
from wallpaper.assets import get_layer_paths
from wallpaper.monitors import set_wallpaper, set_wallpapers_per_monitor, debug_monitor_ids


def layer_fingerprint(layer_paths):
    """Serializable fingerprint of the actual artwork inputs for one monitor group."""
    return [str(path) for path in layer_paths]


def weather_overlay_fingerprint(weather_data):
    """Match exactly what add_weather_overlay() currently renders."""
    temp = weather_data.get("main", {}).get("temp")
    description = weather_data.get("weather", [{}])[0].get("description", "").title()

    return {
        "temp": round(temp) if temp is not None else None,
        "description": description,
    }


def next_output_slot(previous_slot):
    return "b" if previous_slot == "a" else "a"
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
    if DEBUG and DEBUG_HOUR_OVERRIDE is not None:
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
    moon_bucket = get_moon_bucket(bucket)
    shade = get_shade_by_bucket(bucket)

    if DEBUG:
        debug_log(f"Now: {now}")
        debug_log(f"Sunrise: {sunrise}")
        debug_log(f"Sunset: {sunset}")
        debug_log(f"Minutes after sunrise: {(now - sunrise).total_seconds() / 60:.1f}")
        debug_log(f"Minutes after sunset: {(now - sunset).total_seconds() / 60:.1f}")
        debug_log(f"Bucket: {bucket}")

    previous_state = load_state()

    top_monitor_config = config.get("top_monitor", {})
    top_monitor_enabled = bool(top_monitor_config.get("enabled", False))

    if top_monitor_enabled:
        # Resolve the actual layers first. This lets horizontal and vertical
        # artwork change independently even when the semantic weather/time state changes.
        bottom_layers = get_layer_paths(
            bucket, star_bucket, moon_bucket, season, holiday, weather, shade,
            ASSETS_DIR, "horizontal"
        )
        top_layers = get_layer_paths(
            bucket, star_bucket, moon_bucket, season, holiday, weather, shade,
            ASSETS_DIR, "vertical"
        )

        bottom_visual_state = {
            "layers": layer_fingerprint(bottom_layers),
        }

        top_visual_state = {
            "layers": layer_fingerprint(top_layers),
        }

        if top_monitor_config.get("show_weather_overlay", False):
            top_visual_state["weather_overlay"] = weather_overlay_fingerprint(
                weather_state.get("raw", {})
            )

        previous_bottom_visual_state = previous_state.get("_bottom_visual_state")
        previous_top_visual_state = previous_state.get("_top_visual_state")

        previous_legacy_slot = previous_state.get("_output_slot")
        previous_bottom_slot = previous_state.get("_bottom_output_slot", previous_legacy_slot)
        previous_top_slot = previous_state.get("_top_output_slot", previous_legacy_slot)

        bottom_initialized = previous_bottom_slot in ("a", "b")
        top_initialized = previous_top_slot in ("a", "b")

        bottom_changed = (
            bottom_visual_state != previous_bottom_visual_state
            or not bottom_initialized
        )
        top_changed = (
            top_visual_state != previous_top_visual_state
            or not top_initialized
        )

        if not bottom_changed and not top_changed:
            if DEBUG:
                debug_log("No wallpaper update needed.")
            return

        bottom_wallpaper = None
        top_wallpaper = None

        bottom_slot = previous_bottom_slot
        top_slot = previous_top_slot

        if bottom_changed:
            bottom_slot = next_output_slot(previous_bottom_slot)
            bottom_output_path = OUTPUT_DIR / f"current_wallpaper_bottom_{bottom_slot}.png"
            bottom_wallpaper = compose_wallpaper(bottom_layers, bottom_output_path)

        if top_changed:
            top_slot = next_output_slot(previous_top_slot)
            top_output_path = OUTPUT_DIR / f"current_wallpaper_top_{top_slot}.png"
            top_overlay_output_path = OUTPUT_DIR / f"current_wallpaper_top_overlay_{top_slot}.png"

            top_wallpaper = compose_wallpaper(top_layers, top_output_path)

            if top_monitor_config.get("show_weather_overlay", False):
                top_wallpaper = add_weather_overlay(
                    top_wallpaper,
                    weather_state.get("raw", {}),
                    top_overlay_output_path,
                )

        if DEBUG:
            debug_log(
                f"Wallpaper groups changed: horizontal={bottom_changed}, "
                f"vertical={top_changed}"
            )
            try:
                debug_monitor_ids()
            except Exception as e:
                debug_log(f"Could not read monitor IDs: {e}")

        set_wallpapers_per_monitor(
            bottom_path=str(bottom_wallpaper) if bottom_wallpaper is not None else None,
            top_path=str(top_wallpaper) if top_wallpaper is not None else None,
            top_monitor_index=top_monitor_config.get("monitor_index"),
            update_bottom=bottom_changed,
            update_top=top_changed,
        )

        # Only record a group's new fingerprint/slot after composition + Windows
        # switching completed successfully. If anything fails, the next run retries.
        new_state = dict(previous_state)
        new_state["_bottom_visual_state"] = bottom_visual_state
        new_state["_top_visual_state"] = top_visual_state
        new_state["_bottom_output_slot"] = bottom_slot
        new_state["_top_output_slot"] = top_slot

        # Remove Pass-1 metadata after migration so one shared slot cannot
        # accidentally become authoritative again.
        new_state.pop("_output_slot", None)

        save_state(new_state)

    else:
        # Single-monitor mode keeps the same optimization, using the resolved
        # layer list as the visual fingerprint.
        layers = get_layer_paths(
            bucket, star_bucket, moon_bucket, season, holiday, weather, shade,
            ASSETS_DIR, "one_monitor"
        )
        visual_state = {"layers": layer_fingerprint(layers)}

        previous_visual_state = previous_state.get("_single_visual_state")
        previous_slot = previous_state.get(
            "_single_output_slot",
            previous_state.get("_output_slot")
        )
        initialized = previous_slot in ("a", "b")

        if visual_state == previous_visual_state and initialized:
            if DEBUG:
                debug_log("No wallpaper update needed.")
            return

        output_slot = next_output_slot(previous_slot)
        output_path = OUTPUT_DIR / f"current_wallpaper_{output_slot}.png"
        final_wallpaper = compose_wallpaper(layers, output_path)

        set_wallpaper(str(final_wallpaper))

        new_state = dict(previous_state)
        new_state["_single_visual_state"] = visual_state
        new_state["_single_output_slot"] = output_slot
        new_state.pop("_output_slot", None)
        save_state(new_state)

    if DEBUG:
        debug_log(f"Hour: {hour}")
        debug_log(f"Stars: {star_bucket}")
        debug_log(f"Moon: {moon_bucket}")
        debug_log(f"Season: {season}")
        debug_log(f"Holiday: {holiday}")
        debug_log(f"Weather: {weather}")
        debug_log(f"Shade: {shade}")
# ~~~~~ END MAIN ~~~~~

if __name__ == "__main__":
    main()
