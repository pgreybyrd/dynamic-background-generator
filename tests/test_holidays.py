#pytest tests/test_holidays.py -v
import datetime

import pytest

from wallpaper.holidays import (
    calculate_easter,
    second_sunday_of_may,
    third_sunday_of_june,
    fourth_thursday_of_november,
    get_holiday,
    get_banner,
)


# ~~~~~ MOVABLE HOLIDAY HELPERS ~~~~~

@pytest.mark.parametrize(
    "year, expected",
    [
        (2024, datetime.date(2024, 3, 31)),
        (2025, datetime.date(2025, 4, 20)),
        (2026, datetime.date(2026, 4, 5)),
        (2027, datetime.date(2027, 3, 28)),
    ],
)
def test_calculate_easter(year, expected):
    assert calculate_easter(year) == expected


@pytest.mark.parametrize(
    "year, expected_day",
    [
        (2024, 12),
        (2025, 11),
        (2026, 10),
        (2027, 9),
    ],
)
def test_second_sunday_of_may(year, expected_day):
    assert second_sunday_of_may(year) == expected_day


@pytest.mark.parametrize(
    "year, expected_day",
    [
        (2024, 16),
        (2025, 15),
        (2026, 21),
        (2027, 20),
    ],
)
def test_third_sunday_of_june(year, expected_day):
    assert third_sunday_of_june(year) == expected_day


@pytest.mark.parametrize(
    "year, expected_day",
    [
        (2024, 28),
        (2025, 27),
        (2026, 26),
        (2027, 25),
    ],
)
def test_fourth_thursday_of_november(year, expected_day):
    assert fourth_thursday_of_november(year) == expected_day


# ~~~~~ FIXED HOLIDAYS ~~~~~

@pytest.mark.parametrize(
    "day, month, year, expected",
    [
        (1, 1, 2026, "new_years_day"),
        (14, 2, 2026, "valentines"),
        (17, 3, 2026, "st_patricks_day"),
        (1, 4, 2026, "april_fools"),
        (5, 5, 2026, "cinco_de_mayo"),
        (19, 6, 2026, "juneteenth"),
        (4, 7, 2026, "fourth_of_july"),
        (31, 10, 2026, "halloween"),
        (1, 11, 2026, "dia_de_los_muertos"),
        (24, 12, 2026, "christmas_eve"),
        (25, 12, 2026, "christmas_day"),
        (31, 12, 2026, "new_years_eve"),
    ],
)
def test_fixed_holidays(day, month, year, expected):
    assert get_holiday(day, month, year) == expected


# ~~~~~ MOVABLE HOLIDAYS THROUGH get_holiday() ~~~~~

def test_easter():
    assert get_holiday(5, 4, 2026) == "easter"


def test_mothers_day():
    assert get_holiday(10, 5, 2026) == "mothers_day"


def test_fathers_day():
    assert get_holiday(21, 6, 2026) == "fathers_day"


def test_thanksgiving():
    assert get_holiday(26, 11, 2026) == "thanksgiving"


# ~~~~~ ORDINARY DAYS ~~~~~

@pytest.mark.parametrize(
    "day, month, year",
    [
        (2, 1, 2026),
        (15, 2, 2026),
        (18, 3, 2026),
        (2, 4, 2026),
        (6, 5, 2026),
        (20, 6, 2026),
        (5, 7, 2026),
        (1, 8, 2026),
        (7, 9, 2026),
        (30, 10, 2026),
        (2, 11, 2026),
        (26, 12, 2026),
    ],
)
def test_non_holidays(day, month, year):
    assert get_holiday(day, month, year) == "none"


# ~~~~~ BANNERS ~~~~~

def test_astronomical_event_banner_has_priority():
    assert (
        get_banner(
            "christmas_day",
            "winter_solstice",
        )
        == "winter_solstice"
    )


def test_holiday_becomes_banner_when_no_astronomical_event():
    assert (
        get_banner(
            "christmas_day",
            "none",
        )
        == "christmas_day"
    )


def test_no_special_event_means_no_banner():
    assert get_banner("none", "none") == "none"