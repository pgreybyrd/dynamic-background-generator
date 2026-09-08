#pytest tests/test_assets.py -v
from pathlib import Path

from wallpaper.assets import (
    optional_layer,
    weather_layer_path,
    get_layer_paths,
)


def touch(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()
    return path


def basic_weather():
    return {
        "clouds": {
            "type": "normal",
            "coverage": "none",
        },
        "rain": "none",
        "snow": "none",
        "atmosphere": "none",
        "thunderstorm": False,
    }


# ~~~~~ OPTIONAL LAYERS ~~~~~

def test_optional_layer_returns_existing_path(tmp_path):
    path = touch(tmp_path / "exists.png")

    assert optional_layer(path) == path


def test_optional_layer_skips_missing_path(tmp_path):
    path = tmp_path / "missing.png"

    assert optional_layer(path) is None


def test_optional_layer_skips_none():
    assert optional_layer(None) is None


# ~~~~~ WEATHER PATH BUILDING ~~~~~

def test_weather_layer_path_without_subtype(tmp_path):
    result = weather_layer_path(
        tmp_path,
        "rain",
        "horizontal",
        "heavy",
    )

    assert result == (
        tmp_path
        / "weather"
        / "active"
        / "rain"
        / "horizontal"
        / "heavy.png"
    )


def test_weather_layer_path_with_subtype(tmp_path):
    result = weather_layer_path(
        tmp_path,
        "clouds",
        "vertical",
        "very_heavy",
        subtype="storm",
    )

    assert result == (
        tmp_path
        / "weather"
        / "active"
        / "clouds"
        / "storm"
        / "vertical"
        / "very_heavy.png"
    )


def test_weather_layer_path_skips_none_variant(tmp_path):
    assert (
        weather_layer_path(
            tmp_path,
            "rain",
            "horizontal",
            "none",
        )
        is None
    )


def test_weather_layer_path_skips_empty_variant(tmp_path):
    assert (
        weather_layer_path(
            tmp_path,
            "rain",
            "horizontal",
            "",
        )
        is None
    )


# ~~~~~ BASE LAYER RESOLUTION ~~~~~

def test_get_layer_paths_finds_required_base_art(tmp_path):
    sky = touch(
        tmp_path
        / "sky"
        / "horizontal"
        / "noon.png"
    )

    landscape = touch(
        tmp_path
        / "landscape"
        / "horizontal"
        / "base.png"
    )

    result = get_layer_paths(
        bucket="noon",
        stars="stars_0",
        moon="moon_0",
        season="mid_summer",
        holiday="none",
        weather=basic_weather(),
        shade="none",
        banner="none",
        assets_dir=tmp_path,
        layout="horizontal",
    )

    assert result["layers"] == [
        sky,
        landscape,
    ]

    assert result["banner"] is None


def test_missing_optional_art_does_not_crash(tmp_path):
    sky = touch(
        tmp_path
        / "sky"
        / "horizontal"
        / "noon.png"
    )

    landscape = touch(
        tmp_path
        / "landscape"
        / "horizontal"
        / "base.png"
    )

    result = get_layer_paths(
        bucket="noon",
        stars="stars_100",
        moon="moon_100",
        season="late_autumn",
        holiday="halloween",
        weather={
            "clouds": {
                "type": "storm",
                "coverage": "very_heavy",
            },
            "rain": "heavy",
            "snow": "heavy",
            "atmosphere": "smoke",
            "thunderstorm": True,
        },
        shade="shade_100",
        banner="halloween",
        assets_dir=tmp_path,
        layout="horizontal",
    )

    assert result["layers"] == [
        sky,
        landscape,
    ]

    assert result["banner"] is None


# ~~~~~ LAYOUT SEPARATION ~~~~~

def test_horizontal_uses_horizontal_assets(tmp_path):
    horizontal = touch(
        tmp_path
        / "landscape"
        / "horizontal"
        / "base.png"
    )

    touch(
        tmp_path
        / "landscape"
        / "vertical"
        / "base.png"
    )

    touch(
        tmp_path
        / "landscape"
        / "panorama"
        / "base.png"
    )

    result = get_layer_paths(
        "noon",
        "stars_0",
        "moon_0",
        "mid_summer",
        "none",
        basic_weather(),
        "none",
        "none",
        tmp_path,
        "horizontal",
    )

    assert horizontal in result["layers"]


def test_vertical_uses_vertical_assets(tmp_path):
    vertical = touch(
        tmp_path
        / "landscape"
        / "vertical"
        / "base.png"
    )

    touch(
        tmp_path
        / "landscape"
        / "horizontal"
        / "base.png"
    )

    result = get_layer_paths(
        "noon",
        "stars_0",
        "moon_0",
        "mid_summer",
        "none",
        basic_weather(),
        "none",
        "none",
        tmp_path,
        "vertical",
    )

    assert vertical in result["layers"]


def test_panorama_uses_panorama_assets(tmp_path):
    panorama = touch(
        tmp_path
        / "landscape"
        / "panorama"
        / "base.png"
    )

    touch(
        tmp_path
        / "landscape"
        / "horizontal"
        / "base.png"
    )

    result = get_layer_paths(
        "noon",
        "stars_0",
        "moon_0",
        "mid_summer",
        "none",
        basic_weather(),
        "none",
        "none",
        tmp_path,
        "panorama",
    )

    assert panorama in result["layers"]


# ~~~~~ WEATHER LAYERS ~~~~~

def test_normal_cloud_layer_is_resolved(tmp_path):
    clouds = touch(
        tmp_path
        / "weather"
        / "active"
        / "clouds"
        / "normal"
        / "horizontal"
        / "medium.png"
    )

    result = get_layer_paths(
        "noon",
        "stars_0",
        "moon_0",
        "mid_summer",
        "none",
        {
            "clouds": {
                "type": "normal",
                "coverage": "medium",
            },
            "rain": "none",
            "snow": "none",
            "atmosphere": "none",
            "thunderstorm": False,
        },
        "none",
        "none",
        tmp_path,
        "horizontal",
    )

    assert clouds in result["layers"]


def test_storm_cloud_layer_is_resolved(tmp_path):
    clouds = touch(
        tmp_path
        / "weather"
        / "active"
        / "clouds"
        / "storm"
        / "panorama"
        / "very_heavy.png"
    )

    result = get_layer_paths(
        "noon",
        "stars_0",
        "moon_0",
        "mid_summer",
        "none",
        {
            "clouds": {
                "type": "storm",
                "coverage": "very_heavy",
            },
            "rain": "none",
            "snow": "none",
            "atmosphere": "none",
            "thunderstorm": True,
        },
        "none",
        "none",
        tmp_path,
        "panorama",
    )

    assert clouds in result["layers"]


def test_rain_layer_is_resolved(tmp_path):
    rain = touch(
        tmp_path
        / "weather"
        / "active"
        / "rain"
        / "horizontal"
        / "heavy.png"
    )

    weather = basic_weather()
    weather["rain"] = "heavy"

    result = get_layer_paths(
        "noon",
        "stars_0",
        "moon_0",
        "mid_summer",
        "none",
        weather,
        "none",
        "none",
        tmp_path,
        "horizontal",
    )

    assert rain in result["layers"]


def test_snow_layer_is_resolved(tmp_path):
    snow = touch(
        tmp_path
        / "weather"
        / "active"
        / "snow"
        / "vertical"
        / "light.png"
    )

    weather = basic_weather()
    weather["snow"] = "light"

    result = get_layer_paths(
        "noon",
        "stars_0",
        "moon_0",
        "mid_winter",
        "none",
        weather,
        "none",
        "none",
        tmp_path,
        "vertical",
    )

    assert snow in result["layers"]


def test_atmosphere_layer_is_resolved(tmp_path):
    smoke = touch(
        tmp_path
        / "weather"
        / "active"
        / "atmosphere"
        / "horizontal"
        / "smoke.png"
    )

    weather = basic_weather()
    weather["atmosphere"] = "smoke"

    result = get_layer_paths(
        "noon",
        "stars_0",
        "moon_0",
        "mid_summer",
        "none",
        weather,
        "none",
        "none",
        tmp_path,
        "horizontal",
    )

    assert smoke in result["layers"]


def test_lightning_layer_only_when_thunderstorm(tmp_path):
    lightning = touch(
        tmp_path
        / "weather"
        / "active"
        / "lightning"
        / "horizontal"
        / "lightning.png"
    )

    weather = basic_weather()
    weather["thunderstorm"] = True

    result = get_layer_paths(
        "noon",
        "stars_0",
        "moon_0",
        "mid_summer",
        "none",
        weather,
        "none",
        "none",
        tmp_path,
        "horizontal",
    )

    assert lightning in result["layers"]


def test_lightning_is_skipped_without_thunderstorm(tmp_path):
    lightning = touch(
        tmp_path
        / "weather"
        / "active"
        / "lightning"
        / "horizontal"
        / "lightning.png"
    )

    result = get_layer_paths(
        "noon",
        "stars_0",
        "moon_0",
        "mid_summer",
        "none",
        basic_weather(),
        "none",
        "none",
        tmp_path,
        "horizontal",
    )

    assert lightning not in result["layers"]


# ~~~~~ HOLIDAY / BANNER ART ~~~~~

def test_holiday_layer_is_resolved(tmp_path):
    holiday = touch(
        tmp_path
        / "holiday"
        / "horizontal"
        / "christmas_day.png"
    )

    result = get_layer_paths(
        "noon",
        "stars_0",
        "moon_0",
        "mid_winter",
        "christmas_day",
        basic_weather(),
        "none",
        "none",
        tmp_path,
        "horizontal",
    )

    assert holiday in result["layers"]


def test_banner_is_returned_separately(tmp_path):
    banner = touch(
        tmp_path
        / "banners"
        / "winter_solstice.png"
    )

    result = get_layer_paths(
        "noon",
        "stars_0",
        "moon_0",
        "early_winter",
        "none",
        basic_weather(),
        "none",
        "winter_solstice",
        tmp_path,
        "horizontal",
    )

    assert result["banner"] == banner
    assert banner not in result["layers"]


# ~~~~~ LAYER ORDER ~~~~~

def test_layers_are_returned_in_render_order(tmp_path):
    sky = touch(
        tmp_path
        / "sky"
        / "horizontal"
        / "noon.png"
    )

    stars = touch(
        tmp_path
        / "stars"
        / "horizontal"
        / "stars_100.png"
    )

    moon = touch(
        tmp_path
        / "moon"
        / "horizontal"
        / "moon_100.png"
    )

    landscape = touch(
        tmp_path
        / "landscape"
        / "horizontal"
        / "base.png"
    )

    season = touch(
        tmp_path
        / "season"
        / "horizontal"
        / "mid_autumn.png"
    )

    clouds = touch(
        tmp_path
        / "weather"
        / "active"
        / "clouds"
        / "normal"
        / "horizontal"
        / "medium.png"
    )

    holiday = touch(
        tmp_path
        / "holiday"
        / "horizontal"
        / "halloween.png"
    )

    shade = touch(
        tmp_path
        / "shade"
        / "horizontal"
        / "shade_50.png"
    )

    smoke = touch(
        tmp_path
        / "weather"
        / "active"
        / "atmosphere"
        / "horizontal"
        / "smoke.png"
    )

    rain = touch(
        tmp_path
        / "weather"
        / "active"
        / "rain"
        / "horizontal"
        / "heavy.png"
    )

    lightning = touch(
        tmp_path
        / "weather"
        / "active"
        / "lightning"
        / "horizontal"
        / "lightning.png"
    )

    holiday_lights = touch(
        tmp_path
        / "holiday_lights"
        / "horizontal"
        / "halloween.png"
    )

    result = get_layer_paths(
        "noon",
        "stars_100",
        "moon_100",
        "mid_autumn",
        "halloween",
        {
            "clouds": {
                "type": "normal",
                "coverage": "medium",
            },
            "rain": "heavy",
            "snow": "none",
            "atmosphere": "smoke",
            "thunderstorm": True,
        },
        "shade_50",
        "none",
        tmp_path,
        "horizontal",
    )

    assert result["layers"] == [
        sky,
        stars,
        moon,
        landscape,
        season,
        clouds,
        holiday,
        shade,
        smoke,
        rain,
        lightning,
        holiday_lights,
    ]