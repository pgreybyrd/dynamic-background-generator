#pytest tests/test_weather.py -v
import pytest

from wallpaper.weather import (
    bucket_cloud_cover,
    bucket_rain,
    bucket_snow,
    get_atmosphere,
    get_unknown_weather_state,
)


# ~~~~~ CLOUD COVER ~~~~~

@pytest.mark.parametrize(
    "percent, expected",
    [
        (None, "none"),
        (0, "none"),
        (10, "none"),
        (11, "very_light"),
        (30, "very_light"),
        (31, "light"),
        (55, "light"),
        (56, "medium"),
        (75, "medium"),
        (76, "heavy"),
        (90, "heavy"),
        (91, "very_heavy"),
        (100, "very_heavy"),
    ],
)
def test_bucket_cloud_cover(percent, expected):
    assert bucket_cloud_cover(percent) == expected


# ~~~~~ RAIN ~~~~~

@pytest.mark.parametrize(
    "amount, expected",
    [
        (None, "none"),
        (0, "none"),
        (0.1, "very_light"),
        (0.19, "very_light"),
        (0.2, "light"),
        (0.99, "light"),
        (1, "medium"),
        (3.99, "medium"),
        (4, "heavy"),
        (9.99, "heavy"),
        (10, "very_heavy"),
        (25, "very_heavy"),
    ],
)
def test_bucket_rain(amount, expected):
    assert bucket_rain(amount) == expected


# ~~~~~ SNOW ~~~~~

@pytest.mark.parametrize(
    "amount, expected",
    [
        (None, "none"),
        (0, "none"),
        (0.05, "very_light"),
        (0.09, "very_light"),
        (0.1, "light"),
        (0.49, "light"),
        (0.5, "medium"),
        (1.49, "medium"),
        (1.5, "heavy"),
        (3.99, "heavy"),
        (4, "very_heavy"),
        (10, "very_heavy"),
    ],
)
def test_bucket_snow(amount, expected):
    assert bucket_snow(amount) == expected


# ~~~~~ ATMOSPHERE ~~~~~

def test_weather_code_atmosphere_takes_priority():
    code_info = {
        "atmosphere": "fog",
    }

    air_quality = {
        "current": {
            "pm2_5": 100,
            "dust": 100,
            "aerosol_optical_depth": 1.0,
        }
    }

    assert get_atmosphere(code_info, air_quality) == "fog"


def test_dust():
    code_info = {}

    air_quality = {
        "current": {
            "pm2_5": 0,
            "dust": 50,
            "aerosol_optical_depth": 0,
        }
    }

    assert get_atmosphere(code_info, air_quality) == "dust"


def test_smoke():
    code_info = {}

    air_quality = {
        "current": {
            "pm2_5": 35,
            "dust": 0,
            "aerosol_optical_depth": 0,
        }
    }

    assert get_atmosphere(code_info, air_quality) == "smoke"


def test_haze():
    code_info = {}

    air_quality = {
        "current": {
            "pm2_5": 0,
            "dust": 0,
            "aerosol_optical_depth": 0.4,
        }
    }

    assert get_atmosphere(code_info, air_quality) == "haze"


def test_no_atmosphere():
    assert get_atmosphere({}, {}) == "none"


def test_dust_beats_smoke_and_haze():
    air_quality = {
        "current": {
            "pm2_5": 100,
            "dust": 100,
            "aerosol_optical_depth": 1.0,
        }
    }

    assert get_atmosphere({}, air_quality) == "dust"


def test_smoke_beats_haze():
    air_quality = {
        "current": {
            "pm2_5": 100,
            "dust": 0,
            "aerosol_optical_depth": 1.0,
        }
    }

    assert get_atmosphere({}, air_quality) == "smoke"


# ~~~~~ FALLBACK STATE ~~~~~

def test_unknown_weather_state_has_safe_visual_defaults():
    state = get_unknown_weather_state()

    assert state["weather"] == {
        "clouds": {
            "type": "normal",
            "coverage": "none",
        },
        "rain": "none",
        "snow": "none",
        "atmosphere": "none",
        "thunderstorm": False,
    }

    assert state["raw"] == {}


def test_unknown_weather_state_has_sunrise_and_sunset():
    state = get_unknown_weather_state()

    assert state["sunrise"].hour == 6
    assert state["sunset"].hour == 18