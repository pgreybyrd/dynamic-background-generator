# ~~~~~ IMPORTS ~~~~~
from pathlib import Path
from PIL import Image
# ~~~~~ END IMPORTS ~~~~~

# ~~~~~ FUNCTIONS ~~~~~
def add_floating_image(base_path, floating_path, output_path, position):
    from pathlib import Path
    from PIL import Image

    base = Image.open(base_path).convert("RGBA")
    floating = Image.open(floating_path).convert("RGBA")

    base.alpha_composite(floating, position)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    base.save(output_path)

    return output_path


def add_top_centered_image(base_path, floating_path, output_path):
    # Center a floating image across the top portion of whatever canvas it is on.
    base = Image.open(base_path)
    floating = Image.open(floating_path)

    x = (base.width - floating.width) // 2
    y = base.height // 12

    base.close()
    floating.close()

    return add_floating_image(
        base_path,
        floating_path,
        output_path,
        (x, y)
    )


def split_panorama(path, output_dir, slot):
    img = Image.open(path).convert("RGBA")

    left = img.crop((0, 0, 1920, 1080))
    middle = img.crop((1920, 0, 3840, 1080))
    right = img.crop((3840, 0, 5760, 1080))

    left_path = output_dir / f"bottom_left_{slot}.png"
    middle_path = output_dir / f"bottom_middle_{slot}.png"
    right_path = output_dir / f"bottom_right_{slot}.png"

    left.save(left_path)
    middle.save(middle_path)
    right.save(right_path)

    return left_path, middle_path, right_path


def compose_wallpaper(layer_paths, output_path, moon_path=None, moon_position=None):
    valid_layers = [Path(path) for path in layer_paths if path and Path(path).exists()]

    # DEBUG
    #valid_layers = []
    #
    #for path in layer_paths:
    #    if not path:
    #        print("no holiday layer")
    #        continue
    #
    #    path = Path(path)
    #
    #    if path.exists():
    #        print(f"Found layer: {path}")
    #        valid_layers.append(path)
    #    else:
    #        print(f"Missing layer: {path}")

    if not valid_layers:
        raise FileNotFoundError("No valid image layers were provided.")

    base = Image.open(valid_layers[0]).convert("RGBA")

    for layer_path in valid_layers[1:]:
        layer = Image.open(layer_path).convert("RGBA")

        if layer.size != base.size:
            layer = layer.resize(base.size)

        base.alpha_composite(layer)

    if moon_path and moon_position:
        moon = Image.open(moon_path).convert("RGBA")
        base.alpha_composite(moon, moon_position)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    base.save(output_path)

    return output_path
# ~~~~~ END FUNCTIONS ~~~~~