

def add_weather_overlay(image_path, weather_data, output_path):
    """Simple top-monitor text overlay. Safe no-op if Pillow is unavailable."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        #debug_log("Pillow not installed; skipping weather overlay.")
        return image_path

    img = Image.open(image_path).convert("RGBA")
    draw = ImageDraw.Draw(img)

    temp = weather_data.get("main", {}).get("temp")
    weather_items = weather_data.get("weather") or [{}]
    description = weather_items[0].get("description", "").title()

    lines = []
    if temp is not None:
        lines.append(f"{round(temp)}°")
    if description:
        lines.append(description)

    if not lines:
        return image_path

    try:
        font_big = ImageFont.truetype("arial.ttf", 84)
        font_small = ImageFont.truetype("arial.ttf", 38)
    except Exception:
        font_big = ImageFont.load_default()
        font_small = ImageFont.load_default()

    x = 60
    y = 80
    padding = 26
    box_w = 420
    box_h = 170
    draw.rounded_rectangle(
        [x - padding, y - padding, x + box_w, y + box_h],
        radius=28,
        fill=(0, 0, 0, 90),
    )
    draw.text((x, y), lines[0], font=font_big, fill=(255, 255, 255, 235))
    if len(lines) > 1:
        draw.text((x + 6, y + 95), lines[1], font=font_small, fill=(255, 255, 255, 220))

    img.save(output_path)
    return output_path