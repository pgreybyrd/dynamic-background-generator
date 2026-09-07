import datetime
from zoneinfo import ZoneInfo

import astronomy

LOCAL_TIMEZONE = ZoneInfo("America/Los_Angeles")

def get_astronomical_boundaries(year):
    # Get this year's actual equinoxes and solstices in local time.
    seasons = astronomy.Seasons(year)

    return {
        "spring": seasons.mar_equinox.Utc().replace(
            tzinfo=datetime.timezone.utc
        ).astimezone(LOCAL_TIMEZONE),

        "summer": seasons.jun_solstice.Utc().replace(
            tzinfo=datetime.timezone.utc
        ).astimezone(LOCAL_TIMEZONE),

        "autumn": seasons.sep_equinox.Utc().replace(
            tzinfo=datetime.timezone.utc
        ).astimezone(LOCAL_TIMEZONE),

        "winter": seasons.dec_solstice.Utc().replace(
            tzinfo=datetime.timezone.utc
        ).astimezone(LOCAL_TIMEZONE),
    }


def split_season_into_thirds(now, start, end, season_name):
    # Divide one astronomical season into early, mid, and late.
    season_length = end - start
    one_third = season_length / 3

    if now < start + one_third:
        return f"early_{season_name}"

    if now < start + (one_third * 2):
        return f"mid_{season_name}"

    return f"late_{season_name}"


def get_season(now):
    boundaries = get_astronomical_boundaries(now.year)

    spring = boundaries["spring"]
    summer = boundaries["summer"]
    autumn = boundaries["autumn"]
    winter = boundaries["winter"]

    # datetime.now() in main is currently naive, so give it our local timezone
    # before comparing it with the astronomical event times.
    if now.tzinfo is None:
        now = now.replace(tzinfo=LOCAL_TIMEZONE)

    if spring <= now < summer:
        return split_season_into_thirds(
            now, spring, summer, "spring"
        )

    if summer <= now < autumn:
        return split_season_into_thirds(
            now, summer, autumn, "summer"
        )

    if autumn <= now < winter:
        return split_season_into_thirds(
            now, autumn, winter, "autumn"
        )

    if now >= winter:
        next_spring = get_astronomical_boundaries(
            now.year + 1
        )["spring"]

        return split_season_into_thirds(
            now, winter, next_spring, "winter"
        )

    # January through the spring equinox belongs to the winter
    # that began in the previous calendar year.
    previous_winter = get_astronomical_boundaries(
        now.year - 1
    )["winter"]

    return split_season_into_thirds(
        now, previous_winter, spring, "winter"
    )


def get_astronomical_event(now):
    boundaries = get_astronomical_boundaries(now.year)

    if now.tzinfo is None:
        now = now.replace(tzinfo=LOCAL_TIMEZONE)

    today = now.date()

    events = {
        "spring_equinox": boundaries["spring"],
        "summer_solstice": boundaries["summer"],
        "autumn_equinox": boundaries["autumn"],
        "winter_solstice": boundaries["winter"],
    }

    for name, event_time in events.items():
        if today == event_time.date():
            return name

    return "none"