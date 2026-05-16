# ~~~~~ IMPORTS ~~~~~
import ctypes
import datetime
import requests
import os
import json

from pathlib import Path 
from weather_codes import WEATHER_CODES
from image_composer import compose_wallpaper
# ~~~~~ END IMPORTS ~~~~~

# ~~~~~ CONSTANTS ~~~~~
DEBUG = True

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"
STATE_PATH = BASE_DIR / "state.json"

ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR = BASE_DIR / "output"

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

lat = config["lat"]
lon = config["lon"]
# ~~~~~ END CONSTANTS ~~~~~

# ~~~~~ FUNCTIONS ~~~~~
def load_state():
    if not STATE_PATH.exists():
        return {}

    with open(STATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
    
def save_state(state):
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4)

# Map the hour ranges to the time of day
def get_time_bucket(hour):
    if hour in (0, 1, 2):
        return "night"
    if hour in (3, 4, 20, 21, 22, 23):
        return "twilight"
    if hour == 5:
        return "dawn"
    if hour == 6:
        return "sunrise"
    if hour in (7, 8):
        return "early_morning"
    if hour == 9:
        return "mid_morning"
    if hour in (10, 11):
        return "late_morning"
    if hour == 12:
        return "noon"
    if hour in (13, 14):
        return "early_afternoon"    
    if hour == 15:
        return "mid_afternoon"
    if hour in (16, 17):
         return "late_afternoon"
    if hour == 18:
        return "sunset"
    if hour == 19:
        return "dusk"
    return "night"

# Get the shade layer based on the hour
def get_shade(hour):
    if hour in (0, 1, 2):
        return "night"
    if hour in (3, 4, 20, 21, 22, 23):
        return "twilight"
    if hour == 19:
        return "dusk"
    if hour == 18:
        return "sunset"
    return "none"

# Get the season
def get_season(month):
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
def get_weather(api_key, lat, lon):
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        'lat': lat,
        'lon': lon,
        'appid': api_key,
        'units': 'imperial'  #'imperial' for Fahrenheit
    }
    response = requests.get(base_url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()

def set_weather_code(lat, lon):
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        # Missing OPENWEATHER_API_KEY environment variable
        return "unknown"

    try:
        weather_data = get_weather(api_key, lat, lon)

        weather = weather_data["weather"][0]

        weather_id = int(weather["id"])
        description = weather["description"]

        if DEBUG:
            print(f"Weather ID: {weather_id}")
            print(f"Description: {description}")

    except (
        requests.RequestException,
        KeyError,
        IndexError,
        TypeError,
        ValueError
    ) as e:
        print(f"Weather fetch failed: {e}")
        return "unknown"
    
    return WEATHER_CODES.get(weather_id, "unknown")

def normalize_weather(weather):
    return weather if weather != "unknown" else "clear"

def set_wallpaper(path):
    SPI_SETDESKWALLPAPER = 20
    ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, path, 3)
# ~~~~~ END FUNCTIONS ~~~~~

# ~~~~~ MAIN ~~~~~
def main():

    weather = normalize_weather(set_weather_code(lat, lon))
  
    now = datetime.datetime.now()
    year = now.year
    month = now.month
    day = now.day

    season = get_season(month)

    holiday = get_holiday(day, month, year)

    hour = now.hour
    bucket = get_time_bucket(hour)

    shade = get_shade(hour)

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
            print("No wallpaper update needed.")
        return

    save_state(current_state)

    sky_path = ASSETS_DIR / "sky" / f"{bucket}.png"
    #sky_path = ASSETS_DIR / "sky" / "night.png"
    season_path = ASSETS_DIR / "seasons" / f"{season}.png"
    shade_path = ASSETS_DIR / "shade" / f"{shade}.png" if shade != "none" else None
    #shade_path = ASSETS_DIR / "shade" / "night.png"
    #holiday_path = ASSETS_DIR / "holidays" / "christmas_day.png"
    holiday_path = ASSETS_DIR / "holidays" / f"{holiday}.png" if holiday != "none" else None
    #weather_path = ASSETS_DIR / "weather" / "light_rain.png"
    weather_path = ASSETS_DIR / "weather" / f"{weather}.png"

    output_path = OUTPUT_DIR / "current_wallpaper.png"

    final_wallpaper = compose_wallpaper(
        [sky_path, season_path, holiday_path, weather_path, shade_path],
        output_path
    )

    if DEBUG:
        print(f"Hour: {hour}")
        print(f"Bucket: {bucket}")
        print(f"Season: {season}")
        print(f"Holiday: {holiday}")
        print(f"Weather: {weather}")
        print(f"Shade: {shade}")
        #print(f"Wallpaper: {str(final_wallpaper)}")

    set_wallpaper(str(final_wallpaper))
# ~~~~~ END MAIN ~~~~~

if __name__ == "__main__":
    main()
