# pytest tests/test_seasons.py -v
import datetime

import pytest

from wallpaper.seasons import (
    LOCAL_TIMEZONE,
    get_astronomical_boundaries,
    split_season_into_thirds,
    get_season,
    get_astronomical_event,
)


# ~~~~~ ASTRONOMICAL BOUNDARIES ~~~~~

def test_boundaries_include_all_four_seasons():
    boundaries = get_astronomical_boundaries(2026)

    assert set(boundaries.keys()) == {
        "spring",
        "summer",
        "autumn",
        "winter",
    }


def test_boundaries_are_in_chronological_order():
    boundaries = get_astronomical_boundaries(2026)

    assert (
        boundaries["spring"]
        < boundaries["summer"]
        < boundaries["autumn"]
        < boundaries["winter"]
    )


def test_boundaries_are_timezone_aware():
    boundaries = get_astronomical_boundaries(2026)

    for boundary in boundaries.values():
        assert boundary.tzinfo is not None


# ~~~~~ SEASON THIRDS ~~~~~

def test_beginning_of_season_is_early():
    start = datetime.datetime(
        2026, 3, 20, 0, 0,
        tzinfo=LOCAL_TIMEZONE,
    )
    end = datetime.datetime(
        2026, 6, 20, 0, 0,
        tzinfo=LOCAL_TIMEZONE,
    )

    assert (
        split_season_into_thirds(
            start,
            start,
            end,
            "spring",
        )
        == "early_spring"
    )


def test_first_third_is_early():
    start = datetime.datetime(
        2026, 3, 20,
        tzinfo=LOCAL_TIMEZONE,
    )
    end = datetime.datetime(
        2026, 6, 20,
        tzinfo=LOCAL_TIMEZONE,
    )

    one_third = (end - start) / 3

    now = start + one_third - datetime.timedelta(seconds=1)

    assert (
        split_season_into_thirds(
            now,
            start,
            end,
            "spring",
        )
        == "early_spring"
    )


def test_exact_first_third_boundary_becomes_mid():
    start = datetime.datetime(
        2026, 3, 20,
        tzinfo=LOCAL_TIMEZONE,
    )
    end = datetime.datetime(
        2026, 6, 20,
        tzinfo=LOCAL_TIMEZONE,
    )

    one_third = (end - start) / 3
    now = start + one_third

    assert (
        split_season_into_thirds(
            now,
            start,
            end,
            "spring",
        )
        == "mid_spring"
    )


def test_exact_second_third_boundary_becomes_late():
    start = datetime.datetime(
        2026, 3, 20,
        tzinfo=LOCAL_TIMEZONE,
    )
    end = datetime.datetime(
        2026, 6, 20,
        tzinfo=LOCAL_TIMEZONE,
    )

    one_third = (end - start) / 3
    now = start + (one_third * 2)

    assert (
        split_season_into_thirds(
            now,
            start,
            end,
            "spring",
        )
        == "late_spring"
    )


# ~~~~~ REAL ASTRONOMICAL SEASONS ~~~~~

@pytest.mark.parametrize(
    "month, day, expected",
    [
        (4, 1, "early_spring"),
        (5, 1, "mid_spring"),
        (6, 1, "late_spring"),

        (7, 1, "early_summer"),
        (8, 1, "mid_summer"),
        (9, 1, "late_summer"),

        (10, 1, "early_autumn"),
        (11, 1, "mid_autumn"),
        (12, 1, "late_autumn"),

        (1, 1, "early_winter"),
        (2, 1, "mid_winter"),
        (3, 1, "late_winter"),
    ],
)
def test_season_thirds_across_year(month, day, expected):
    now = datetime.datetime(
        2026,
        month,
        day,
        12,
        tzinfo=LOCAL_TIMEZONE,
    )

    assert get_season(now) == expected


# ~~~~~ EXACT SEASON TRANSITIONS ~~~~~

@pytest.mark.parametrize(
    "boundary_name, expected",
    [
        ("spring", "early_spring"),
        ("summer", "early_summer"),
        ("autumn", "early_autumn"),
        ("winter", "early_winter"),
    ],
)
def test_exact_astronomical_boundary_starts_new_season(
    boundary_name,
    expected,
):
    boundaries = get_astronomical_boundaries(2026)
    boundary = boundaries[boundary_name]

    assert get_season(boundary) == expected


def test_moment_before_spring_is_still_winter():
    spring = get_astronomical_boundaries(2026)["spring"]

    just_before = spring - datetime.timedelta(seconds=1)

    assert get_season(just_before) == "late_winter"


def test_moment_before_summer_is_still_spring():
    summer = get_astronomical_boundaries(2026)["summer"]

    just_before = summer - datetime.timedelta(seconds=1)

    assert get_season(just_before) == "late_spring"


def test_moment_before_autumn_is_still_summer():
    autumn = get_astronomical_boundaries(2026)["autumn"]

    just_before = autumn - datetime.timedelta(seconds=1)

    assert get_season(just_before) == "late_summer"


def test_moment_before_winter_is_still_autumn():
    winter = get_astronomical_boundaries(2026)["winter"]

    just_before = winter - datetime.timedelta(seconds=1)

    assert get_season(just_before) == "late_autumn"


# ~~~~~ WINTER CROSSING CALENDAR YEARS ~~~~~

def test_january_uses_previous_years_winter():
    now = datetime.datetime(
        2026, 1, 15, 12,
        tzinfo=LOCAL_TIMEZONE,
    )

    assert get_season(now) == "early_winter"


def test_march_before_equinox_is_late_winter():
    spring = get_astronomical_boundaries(2026)["spring"]

    now = spring - datetime.timedelta(days=1)

    assert get_season(now) == "late_winter"


def test_december_after_solstice_is_early_winter():
    winter = get_astronomical_boundaries(2026)["winter"]

    now = winter + datetime.timedelta(days=1)

    assert get_season(now) == "early_winter"


# ~~~~~ NAIVE DATETIME SUPPORT ~~~~~

def test_naive_datetime_is_treated_as_local_time():
    naive = datetime.datetime(
        2026, 7, 1, 12,
    )

    aware = naive.replace(
        tzinfo=LOCAL_TIMEZONE,
    )

    assert get_season(naive) == get_season(aware)


# ~~~~~ ASTRONOMICAL EVENT BANNERS ~~~~~

@pytest.mark.parametrize(
    "boundary_name, expected",
    [
        ("spring", "spring_equinox"),
        ("summer", "summer_solstice"),
        ("autumn", "autumn_equinox"),
        ("winter", "winter_solstice"),
    ],
)
def test_astronomical_event_on_event_date(
    boundary_name,
    expected,
):
    boundaries = get_astronomical_boundaries(2026)

    assert (
        get_astronomical_event(
            boundaries[boundary_name]
        )
        == expected
    )


@pytest.mark.parametrize(
    "month, day",
    [
        (1, 15),
        (2, 15),
        (4, 15),
        (5, 15),
        (7, 15),
        (8, 15),
        (10, 15),
        (11, 15),
    ],
)
def test_ordinary_days_have_no_astronomical_event(
    month,
    day,
):
    now = datetime.datetime(
        2026,
        month,
        day,
        12,
        tzinfo=LOCAL_TIMEZONE,
    )

    assert get_astronomical_event(now) == "none"


def test_entire_astronomical_event_date_counts():
    spring = get_astronomical_boundaries(2026)["spring"]

    later_that_day = spring.replace(
        hour=23,
        minute=59,
        second=59,
    )

    assert (
        get_astronomical_event(later_that_day)
        == "spring_equinox"
    )


def test_day_after_astronomical_event_has_no_event():
    spring = get_astronomical_boundaries(2026)["spring"]

    next_day = spring + datetime.timedelta(days=1)

    assert get_astronomical_event(next_day) == "none"


def test_naive_datetime_works_for_astronomical_events():
    spring = get_astronomical_boundaries(2026)["spring"]

    naive = spring.replace(tzinfo=None)

    assert (
        get_astronomical_event(naive)
        == "spring_equinox"
    )