def optional_layer(path):
    # Return a layer path only when the file exists, otherwise skip it.
    return path if path and path.exists() else None

# Build the ordered list of artwork layers for the requested monitor layout.
# Missing optional art just gets skipped instead of breaking the wallpaper.
def get_layer_paths(bucket, stars, moon, season, holiday, weather, shade, astronomical_event, assets_dir, layout="one_monitor"):
    layers = []

    # These are shared by every layout.
    sky_path = assets_dir / "sky" / layout / f"{bucket}.png"
    stars_path = assets_dir / "stars" / layout / f"{stars}.png"
    weather_path = assets_dir / "weather" / layout / f"{weather}.png"
    moon_path = assets_dir / "moon" / layout / f"{moon}.png"
    astronomical_event_path = (assets_dir / "astronomical_events" / f"{astronomical_event}.png"
                               if astronomical_event != "none"
                               else None)

    layers.append(optional_layer(sky_path))
    layers.append(optional_layer(stars_path))
    layers.append(optional_layer(moon_path))

    if layout == "vertical":
        # The portrait monitor has its own simpler stack for now.
        holiday_path = (assets_dir / "holiday" / "vertical" / f"{holiday}.png" 
                        if holiday != "none" 
                        else None)

        layers.extend([
            optional_layer(weather_path),
            optional_layer(holiday_path),
            # Weather/UI overlay gets added after the artwork is composed.
        ])

    else:
        # Horizontal layouts also get seasonal landscape shading and holiday lights.
        season_path = assets_dir / "season" / layout / f"{season}.png"
        holiday_path = assets_dir / "holiday" / layout / f"{holiday}.png" if holiday != "none" else None
        shade_path = assets_dir / "shade" / layout / f"{shade}.png" if shade != "none" else None
        holiday_lights_path = assets_dir / "holiday_lights" / layout / f"{holiday}.png" if holiday != "none" else None

        layers.extend([
            optional_layer(season_path),
            optional_layer(holiday_path),
            optional_layer(weather_path),
            optional_layer(shade_path),
            optional_layer(holiday_lights_path),
        ])

    return {
        "layers": layers,
        "astronomical_event": optional_layer(astronomical_event_path),
    }