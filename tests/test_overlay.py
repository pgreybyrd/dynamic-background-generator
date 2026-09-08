#pytest tests/test_overlay.py -v
from PIL import Image

from wallpaper.overlay import add_weather_overlay


def make_image(path, size=(800, 400)):
    image = Image.new(
        "RGBA",
        size,
        (20, 30, 40, 255),
    )
    image.save(path)
    image.close()

    return path


def test_overlay_creates_output_file(tmp_path):
    input_path = make_image(
        tmp_path / "input.png"
    )

    output_path = tmp_path / "output.png"

    result = add_weather_overlay(
        input_path,
        {
            "main": {
                "temp": 72,
            },
            "weather": [
                {
                    "description": "clear sky",
                }
            ],
        },
        output_path,
    )

    assert result == output_path
    assert output_path.exists()


def test_overlay_preserves_image_size(tmp_path):
    input_path = make_image(
        tmp_path / "input.png",
        size=(900, 500),
    )

    output_path = tmp_path / "output.png"

    add_weather_overlay(
        input_path,
        {
            "main": {
                "temp": 65,
            },
            "weather": [
                {
                    "description": "light rain",
                }
            ],
        },
        output_path,
    )

    image = Image.open(output_path)

    assert image.size == (900, 500)

    image.close()


def test_overlay_actually_changes_pixels(tmp_path):
    input_path = make_image(
        tmp_path / "input.png"
    )

    output_path = tmp_path / "output.png"

    add_weather_overlay(
        input_path,
        {
            "main": {
                "temp": 72,
            },
            "weather": [
                {
                    "description": "clear sky",
                }
            ],
        },
        output_path,
    )

    original = Image.open(input_path).convert("RGBA")
    result = Image.open(output_path).convert("RGBA")

    assert list(original.getdata()) != list(result.getdata())

    original.close()
    result.close()


def test_temperature_only_still_creates_overlay(tmp_path):
    input_path = make_image(
        tmp_path / "input.png"
    )

    output_path = tmp_path / "output.png"

    result = add_weather_overlay(
        input_path,
        {
            "main": {
                "temp": 42.6,
            },
            "weather": [
                {
                    "description": "",
                }
            ],
        },
        output_path,
    )

    assert result == output_path
    assert output_path.exists()


def test_description_only_still_creates_overlay(tmp_path):
    input_path = make_image(
        tmp_path / "input.png"
    )

    output_path = tmp_path / "output.png"

    result = add_weather_overlay(
        input_path,
        {
            "main": {},
            "weather": [
                {
                    "description": "heavy rain",
                }
            ],
        },
        output_path,
    )

    assert result == output_path
    assert output_path.exists()


def test_empty_weather_is_safe_no_op(tmp_path):
    input_path = make_image(
        tmp_path / "input.png"
    )

    output_path = tmp_path / "output.png"

    result = add_weather_overlay(
        input_path,
        {},
        output_path,
    )

    assert result == input_path
    assert not output_path.exists()


def test_missing_weather_list_is_safe(tmp_path):
    input_path = make_image(
        tmp_path / "input.png"
    )

    output_path = tmp_path / "output.png"

    result = add_weather_overlay(
        input_path,
        {
            "main": {},
        },
        output_path,
    )

    assert result == input_path


def test_empty_weather_list_is_safe(tmp_path):
    input_path = make_image(
        tmp_path / "input.png"
    )

    output_path = tmp_path / "output.png"

    result = add_weather_overlay(
        input_path,
        {
            "main": {},
            "weather": [],
        },
        output_path,
    )

    assert result == input_path


def test_decimal_temperature_is_supported(tmp_path):
    input_path = make_image(
        tmp_path / "input.png"
    )

    output_path = tmp_path / "output.png"

    result = add_weather_overlay(
        input_path,
        {
            "main": {
                "temp": 71.8,
            },
            "weather": [],
        },
        output_path,
    )

    assert result == output_path
    assert output_path.exists()