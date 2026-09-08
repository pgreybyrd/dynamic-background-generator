#pytest tests/test_moon.py -v
import pytest

from wallpaper.moon import get_moon_global_position


@pytest.mark.parametrize(
    "bucket, expected",
    [
        ("sunset_45", (200, 850)),
        ("sunset_60", (600, 650)),
        ("blue_hour", (1100, 400)),
        ("dusk", (1700, 120)),
        ("deep_twilight", (2100, -250)),
        ("night", (2600, -650)),
        ("deep_night", (3100, -720)),
        ("pre_dawn", (3600, -350)),
        ("sunrise_-60", (4400, 200)),
        ("sunrise_-45", (5000, 500)),
    ],
)
def test_moon_positions(bucket, expected):
    assert get_moon_global_position(bucket) == expected


@pytest.mark.parametrize(
    "bucket",
    [
        "noon",
        "early_morning",
        "mid_afternoon",
        "sunrise_0",
        "sunset_0",
        "what_even_is_the_moon_doing",
        None,
    ],
)
def test_unmapped_bucket_has_no_moon_position(bucket):
    assert get_moon_global_position(bucket) is None