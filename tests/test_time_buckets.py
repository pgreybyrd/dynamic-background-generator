#pytest tests/test_time_buckets.py -v
import datetime

import pytest

from wallpaper.time_buckets import (
    closest_bucket,
    get_time_bucket_by_sun,
    get_shade_by_bucket,
    get_star_bucket,
    get_moon_bucket,
)


# Use simple fixed sunrise/sunset times so these tests care about
# bucket logic, not whatever today's actual sunrise happens to be.
SUNRISE = datetime.datetime(2026, 6, 1, 6, 0)
SUNSET = datetime.datetime(2026, 6, 1, 20, 0)


def time_at(hour, minute=0):
    return datetime.datetime(2026, 6, 1, hour, minute)


# ~~~~~ CLOSEST BUCKET ~~~~~

def test_closest_bucket_exact_match():
    schedule = [
        (-60, "a"),
        (-30, "b"),
        (0, "c"),
    ]

    assert closest_bucket(-30, schedule) == "b"


def test_closest_bucket_chooses_nearest():
    schedule = [
        (-60, "a"),
        (-30, "b"),
        (0, "c"),
    ]

    assert closest_bucket(-40, schedule) == "b"


# ~~~~~ BEFORE SUNRISE ~~~~~

@pytest.mark.parametrize(
    "now, expected",
    [
        (time_at(1, 0), "deep_night"),
        (time_at(2, 59), "deep_night"),
        (time_at(3, 0), "pre_dawn"),
        (time_at(3, 59), "pre_dawn"),
        (time_at(4, 0), "pre_dawn"),
        (time_at(4, 59), "pre_dawn"),
    ],
)
def test_before_sunrise(now, expected):
    assert get_time_bucket_by_sun(now, SUNRISE, SUNSET) == expected


# ~~~~~ SUNRISE WINDOW ~~~~~

@pytest.mark.parametrize(
    "minutes, expected",
    [
        (-60, "sunrise_-60"),
        (-45, "sunrise_-45"),
        (-30, "sunrise_-30"),
        (-15, "sunrise_-15"),
        (0, "sunrise_0"),
        (15, "sunrise_15"),
        (30, "sunrise_30"),
        (45, "sunrise_45"),
    ],
)
def test_sunrise_buckets(minutes, expected):
    now = SUNRISE + datetime.timedelta(minutes=minutes)

    assert get_time_bucket_by_sun(now, SUNRISE, SUNSET) == expected


def test_sunrise_window_uses_nearest_bucket():
    now = SUNRISE + datetime.timedelta(minutes=22)

    assert (
        get_time_bucket_by_sun(now, SUNRISE, SUNSET)
        == "sunrise_15"
    )


# ~~~~~ DAYTIME ~~~~~

@pytest.mark.parametrize(
    "hour, minute, expected",
    [
        (8, 0, "early_morning"),
        (9, 30, "mid_morning"),
        (11, 0, "late_morning"),
        (12, 30, "noon"),
        (14, 0, "early_afternoon"),
        (15, 30, "mid_afternoon"),
        (17, 0, "late_afternoon"),
    ],
)
def test_daytime_progression(hour, minute, expected):
    now = time_at(hour, minute)

    assert get_time_bucket_by_sun(now, SUNRISE, SUNSET) == expected


# ~~~~~ SUNSET WINDOW ~~~~~

@pytest.mark.parametrize(
    "minutes, expected",
    [
        (-90, "golden_early"),
        (-60, "sunset_-60"),
        (-45, "sunset_-45"),
        (-30, "sunset_-30"),
        (-15, "sunset_-15"),
        (0, "sunset_0"),
        (10, "sunset_15"),
        (20, "sunset_30"),
        (30, "sunset_45"),
        (40, "sunset_60"),
    ],
)
def test_sunset_buckets(minutes, expected):
    now = SUNSET + datetime.timedelta(minutes=minutes)

    assert get_time_bucket_by_sun(now, SUNRISE, SUNSET) == expected


def test_sunset_window_uses_nearest_bucket():
    now = SUNSET + datetime.timedelta(minutes=17)

    assert (
        get_time_bucket_by_sun(now, SUNRISE, SUNSET)
        == "sunset_30"
    )


# ~~~~~ NIGHT AFTER SUNSET ~~~~~

def test_after_sunset_window_returns_night():
    now = SUNSET + datetime.timedelta(hours=2)

    assert get_time_bucket_by_sun(now, SUNRISE, SUNSET) == "night"


# ~~~~~ SHADE MAPPING ~~~~~

@pytest.mark.parametrize(
    "bucket, expected",
    [
        ("deep_night", "shade_100"),
        ("night", "shade_100"),
        ("pre_dawn", "shade_75"),

        ("sunrise_-60", "shade_50"),
        ("sunrise_-45", "shade_25"),
        ("sunrise_-30", "shade_10"),
        ("sunrise_-15", "shade_0"),
        ("sunrise_0", "shade_0"),

        ("noon", "shade_0"),
        ("golden_early", "shade_0"),
        ("sunset_0", "shade_0"),

        ("sunset_15", "shade_10"),
        ("sunset_30", "shade_25"),
        ("sunset_45", "shade_50"),
        ("sunset_60", "shade_75"),

        ("blue_hour", "shade_75"),
        ("dusk", "shade_50"),
        ("deep_twilight", "shade_75"),
    ],
)
def test_shade_mapping(bucket, expected):
    assert get_shade_by_bucket(bucket) == expected


def test_unknown_bucket_gets_no_shade():
    assert get_shade_by_bucket("what_even_is_time") == "shade_0"


# ~~~~~ STAR MAPPING ~~~~~

@pytest.mark.parametrize(
    "bucket, expected",
    [
        ("deep_night", "stars_100"),
        ("night", "stars_100"),
        ("pre_dawn", "stars_75"),

        ("sunrise_-60", "stars_50"),
        ("sunrise_-45", "stars_25"),
        ("sunrise_-30", "stars_10"),
        ("sunrise_-15", "stars_0"),
        ("sunrise_0", "stars_0"),

        ("noon", "stars_0"),
        ("golden_early", "stars_0"),
        ("sunset_0", "stars_0"),

        ("sunset_15", "stars_10"),
        ("sunset_30", "stars_25"),
        ("sunset_45", "stars_50"),
        ("sunset_60", "stars_75"),

        ("blue_hour", "stars_75"),
        ("dusk", "stars_50"),
        ("deep_twilight", "stars_75"),
    ],
)
def test_star_mapping(bucket, expected):
    assert get_star_bucket(bucket) == expected


def test_unknown_bucket_gets_no_stars():
    assert get_star_bucket("what_even_is_time") == "stars_0"


# ~~~~~ MOON MAPPING ~~~~~

@pytest.mark.parametrize(
    "bucket, expected",
    [
        ("deep_night", "moon_100"),
        ("night", "moon_100"),
        ("pre_dawn", "moon_100"),

        ("sunrise_-60", "moon_75"),
        ("sunrise_-45", "moon_50"),
        ("sunrise_-30", "moon_25"),
        ("sunrise_-15", "moon_10"),
        ("sunrise_0", "moon_0"),

        ("early_morning", "moon_0"),
        ("noon", "moon_0"),
        ("late_afternoon", "moon_0"),

        ("golden_early", "moon_0"),
        ("sunset_-60", "moon_0"),
        ("sunset_-45", "moon_10"),
        ("sunset_-30", "moon_25"),
        ("sunset_-15", "moon_50"),
        ("sunset_0", "moon_75"),

        ("sunset_15", "moon_100"),
        ("sunset_30", "moon_100"),
        ("sunset_45", "moon_100"),
        ("sunset_60", "moon_100"),

        ("blue_hour", "moon_100"),
        ("dusk", "moon_100"),
        ("deep_twilight", "moon_100"),
    ],
)
def test_moon_mapping(bucket, expected):
    assert get_moon_bucket(bucket) == expected


def test_unknown_bucket_hides_moon():
    assert get_moon_bucket("what_even_is_time") == "moon_0"