def get_moon_global_position(bucket):
    positions = {
        "sunset_45": (200, 850),
        "sunset_60": (600, 650),
        "blue_hour": (1100, 400),

        "dusk": (1700, 120),
        "deep_twilight": (2100, -250),
        "night": (2600, -650),
        "deep_night": (3100, -720),
        "pre_dawn": (3600, -350),

        "sunrise_-60": (4400, 200),
        "sunrise_-45": (5000, 500),
    }

    return positions.get(bucket)