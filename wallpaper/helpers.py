def layer_fingerprint(layer_paths):
    # Reduce the resolved artwork for one monitor group to something cheap
    # and serializable that I can compare on the next run.
    return [str(path) for path in layer_paths]


def weather_overlay_fingerprint(weather_data):
    # Track only weather values that actually appear in the top-monitor overlay.
    temp = weather_data.get("main", {}).get("temp")
    weather_items = weather_data.get("weather") or [{}]
    description = weather_items[0].get("description", "").title()

    # Match the formatting in add_weather_overlay(), including rounding the
    # temperature. A change from 71.1 to 71.4 should not trigger an update if
    # both are still displayed as 71°.
    return {
        "temp": round(temp) if temp is not None else None,
        "description": description,
    }


def next_output_slot(previous_slot):
    # Alternate between A/B output files.
    # Windows may still be displaying the current wallpaper file, so I do not
    # overwrite it underneath Explorer. The new image is composed into the
    # inactive file first and Windows is switched to it afterward.
    return "b" if previous_slot == "a" else "a"