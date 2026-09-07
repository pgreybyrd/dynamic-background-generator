# ~~~~~ IMPORTS ~~~~~
import datetime
import json

from pathlib import Path 
# ~~~~~ END IMPORTS ~~~~~


# ~~~~~ CONSTANTS ~~~~~
# Keep paths relative to the script so this still works when Task Scheduler
# decides it lives somewhere else.
BASE_DIR = Path(__file__).resolve().parent

CONFIG_PATH = BASE_DIR / "config.json"
STATE_PATH = BASE_DIR / "state.json"
LOG_PATH = BASE_DIR / "debug_log.txt"

ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR = BASE_DIR / "output"

# Debug overrides let me force specific visual conditions without waiting for
# Spokane to conveniently provide midnight, snow, Halloween, etc.
#
# These only do anything when config["debug"] is true.
DEBUG_HOUR_OVERRIDE = None # int from 0-23, or None to disable 
DEBUG_TIME_OVERRIDE = None # time of day like 'dawn', 'noon', 'dusk', etc., or None to disable
DEBUG_WEATHER_OVERRIDE = None # weather code like 'clear', 'rain', 'snow', etc., or None to disable
DEBUG_SEASON_OVERRIDE = None # 'early_spring', 'mid_summer', 'late_autumn', 'mid_winter', etc., or None to disable
DEBUG_HOLIDAY_OVERRIDE = None # 'valentines', 'halloween', 'thanksgiving', 'christmas_eve', 'christmas_day', etc., or None to disable
DEBUG_BANNER_OVERRIDE = None # 'autumn_equinox', 'happy_birthday','happy_halloween', etc., or None to disable

# Configuration is intentionally outside the Python code so location,
# monitor layout, update interval, etc. can change without touching the
# wallpaper engine itself.
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

DEBUG = config.get("debug", False)

LAT = config["lat"]
LON = config["lon"]
UNITS = config["units"]  
# ~~~~~ END CONSTANTS ~~~~~


# ~~~~~ FUNCTIONS ~~~~~
# Keep debug configuration centralized here so the rest of the project can
# just call debug_log() without repeatedly passing the same paths/settings.
from wallpaper.logging import debug_log as _debug_log
def debug_log(message):
    _debug_log(message, debug=DEBUG, log_path=LOG_PATH)

# Same idea for state: main owns where the state file lives while state.py
# owns the actual serialization.
from wallpaper.state import load_state as _load_state, save_state as _save_state
def load_state():
    return _load_state(STATE_PATH)
def save_state(state):
    _save_state(state, STATE_PATH)  

from wallpaper.image_composer import compose_wallpaper, add_top_centered_image, split_panorama, add_floating_image
from wallpaper.time_buckets import get_moon_bucket, get_time_bucket_by_sun, get_shade_by_bucket, get_star_bucket
from wallpaper.moon import get_moon_global_position
from wallpaper.seasons import get_season, get_astronomical_event
from wallpaper.holidays import get_holiday, get_banner
from wallpaper.weather import get_weather_state
from wallpaper.overlay import add_weather_overlay
from wallpaper.assets import get_layer_paths
from wallpaper.monitors import set_wallpaper, set_wallpapers_per_monitor, debug_monitor_ids


def layer_fingerprint(layer_paths):
    # Reduce the resolved artwork for one monitor group to something cheap
    # and serializable that I can compare on the next run.
    return [str(path) for path in layer_paths]


def weather_overlay_fingerprint(weather_data):
    # Track only weather values that actually appear in the top-monitor overlay.
    temp = weather_data.get("main", {}).get("temp")
    description = weather_data.get("weather", [{}])[0].get("description", "").title()

    # Match the formatting in add_weather_overlay(), including rounding the
    # temperature. A change from 71.1 to 71.4 should not trigger an update if
    # both are still displayed as 71°.
    return {
        "temp": round(temp) if temp is not None else None,
        "description": description,
    }


def next_output_slot(previous_slot):
    # Alternate between A/B output files.
    # Windows may still be displaying the current wallpaper file, so I do not
    # overwrite it underneath Explorer. The new image is composed into the
    # inactive file first and Windows is switched to it afterward.
    return "b" if previous_slot == "a" else "a"
# ~~~~~ END FUNCTIONS ~~~~~


# ~~~~~ MAIN ~~~~~
def main():

    # Weather is fetched once per run and then reused for both artwork
    # selection and the optional top-monitor weather overlay.
    weather_state = get_weather_state(LAT, LON, UNITS)

    if DEBUG and DEBUG_WEATHER_OVERRIDE is not None:
        debug_log(f"Overriding weather with {DEBUG_WEATHER_OVERRIDE}")
        weather = DEBUG_WEATHER_OVERRIDE
    else:
        weather = weather_state["weather"]

    # Use the real sunrise/sunset so "dawn" actually moves with the seasons.
    sunrise = weather_state["sunrise"]
    sunset = weather_state["sunset"]

    now = datetime.datetime.now()
    if DEBUG and DEBUG_HOUR_OVERRIDE is not None:
        now = now.replace(hour=DEBUG_HOUR_OVERRIDE)
    year = now.year
    month = now.month
    day = now.day
    hour = now.hour

    astronomical_event = get_astronomical_event(now)

    if DEBUG and DEBUG_SEASON_OVERRIDE is not None:
        debug_log(f"Overriding season with {DEBUG_SEASON_OVERRIDE}")
        season = DEBUG_SEASON_OVERRIDE
    else:
        season = get_season(now)

    if DEBUG and DEBUG_HOLIDAY_OVERRIDE is not None:
        debug_log(f"Overriding holiday with {DEBUG_HOLIDAY_OVERRIDE}")
        holiday = DEBUG_HOLIDAY_OVERRIDE
    else:
        holiday = get_holiday(day, month, year)

    banner = get_banner(holiday, astronomical_event)

    if DEBUG and DEBUG_BANNER_OVERRIDE is not None:
        debug_log(f"Overriding banner with {DEBUG_BANNER_OVERRIDE}")
        banner = DEBUG_BANNER_OVERRIDE

    debug_log(f"Season: {season}")
    debug_log(f"Holiday: {holiday}")
    debug_log(f"Astronomical event: {astronomical_event}")
    debug_log(f"Banner: {banner}")

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

    # Remember what is already on the desktop so most runs can do absolutely nothing.
    previous_state = load_state()

    top_monitor_config = config.get("top_monitor", {})
    top_monitor_enabled = bool(top_monitor_config.get("enabled", False))

    if top_monitor_enabled:

        bottom_config = config.get("bottom_monitors", {})
        bottom_mode = bottom_config.get("mode", "shared")
        bottom_monitor_indices = bottom_config.get("monitor_indices")
        bottom_monitor_widths = bottom_config.get("monitor_widths", [])

        if bottom_mode == "panorama":
            if not bottom_monitor_indices:
                raise ValueError(
                    "Panorama mode requires bottom_monitors.monitor_indices."
                )

            if not bottom_monitor_widths:
                raise ValueError(
                    "Panorama mode requires bottom_monitors.monitor_widths."
                )

            if len(bottom_monitor_indices) != len(bottom_monitor_widths):
                raise ValueError(
                    "bottom_monitors.monitor_indices and monitor_widths "
                    "must contain the same number of entries."
                )

        bottom_layout = "panorama" if bottom_mode == "panorama" else "horizontal"

        bottom_assets = get_layer_paths(
            bucket,
            star_bucket,
            moon_bucket,
            season,
            holiday,
            weather,
            shade,
            banner,
            ASSETS_DIR,
            bottom_layout,
        )

        bottom_layers = bottom_assets["layers"]
        bottom_banner = bottom_assets["banner"]
        
        top_assets = get_layer_paths(
            bucket, star_bucket, moon_bucket, season, holiday, weather, shade,
            banner, ASSETS_DIR, "vertical"
        )

        top_layers = top_assets["layers"]
        top_banner = top_assets["banner"]

        # Each monitor group gets its own fingerprint now.
        bottom_visual_state = {
            "layers": layer_fingerprint(bottom_layers),
            "banner": str(bottom_banner) if bottom_banner else None,
            "mode": bottom_mode,
            "monitor_indices": bottom_monitor_indices,
            "monitor_widths": bottom_monitor_widths,
        }

        top_visual_state = {
            "layers": layer_fingerprint(top_layers),
            "banner": str(top_banner) if top_banner else None,
        }

        if top_monitor_config.get("show_weather_overlay", False):
            top_visual_state["weather_overlay"] = weather_overlay_fingerprint(
                weather_state.get("raw", {})
            )

        previous_bottom_visual_state = previous_state.get("_bottom_visual_state")
        previous_top_visual_state = previous_state.get("_top_visual_state")

        # Fall back to the old shared slot so Pass 1 state migrates cleanly.
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

        # Nothing changed! Leave Windows alone.
        if not bottom_changed and not top_changed:
            if DEBUG:
                debug_log("No wallpaper update needed.")
            return

        bottom_wallpaper = None
        top_wallpaper = None
        panorama_paths = None

        bottom_slot = previous_bottom_slot
        top_slot = previous_top_slot

        # Only rebuild the monitor group that actually changed.
        if bottom_changed:
            bottom_slot = next_output_slot(previous_bottom_slot)
            bottom_output_path = OUTPUT_DIR / f"current_wallpaper_bottom_{bottom_slot}.png"
            bottom_wallpaper = compose_wallpaper(bottom_layers, bottom_output_path)

            if bottom_banner:
                bottom_wallpaper = add_top_centered_image(
                    bottom_wallpaper,
                    bottom_banner,
                    bottom_output_path,
                )

            if bottom_mode == "panorama":
                panorama_paths = split_panorama(
                    bottom_wallpaper,
                    OUTPUT_DIR,
                    bottom_slot,
                    bottom_monitor_widths,
                )

        if top_changed:
            top_slot = next_output_slot(previous_top_slot)
            top_output_path = OUTPUT_DIR / f"current_wallpaper_top_{top_slot}.png"
            top_overlay_output_path = OUTPUT_DIR / f"current_wallpaper_top_overlay_{top_slot}.png"

            top_wallpaper = compose_wallpaper(top_layers, top_output_path)
            if top_banner:
                top_wallpaper = add_top_centered_image(
                    top_wallpaper,
                    top_banner,
                    top_output_path
                )

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
            bottom_mode=bottom_mode,
            bottom_monitor_indices=bottom_monitor_indices,
            panorama_paths=panorama_paths,
            update_bottom=bottom_changed,
            update_top=top_changed,
        )

        # Don't save the new state until composition + the Windows switch succeed.
        # If something explodes, the next run can retry.
        new_state = dict(previous_state)
        new_state["_bottom_visual_state"] = bottom_visual_state
        new_state["_top_visual_state"] = top_visual_state
        new_state["_bottom_output_slot"] = bottom_slot
        new_state["_top_output_slot"] = top_slot

        # Pass 1's shared slot can go away once migrated.
        new_state.pop("_output_slot", None)

        save_state(new_state)

    else:
        # Single-monitor mode gets the same fingerprint + double-buffer optimization.
        assets = get_layer_paths(
            bucket, star_bucket, moon_bucket, season, holiday, weather, shade,
            banner, ASSETS_DIR, "horizontal"
        )

        layers = assets["layers"]
        single_banner = assets["banner"]
        
        visual_state = {
            "layers": layer_fingerprint(layers),
            "banner": str(single_banner) if single_banner else None,
        }

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

        if single_banner:
            final_wallpaper = add_top_centered_image(
                final_wallpaper,
                single_banner,
                output_path,
            )

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
