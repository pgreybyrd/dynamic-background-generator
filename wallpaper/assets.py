def optional_layer(path):
    # Return a layer path only when the file exists, otherwise skip it.
    return path if path and path.exists() else None


def weather_layer_path(assets_dir, effect, layout, variant, subtype=None):
    """
    Build a weather artwork path without making get_layer_paths unreadable.
    """
    if not variant or variant == "none":
        return None

    path = assets_dir / "weather" / "active" / effect

    if subtype:
        path = path / subtype

    return path / layout / f"{variant}.png"


def get_layer_paths(
    bucket,
    stars,
    moon,
    season,
    holiday,
    weather,
    shade,
    banner,
    assets_dir,
    layout="horizontal",
    ):

    layers = []

    # Base scene
    sky_path = assets_dir / "sky" / layout / f"{bucket}.png"
    stars_path = assets_dir / "stars" / layout / f"{stars}.png"
    landscape_path = assets_dir / "landscape" / layout / "base.png"
    moon_path = assets_dir / "moon" / layout / f"{moon}.png"

    season_path = assets_dir / "season" / layout / f"{season}.png"

    holiday_path = (
        assets_dir / "holiday" / layout / f"{holiday}.png"
        if holiday != "none"
        else None
    )

    shade_path = (
        assets_dir / "shade" / layout / f"{shade}.png"
        if shade != "none"
        else None
    )

    holiday_lights_path = (
        assets_dir / "holiday_lights" / layout / f"{holiday}.png"
        if holiday != "none"
        else None
    )

    banner_path = (
        assets_dir / "banners" / f"{banner}.png"
        if banner != "none"
        else None
    )

    # Weather
    cloud_info = weather.get("clouds", {})
    cloud_type = cloud_info.get("type", "normal")
    cloud_coverage = cloud_info.get("coverage", "none")

    clouds_path = weather_layer_path(
        assets_dir,
        "clouds",
        layout,
        cloud_coverage,
        subtype=cloud_type,
    )

    rain_path = weather_layer_path(
        assets_dir,
        "rain",
        layout,
        weather.get("rain", "none"),
    )

    snow_path = weather_layer_path(
        assets_dir,
        "snow",
        layout,
        weather.get("snow", "none"),
    )

    atmosphere_path = weather_layer_path(
        assets_dir,
        "atmosphere",
        layout,
        weather.get("atmosphere", "none"),
    )

    lightning_path = (
        assets_dir
        / "weather"
        / "active"
        / "lightning"
        / layout
        / "lightning.png"
        if weather.get("thunderstorm", False)
        else None
    )

    candidate_layers = [
        optional_layer(sky_path),
        optional_layer(stars_path),
        optional_layer(moon_path),

        optional_layer(landscape_path),
        optional_layer(season_path),

        optional_layer(clouds_path),

        optional_layer(holiday_path),
        optional_layer(shade_path),

        optional_layer(atmosphere_path),

        optional_layer(rain_path),
        optional_layer(snow_path),

        optional_layer(lightning_path),
        optional_layer(holiday_lights_path),
    ]

    # Missing optional artwork resolves to None. Keep those placeholders out of
    # the final layer list so everything downstream only sees artwork that exists.
    layers.extend(
        layer
        for layer in candidate_layers
        if layer is not None
    )

    return {
        "layers": layers,
        "banner": optional_layer(banner_path),
    }