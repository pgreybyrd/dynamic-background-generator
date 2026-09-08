#pytest tests/test_image_composer.py -v
from pathlib import Path

import pytest
from PIL import Image

from wallpaper.image_composer import (
    add_floating_image,
    add_top_centered_image,
    split_panorama,
    compose_wallpaper,
)


def make_image(path, size=(100, 100), color=(0, 0, 0, 0)):
    path.parent.mkdir(parents=True, exist_ok=True)

    image = Image.new("RGBA", size, color)
    image.save(path)
    image.close()

    return path


def get_pixel(path, x, y):
    image = Image.open(path).convert("RGBA")
    pixel = image.getpixel((x, y))
    image.close()

    return pixel


# ~~~~~ FLOATING IMAGE ~~~~~

def test_add_floating_image_places_overlay_at_position(tmp_path):
    base_path = make_image(
        tmp_path / "base.png",
        size=(100, 100),
        color=(0, 0, 0, 255),
    )

    floating_path = make_image(
        tmp_path / "floating.png",
        size=(10, 10),
        color=(255, 0, 0, 255),
    )

    output_path = tmp_path / "output.png"

    result = add_floating_image(
        base_path,
        floating_path,
        output_path,
        position=(20, 30),
    )

    assert result == output_path
    assert output_path.exists()

    assert get_pixel(output_path, 20, 30) == (255, 0, 0, 255)
    assert get_pixel(output_path, 29, 39) == (255, 0, 0, 255)
    assert get_pixel(output_path, 19, 29) == (0, 0, 0, 255)


def test_add_floating_image_preserves_transparency(tmp_path):
    base_path = make_image(
        tmp_path / "base.png",
        size=(20, 20),
        color=(0, 0, 255, 255),
    )

    floating_path = make_image(
        tmp_path / "floating.png",
        size=(10, 10),
        color=(255, 0, 0, 128),
    )

    output_path = tmp_path / "output.png"

    add_floating_image(
        base_path,
        floating_path,
        output_path,
        position=(0, 0),
    )

    pixel = get_pixel(output_path, 0, 0)

    assert pixel[0] > 0
    assert pixel[2] > 0
    assert pixel[3] == 255


# ~~~~~ TOP-CENTERED IMAGE ~~~~~

def test_add_top_centered_image_centers_horizontally(tmp_path):
    base_path = make_image(
        tmp_path / "base.png",
        size=(100, 120),
        color=(0, 0, 0, 255),
    )

    floating_path = make_image(
        tmp_path / "banner.png",
        size=(20, 10),
        color=(255, 0, 0, 255),
    )

    output_path = tmp_path / "output.png"

    add_top_centered_image(
        base_path,
        floating_path,
        output_path,
    )

    expected_x = (100 - 20) // 2
    expected_y = 120 // 12

    assert get_pixel(
        output_path,
        expected_x,
        expected_y,
    ) == (255, 0, 0, 255)


def test_add_top_centered_image_uses_top_twelfth(tmp_path):
    base_path = make_image(
        tmp_path / "base.png",
        size=(120, 240),
        color=(0, 0, 0, 255),
    )

    floating_path = make_image(
        tmp_path / "banner.png",
        size=(20, 10),
        color=(255, 0, 0, 255),
    )

    output_path = tmp_path / "output.png"

    add_top_centered_image(
        base_path,
        floating_path,
        output_path,
    )

    expected_y = 240 // 12

    assert get_pixel(
        output_path,
        50,
        expected_y,
    ) == (255, 0, 0, 255)


# ~~~~~ PANORAMA SPLITTING ~~~~~

def test_split_panorama_creates_one_slice_per_width(tmp_path):
    panorama_path = make_image(
        tmp_path / "panorama.png",
        size=(300, 50),
        color=(10, 20, 30, 255),
    )

    paths = split_panorama(
        panorama_path,
        tmp_path,
        "a",
        [100, 100, 100],
    )

    assert len(paths) == 3

    for path in paths:
        assert path.exists()


def test_split_panorama_uses_requested_widths(tmp_path):
    panorama_path = make_image(
        tmp_path / "panorama.png",
        size=(450, 50),
        color=(10, 20, 30, 255),
    )

    paths = split_panorama(
        panorama_path,
        tmp_path,
        "b",
        [100, 150, 200],
    )

    sizes = []

    for path in paths:
        image = Image.open(path)
        sizes.append(image.size)
        image.close()

    assert sizes == [
        (100, 50),
        (150, 50),
        (200, 50),
    ]


def test_split_panorama_preserves_left_to_right_content(tmp_path):
    panorama = Image.new(
        "RGBA",
        (300, 20),
        (0, 0, 0, 255),
    )

    for x in range(0, 100):
        for y in range(20):
            panorama.putpixel((x, y), (255, 0, 0, 255))

    for x in range(100, 200):
        for y in range(20):
            panorama.putpixel((x, y), (0, 255, 0, 255))

    for x in range(200, 300):
        for y in range(20):
            panorama.putpixel((x, y), (0, 0, 255, 255))

    panorama_path = tmp_path / "panorama.png"
    panorama.save(panorama_path)
    panorama.close()

    paths = split_panorama(
        panorama_path,
        tmp_path,
        "a",
        [100, 100, 100],
    )

    assert get_pixel(paths[0], 50, 10) == (255, 0, 0, 255)
    assert get_pixel(paths[1], 50, 10) == (0, 255, 0, 255)
    assert get_pixel(paths[2], 50, 10) == (0, 0, 255, 255)


def test_split_panorama_rejects_wrong_total_width(tmp_path):
    panorama_path = make_image(
        tmp_path / "panorama.png",
        size=(300, 50),
        color=(0, 0, 0, 255),
    )

    with pytest.raises(
        ValueError,
        match="configured monitors require 250px",
    ):
        split_panorama(
            panorama_path,
            tmp_path,
            "a",
            [100, 150],
        )


# ~~~~~ WALLPAPER COMPOSITION ~~~~~

def test_compose_wallpaper_uses_first_valid_layer_as_base(tmp_path):
    base_path = make_image(
        tmp_path / "base.png",
        size=(100, 100),
        color=(0, 0, 255, 255),
    )

    output_path = tmp_path / "output.png"

    result = compose_wallpaper(
        [base_path],
        output_path,
    )

    assert result == output_path
    assert output_path.exists()

    assert get_pixel(output_path, 50, 50) == (0, 0, 255, 255)


def test_compose_wallpaper_skips_missing_layers(tmp_path):
    base_path = make_image(
        tmp_path / "base.png",
        size=(100, 100),
        color=(0, 0, 255, 255),
    )

    missing_path = tmp_path / "missing.png"

    output_path = tmp_path / "output.png"

    compose_wallpaper(
        [
            missing_path,
            base_path,
            None,
        ],
        output_path,
    )

    assert get_pixel(output_path, 50, 50) == (0, 0, 255, 255)


def test_compose_wallpaper_raises_when_no_valid_layers(tmp_path):
    with pytest.raises(
        FileNotFoundError,
        match="No valid image layers were provided",
    ):
        compose_wallpaper(
            [
                None,
                tmp_path / "missing.png",
            ],
            tmp_path / "output.png",
        )


def test_compose_wallpaper_resizes_overlay_to_base(tmp_path):
    base_path = make_image(
        tmp_path / "base.png",
        size=(100, 100),
        color=(0, 0, 255, 255),
    )

    overlay_path = make_image(
        tmp_path / "overlay.png",
        size=(10, 10),
        color=(255, 0, 0, 255),
    )

    output_path = tmp_path / "output.png"

    compose_wallpaper(
        [
            base_path,
            overlay_path,
        ],
        output_path,
    )

    assert get_pixel(output_path, 99, 99) == (255, 0, 0, 255)


def test_compose_wallpaper_respects_layer_order(tmp_path):
    base_path = make_image(
        tmp_path / "base.png",
        size=(50, 50),
        color=(0, 0, 255, 255),
    )

    middle_path = make_image(
        tmp_path / "middle.png",
        size=(50, 50),
        color=(0, 255, 0, 255),
    )

    top_path = make_image(
        tmp_path / "top.png",
        size=(50, 50),
        color=(255, 0, 0, 255),
    )

    output_path = tmp_path / "output.png"

    compose_wallpaper(
        [
            base_path,
            middle_path,
            top_path,
        ],
        output_path,
    )

    assert get_pixel(output_path, 25, 25) == (255, 0, 0, 255)


def test_compose_wallpaper_can_add_moon(tmp_path):
    base_path = make_image(
        tmp_path / "base.png",
        size=(100, 100),
        color=(0, 0, 0, 255),
    )

    moon_path = make_image(
        tmp_path / "moon.png",
        size=(10, 10),
        color=(255, 255, 255, 255),
    )

    output_path = tmp_path / "output.png"

    compose_wallpaper(
        [base_path],
        output_path,
        moon_path=moon_path,
        moon_position=(20, 30),
    )

    assert get_pixel(output_path, 20, 30) == (255, 255, 255, 255)