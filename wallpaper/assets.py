def optional_layer(path):
    """Return a layer path only when the file exists, otherwise skip it."""
    return path if path and path.exists() else None


def get_layer_paths(bucket, stars, moon, season, holiday, weather, shade, assets_dir, layout="one_monitor"):
    layers = []

    sky_path = assets_dir / "sky" / layout / f"{bucket}.png"
    stars_path = assets_dir / "stars" / layout / f"{stars}.png"
    weather_path = assets_dir / "weather" / layout / f"{weather}.png"
    moon_path = assets_dir / "moon" / layout / f"{moon}.png"

    layers.append(optional_layer(sky_path))
    layers.append(optional_layer(stars_path))
    layers.append(optional_layer(moon_path))

    if layout == "vertical":
        holiday_path = assets_dir / "holiday" / "vertical" / f"{holiday}.png" if holiday != "none" else None

        layers.extend([
            optional_layer(weather_path),
            optional_layer(holiday_path),
            optional_layer(moon_path),
            # ui overlay later
        ])

    else:
        season_path = assets_dir / "season" / layout / f"{season}.png"
        holiday_path = assets_dir / "holiday" / layout / f"{holiday}.png" if holiday != "none" else None
        shade_path = assets_dir / "shade" / layout / f"{shade}.png" if shade != "none" else None
        holiday_lights_path = assets_dir / "holiday_lights" / layout / f"{holiday}.png" if holiday != "none" else None
        moon_path = assets_dir / "moon" / layout / f"{moon}.png"

        layers.extend([
            optional_layer(season_path),
            optional_layer(holiday_path),
            optional_layer(weather_path),
            optional_layer(moon_path),
            optional_layer(shade_path),
            optional_layer(holiday_lights_path),
        ])

    return layers