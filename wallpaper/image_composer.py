# ~~~~~ IMPORTS ~~~~~
from pathlib import Path
from PIL import Image
# ~~~~~ END IMPORTS ~~~~~

# ~~~~~ FUNCTIONS ~~~~~
def compose_wallpaper(layer_paths, output_path):
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

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    base.save(output_path)

    return output_path
# ~~~~~ END FUNCTIONS ~~~~~