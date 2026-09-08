from pathlib import Path

import pytest

from wallpaper.helpers import (
    layer_fingerprint,
    weather_overlay_fingerprint,
    next_output_slot,
)


# ~~~~~ LAYER FINGERPRINT ~~~~~

def test_layer_fingerprint_converts_paths_to_strings():
    paths = [
        Path("sky.png"),
        Path("clouds.png"),
        Path("landscape.png"),
    ]

    assert layer_fingerprint(paths) == [
        str(Path("sky.png")),
        str(Path("clouds.png")),
        str(Path("landscape.png")),
    ]


def test_layer_fingerprint_handles_empty_list():
    assert layer_fingerprint([]) == []


def test_layer_fingerprint_preserves_order():
    paths = [
        Path("first.png"),
        Path("second.png"),
        Path("third.png"),
    ]

    result = layer_fingerprint(paths)

    assert result == [str(path) for path in paths]


# ~~~~~ WEATHER OVERLAY FINGERPRINT ~~~~~

def test_weather_fingerprint_extracts_displayed_values():
    weather = {
        "main": {
            "temp": 71.8,
        },
        "weather": [
            {
                "description": "broken clouds",
            }
        ],
    }

    assert weather_overlay_fingerprint(weather) == {
        "temp": 72,
        "description": "Broken Clouds",
    }


@pytest.mark.parametrize(
    "temperature, expected",
    [
        (71.1, 71),
        (71.4, 71),
        (71.5, 72),
        (71.8, 72),
        (-4.4, -4),
        (-4.6, -5),
    ],
)
def test_weather_fingerprint_rounds_temperature(
    temperature,
    expected,
):
    weather = {
        "main": {
            "temp": temperature,
        },
        "weather": [],
    }

    result = weather_overlay_fingerprint(weather)

    assert result["temp"] == expected


def test_weather_fingerprint_handles_missing_temperature():
    weather = {
        "main": {},
        "weather": [
            {
                "description": "clear sky",
            }
        ],
    }

    assert weather_overlay_fingerprint(weather) == {
        "temp": None,
        "description": "Clear Sky",
    }


def test_weather_fingerprint_handles_missing_main():
    weather = {
        "weather": [
            {
                "description": "rain",
            }
        ],
    }

    assert weather_overlay_fingerprint(weather) == {
        "temp": None,
        "description": "Rain",
    }


def test_weather_fingerprint_handles_missing_weather():
    assert weather_overlay_fingerprint(
        {
            "main": {
                "temp": 70,
            }
        }
    ) == {
        "temp": 70,
        "description": "",
    }


def test_weather_fingerprint_handles_empty_weather_list():
    assert weather_overlay_fingerprint(
        {
            "main": {
                "temp": 70,
            },
            "weather": [],
        }
    ) == {
        "temp": 70,
        "description": "",
    }


def test_weather_fingerprint_only_uses_first_condition():
    weather = {
        "main": {
            "temp": 50,
        },
        "weather": [
            {
                "description": "snow",
            },
            {
                "description": "rain",
            },
        ],
    }

    assert weather_overlay_fingerprint(weather) == {
        "temp": 50,
        "description": "Snow",
    }


# ~~~~~ OUTPUT SLOT ~~~~~

def test_output_slot_alternates_a_to_b():
    assert next_output_slot("a") == "b"


def test_output_slot_alternates_b_to_a():
    assert next_output_slot("b") == "a"


@pytest.mark.parametrize(
    "previous_slot",
    [
        None,
        "",
        "garbage",
    ],
)
def test_uninitialized_output_slot_starts_with_a(previous_slot):
    assert next_output_slot(previous_slot) == "a"