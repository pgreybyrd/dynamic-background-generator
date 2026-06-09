# ~~~~~ IMPORTS ~~~~~
import ctypes
import datetime
import requests
import os
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
from weather_codes import WEATHER_CODES
from image_composer import compose_wallpaper
# ~~~~~ END IMPORTS ~~~~~

# ~~~~~ CONSTANTS ~~~~~
DEBUG = True 
DEBUG_HOUR_OVERRIDE = None # int from 0-23, or None to disable 
DEBUG_TIME_OVERRIDE = None # time of day like 'dawn', 'noon', 'dusk', etc., or None to disable
DEBUG_WEATHER_OVERRIDE = None # weather code like 'clear', 'rain', 'snow', etc., or None to disable
DEBUG_SEASON_OVERRIDE = None # 'spring', 'summer', 'autumn', 'winter', or None to disable
DEBUG_HOLIDAY_OVERRIDE = None # 'valentines', 'halloween', 'thanksgiving', 'christmas_eve', 'christmas_day', etc., or None to disable

BASE_DIR = Path(__file__).resolve().parent

CONFIG_PATH = BASE_DIR / "config.json"
STATE_PATH = BASE_DIR / "state.json"
LOG_PATH = BASE_DIR / "debug_log.txt"

ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR = BASE_DIR / "output"

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

LAT = config["lat"]
LON = config["lon"]

UNITS = config["units"]  
# ~~~~~ END CONSTANTS ~~~~~

# ~~~~~ FUNCTIONS ~~~~~
def debug_log(message):
    if DEBUG:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
        print(message)
        
def load_state():
    if not STATE_PATH.exists():
        return {}

    with open(STATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
    
def save_state(state):
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4)

# # Map the time of day to sunrise/sunset anchored sky buckets.
# # The bucket names here must match PNG filenames in assets/sky.
# def get_time_bucket_by_sun(now, sunrise, sunset):
#     if DEBUG and DEBUG_TIME_OVERRIDE is not None:
#         debug_log(f"Overriding time of day to {DEBUG_TIME_OVERRIDE}")
#         return DEBUG_TIME_OVERRIDE

#     # Morning is anchored to today's sunrise.
#     # These are intentionally short/soft so the sky eases into daylight.
#     morning_schedule = [
#         (sunrise - datetime.timedelta(hours=5), "midnight"),
#         (sunrise - datetime.timedelta(hours=3), "night"),
#         (sunrise - datetime.timedelta(hours=2), "deep_twilight"),
#         (sunrise - datetime.timedelta(minutes=90), "pre_dawn"),
#         (sunrise - datetime.timedelta(minutes=45), "dawn"),
#         (sunrise + datetime.timedelta(minutes=45), "sunrise"),
#     ]

#     for end_time, bucket in morning_schedule:
#         if now < end_time:
#             return bucket

#     # Evening is anchored to today's sunset.
#     # The goal: keep late afternoon / early evening blue for longer,
#     # then let the dramatic colors happen near sunset.
#     evening_schedule = [
#         (sunset - datetime.timedelta(hours=3), "DAYLIGHT"),
#         (sunset - datetime.timedelta(hours=2), "early_evening"),
#         (sunset - datetime.timedelta(hours=1), "golden_hour"),
#         (sunset - datetime.timedelta(minutes=20), "sunset_start"),
#         (sunset + datetime.timedelta(minutes=15), "sunset_peak"),
#         (sunset + datetime.timedelta(minutes=35), "afterglow"),
#         (sunset + datetime.timedelta(minutes=60), "dusk"),
#         (sunset + datetime.timedelta(minutes=90), "deep_dusk"),
#         (sunset + datetime.timedelta(minutes=125), "twilight"),
#         (sunset + datetime.timedelta(minutes=160), "deep_twilight"),
#     ]

#     if now < evening_schedule[0][0]:
#         daylight_start = sunrise + datetime.timedelta(minutes=45)
#         daylight_end = sunset - datetime.timedelta(hours=3)

#         daytime_buckets = [
#             "early_morning",
#             "mid_morning",
#             "late_morning",
#             "noon",
#             "early_afternoon",
#             "mid_afternoon",
#             "late_afternoon",
#         ]

#         total_seconds = max(1, (daylight_end - daylight_start).total_seconds())
#         elapsed_seconds = (now - daylight_start).total_seconds()

#         index = int((elapsed_seconds / total_seconds) * len(daytime_buckets))
#         index = max(0, min(index, len(daytime_buckets) - 1))

#         return daytime_buckets[index]

#     for end_time, bucket in evening_schedule[1:]:
#         if now < end_time:
#             return bucket

#     return "night"

def get_time_bucket_by_sun(now, sunrise, sunset):
    if DEBUG and DEBUG_TIME_OVERRIDE is not None:
        debug_log(f"Overriding time of day to {DEBUG_TIME_OVERRIDE}")
        return DEBUG_TIME_OVERRIDE

    minutes_from_sunrise = int((now - sunrise).total_seconds() / 60)
    minutes_from_sunset = int((now - sunset).total_seconds() / 60)

    sunrise_buckets = [
        (-60, "sunrise_-60"),
        (-45, "sunrise_-45"),
        (-30, "sunrise_-30"),
        (-15, "sunrise_-15"),
        (0, "sunrise_0"),
        (15, "sunrise_15"),
        (30, "sunrise_30"),
        (45, "sunrise_45"),
    ]

    sunset_buckets = [
        (-90, "golden_early"),
        (-60, "sunset_-60"),
        (-45, "sunset_-45"),
        (-30, "sunset_-30"),
        (-15, "sunset_-15"),
        (0, "sunset_0"),
        (15, "sunset_15"),
        (30, "sunset_30"),
        (45, "sunset_45"),
        (60, "sunset_60"),
        (90, "blue_hour"),
        (120, "dusk"),
        (150, "deep_twilight"),
    ]

    # Sunrise window: 60 min before to 45 min after
    if -60 <= minutes_from_sunrise < 60:
        return closest_bucket(minutes_from_sunrise, sunrise_buckets)

    # Sunset window: 90 min before to 150 min after
    if -90 <= minutes_from_sunset < 150:
        return closest_bucket(minutes_from_sunset, sunset_buckets)

    # Before sunrise
    if now < sunrise:
        if minutes_from_sunrise < -180:
            return "deep_night"
        if minutes_from_sunrise < -120:
            return "night"
        return "pre_dawn"

    # After sunrise, before sunset
    daylight_start = sunrise + datetime.timedelta(minutes=60)
    daylight_end = sunset - datetime.timedelta(minutes=90)

    if daylight_start <= now < daylight_end:
        daytime_buckets = [
            "early_morning",
            "mid_morning",
            "late_morning",
            "noon",
            "early_afternoon",
            "mid_afternoon",
            "late_afternoon",
        ]

        total_seconds = max(1, (daylight_end - daylight_start).total_seconds())
        elapsed_seconds = (now - daylight_start).total_seconds()

        index = int((elapsed_seconds / total_seconds) * len(daytime_buckets))
        index = max(0, min(index, len(daytime_buckets) - 1))

        return daytime_buckets[index]

    return "night"


def closest_bucket(minutes, schedule):
    closest = min(schedule, key=lambda item: abs(minutes - item[0]))
    return closest[1]

# Get the shade layer based on the sky bucket.
# This assumes shade PNG filenames match these bucket names.
# If you do not have a matching shade file yet, map that bucket to the closest existing one.
def get_shade_by_bucket(bucket):
    shade_by_bucket = {
        "sunset_start": "sunset",
        "sunset_peak": "sunset",
        "afterglow": "dusk",
        "dusk": "dusk",
        "deep_dusk": "twilight",
        "twilight": "twilight",
        "deep_twilight": "night",
        "night": "night",
        "midnight": "night",
        "pre_dawn": "twilight",
        "dawn": "dusk",
        "sunrise": "sunset",
    }

    return shade_by_bucket.get(bucket, "none")

# Get the season
def get_season(month):
    if DEBUG and DEBUG_SEASON_OVERRIDE is not None:
        return DEBUG_SEASON_OVERRIDE
    if month in (3, 4, 5):
        return "spring"
    if month in (6, 7, 8):
        return "summer"
    if month in (9, 10, 11):
        return "autumn"
    return "winter"

# Calculate the holidays that aren't on a set date each year
def calculate_easter(year):
    # Anonymous Gregorian algorithm (Computus)
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return datetime.date(year, month, day)

def second_sunday_of_may(year):
    # Start with the first day of May
    first_of_may = datetime.date(year, 5, 1)
    
    # Find the day of the week for May 1st (0 is Monday, 6 is Sunday)
    day_of_week = first_of_may.weekday()
    
    # Calculate how many days to add to get to the first Sunday
    days_until_first_sunday = (6 - day_of_week) % 7
    
    # Calculate the date of the first Sunday
    first_sunday = first_of_may + datetime.timedelta(days=days_until_first_sunday)
    
    # The second Sunday will be exactly one week after the first Sunday
    second_sunday = first_sunday + datetime.timedelta(days=7)
    
    # Return just the day of the month
    return second_sunday.day

def third_sunday_of_june(year):
    # Start with the first day of May
    first_of_june = datetime.date(year, 6, 1)
    
    # Find the day of the week for May 1st (0 is Monday, 6 is Sunday)
    day_of_week = first_of_june.weekday()
    
    # Calculate how many days to add to get to the first Sunday
    days_until_first_sunday = (6 - day_of_week) % 7
    
    # Calculate the date of the first Sunday
    first_sunday = first_of_june + datetime.timedelta(days=days_until_first_sunday)
    
    # The second Sunday will be exactly one week after the first Sunday
    third_sunday = first_sunday + datetime.timedelta(days=14)
    
    # Return just the day of the month
    return third_sunday.day

def fourth_thursday_of_november(year):
    # Start with the first day of November
    first_of_november = datetime.date(year, 11, 1)
    
    # Find the day of the week for November 1st (0 is Monday, 6 is Sunday)
    day_of_week = first_of_november.weekday()
    
    # Calculate how many days to add to get to the first Thursday
    # If November 1st is a Thursday (day_of_week == 3), we need to add 0 days, otherwise,
    # we add the necessary days to reach the upcoming Thursday
    days_until_first_thursday = (3 - day_of_week) % 7
    
    # Calculate the date of the first Thursday
    first_thursday = first_of_november + datetime.timedelta(days=days_until_first_thursday)
    
    # The fourth Thursday will be exactly three weeks after the first Thursday
    fourth_thursday = first_thursday + datetime.timedelta(days=21)
    
    # Return just the day of the month
    return fourth_thursday.day

def get_holiday(day, month, year):
    # Debug override
    if DEBUG and DEBUG_HOLIDAY_OVERRIDE:
        debug_log(f"Overriding holiday for {day}-{month}-{year}")
        return DEBUG_HOLIDAY_OVERRIDE
    # Easter
    easter_date = calculate_easter(year)
    if month == easter_date.month and day == easter_date.day:
        return 'easter'       
    # January
    if month == 1:
        # New Year's Day
        if day == 1:
            return 'new_years_day'
    # February
    if month == 2:
        # Valentine's Day
        if day == 14:
            return 'valentines'
    # March
    if month == 3:
        # St. Patrick's Day
        if day == 17:
            return 'st_patricks_day'
    # April
    if month == 4:
        # April Fool's Day
        if day == 1:
            return 'april_fools'
    # May
    if month == 5:
        # 2nd Sunday (Mother's Day)
        if day == second_sunday_of_may(year):
            return 'mothers_day'
        # Cinco de Mayo
        if day == 5:
            return 'cinco_de_mayo'        
    # June
    if month == 6:
        # 3rd Sunday (Father's Day)
        if day == third_sunday_of_june(year):
            return 'fathers_day'  
        # Juneteenth
        if day == 19:
            return 'juneteenth'   
    # July
    if month == 7:
        # Fourth of July (Independence Day)
        if day == 4:
            return 'fourth_of_july'
    # August
    # September
    # October
    if month == 10:
        if day == 31:
            return 'halloween'
    # November
    if month == 11:
        # Dia de los Muertos
        if day == 1:
            return 'dia_de_los_muertos'
        # Thanksgiving
        if day == fourth_thursday_of_november(year):
            return 'thanksgiving'
    # December
    if month == 12:
        if day == 24:
            return 'christmas_eve'
        if day == 25:
            return 'christmas_day'
        if day == 31:
            return 'new_years_eve'   
    return 'none'

# Weather layer
def get_weather(api_key):
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        'lat': LAT,
        'lon': LON,
        'appid': api_key,
        'units': UNITS
    }
    if DEBUG:
        debug_log(f"Fetching weather data for lat = {LAT}, lon = {LON}")

    response = requests.get(base_url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()

def set_weather_code():
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        # Missing OPENWEATHER_API_KEY environment variable
        now_ts = int(datetime.datetime.now().timestamp())
        return {
            "weather": "unknown",
            "sunrise": now_ts + 6 * 3600,
            "sunset": now_ts + 18 * 3600,
            "raw": {},
        }

    try:
        weather_data = get_weather(api_key)

        weather = weather_data["weather"][0]

        weather_id = int(weather["id"])
        description = weather["description"]

        if DEBUG:
            debug_log(f"Weather ID: {weather_id}")
            debug_log(f"Description: {description}")

    except (
        requests.RequestException,
        KeyError,
        IndexError,
        TypeError,
        ValueError
    ) as e:
        debug_log(f"Weather fetch failed: {e}")
        return "unknown"
    
    return {
        "weather": WEATHER_CODES.get(weather_id, "unknown"),
        "sunrise": weather_data["sys"]["sunrise"],
        "sunset": weather_data["sys"]["sunset"],
        "raw": weather_data,
    }

def normalize_weather(weather):
    if DEBUG and DEBUG_WEATHER_OVERRIDE is not None:
        debug_log(f"Overriding weather with ID {DEBUG_WEATHER_OVERRIDE}")
        weather = DEBUG_WEATHER_OVERRIDE
    return weather if weather != "unknown" else "clear"

def get_star_bucket(bucket):
    """Return the star overlay filename stem for the current sky bucket."""
    star_by_bucket = {
        "deep_night": "stars_100",
        "night": "stars_100",

        "deep_twilight": "stars_75",
        "dusk": "stars_50",
        "pre_dawn": "stars_50",

        "sunrise_-60": "stars_50",
        "sunrise_-45": "stars_25",
        "sunrise_-30": "stars_10",
        "sunrise_-15": "stars_0",
        "sunrise_0": "stars_0",
        "sunrise_15": "stars_0",
        "sunrise_30": "stars_0",
        "sunrise_45": "stars_0",

        "early_morning": "stars_0",
        "mid_morning": "stars_0",
        "late_morning": "stars_0",
        "noon": "stars_0",
        "early_afternoon": "stars_0",
        "mid_afternoon": "stars_0",
        "late_afternoon": "stars_0",
        "golden_early": "stars_0",

        "sunset_-60": "stars_0",
        "sunset_-45": "stars_0",
        "sunset_-30": "stars_0",
        "sunset_-15": "stars_0",
        "sunset_0": "stars_0",
        "sunset_15": "stars_10",
        "sunset_30": "stars_25",
        "sunset_45": "stars_50",
        "sunset_60": "stars_75",
        "blue_hour": "stars_75",
    }
    return star_by_bucket.get(bucket, "stars_0")


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
        season_path = ASSETS_DIR / "seasons" / layout / f"{season}.png"
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

def add_weather_overlay(image_path, weather_data, output_path):
    """Simple top-monitor text overlay. Safe no-op if Pillow is unavailable."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        debug_log("Pillow not installed; skipping weather overlay.")
        return image_path

    img = Image.open(image_path).convert("RGBA")
    draw = ImageDraw.Draw(img)

    temp = weather_data.get("main", {}).get("temp")
    description = weather_data.get("weather", [{}])[0].get("description", "").title()

    lines = []
    if temp is not None:
        lines.append(f"{round(temp)}°")
    if description:
        lines.append(description)

    if not lines:
        return image_path

    try:
        font_big = ImageFont.truetype("arial.ttf", 84)
        font_small = ImageFont.truetype("arial.ttf", 38)
    except Exception:
        font_big = ImageFont.load_default()
        font_small = ImageFont.load_default()

    x = 60
    y = 80
    padding = 26
    box_w = 420
    box_h = 170
    draw.rounded_rectangle(
        [x - padding, y - padding, x + box_w, y + box_h],
        radius=28,
        fill=(0, 0, 0, 90),
    )
    draw.text((x, y), lines[0], font=font_big, fill=(255, 255, 255, 235))
    if len(lines) > 1:
        draw.text((x + 6, y + 95), lines[1], font=font_small, fill=(255, 255, 255, 220))

    img.save(output_path)
    return output_path


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

    weather_info = set_weather_code()

    weather = normalize_weather(weather_info["weather"])

    sunrise = datetime.datetime.fromtimestamp(weather_info["sunrise"])
    sunset = datetime.datetime.fromtimestamp(weather_info["sunset"])
  
    now = datetime.datetime.now()
    if DEBUG_HOUR_OVERRIDE is not None:
        now = now.replace(hour=DEBUG_HOUR_OVERRIDE)
    year = now.year
    month = now.month
    day = now.day

    season = get_season(month)

    holiday = get_holiday(day, month, year)

    hour = now.hour

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
                weather_info.get("raw", {}),
                top_overlay_output_path,
            )

        final_wallpaper = bottom_wallpaper
    else:
        output_path = OUTPUT_DIR / "current_wallpaper.png"
        layers = get_layer_paths(bucket, star_bucket, season, holiday, weather, shade, "one_monitor")
        final_wallpaper = compose_wallpaper(layers, output_path)

    if DEBUG:
        debug_log(f"Hour: {hour}")
        #debug_log(f"Bucket: {bucket}")
        debug_log(f"Stars: {star_bucket}")
        debug_log(f"Season: {season}")
        debug_log(f"Holiday: {holiday}")
        debug_log(f"Weather: {weather}")
        debug_log(f"Shade: {shade}")
        #debug_log(f"Wallpaper: {str(final_wallpaper)}")

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
