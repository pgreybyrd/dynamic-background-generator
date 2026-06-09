import datetime

def get_time_bucket_by_sun(now, sunrise, sunset):
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
        (75, "blue_hour"),
        (100, "dusk"),
        (140, "deep_twilight"),
    ]

    # Sunrise window: 60 min before to 60 min after
    if -60 <= minutes_from_sunrise < 60:
        return closest_bucket(minutes_from_sunrise, sunrise_buckets)

    # Sunset window: 60 min before to 60 min after
    if -60 <= minutes_from_sunset < 60:
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
        "pre_dawn": "shade_75",

        "sunrise_-60": "shade_50",
        "sunrise_-45": "shade_25",
        "sunrise_-30": "shade_10",
        "sunrise_-15": "shade_0",
        "sunrise_0": "shade_0",
        "sunrise_15": "shade_0",
        "sunrise_30": "shade_0",
        "sunrise_45": "shade_0",

        "early_morning": "shade_0",
        "mid_morning": "shade_0",
        "late_morning": "shade_0",
        "noon": "shade_0",
        "early_afternoon": "shade_0",
        "mid_afternoon": "shade_0",
        "late_afternoon": "shade_0",
        "golden_early": "shade_0",

        "sunset_-60": "shade_0",
        "sunset_-45": "shade_0",
        "sunset_-30": "shade_0",
        "sunset_-15": "shade_0",
        "sunset_0": "shade_0",
        "sunset_15": "shade_10",
        "sunset_30": "shade_25",
        "sunset_45": "shade_50",
        "sunset_60": "shade_75",

        "blue_hour": "shade_75",
        "dusk": "shade_50",
        "deep_twilight": "shade_75",
        "night": "shade_100",
        "deep_night": "shade_100",   
    }
    return shade_by_bucket.get(bucket, "shade_0")

def get_star_bucket(bucket):
    """Return the star overlay filename stem for the current sky bucket."""
    star_by_bucket = {
        "pre_dawn": "stars_75",

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
        "dusk": "stars_50",
        "deep_twilight": "stars_75",
        "night": "stars_100",
        "deep_night": "stars_100",   
    }
    return star_by_bucket.get(bucket, "stars_0")