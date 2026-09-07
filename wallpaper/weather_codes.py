# WMO weather codes used by Open-Meteo.
# Rain, snow, and cloud coverage come from the actual current values.
# These codes add context that those numbers cannot describe by themselves.

WEATHER_CODES = {
    # Clear / cloud conditions
    0: {
        "description": "Clear sky",
        "cloud_type": "normal",
    },
    1: {
        "description": "Mainly clear",
        "cloud_type": "normal",
    },
    2: {
        "description": "Partly cloudy",
        "cloud_type": "normal",
    },
    3: {
        "description": "Overcast",
        "cloud_type": "normal",
    },

    # Fog
    45: {
        "description": "Fog",
        "cloud_type": "normal",
        "atmosphere": "fog",
    },
    48: {
        "description": "Rime fog",
        "cloud_type": "normal",
        "atmosphere": "fog",
    },

    # Drizzle
    51: {
        "description": "Light drizzle",
        "cloud_type": "normal",
    },
    53: {
        "description": "Drizzle",
        "cloud_type": "normal",
    },
    55: {
        "description": "Heavy drizzle",
        "cloud_type": "normal",
    },

    # Freezing drizzle
    # It can use the regular rain artwork while falling. Ice buildup can
    # become a separate environment effect later.
    56: {
        "description": "Light freezing drizzle",
        "cloud_type": "normal",
        "freezing_precipitation": True,
    },
    57: {
        "description": "Freezing drizzle",
        "cloud_type": "normal",
        "freezing_precipitation": True,
    },

    # Rain
    61: {
        "description": "Light rain",
        "cloud_type": "normal",
    },
    63: {
        "description": "Rain",
        "cloud_type": "normal",
    },
    65: {
        "description": "Heavy rain",
        "cloud_type": "normal",
    },

    # Freezing rain
    66: {
        "description": "Light freezing rain",
        "cloud_type": "normal",
        "freezing_precipitation": True,
    },
    67: {
        "description": "Freezing rain",
        "cloud_type": "normal",
        "freezing_precipitation": True,
    },

    # Snow
    71: {
        "description": "Light snow",
        "cloud_type": "normal",
    },
    73: {
        "description": "Snow",
        "cloud_type": "normal",
    },
    75: {
        "description": "Heavy snow",
        "cloud_type": "normal",
    },
    77: {
        "description": "Snow grains",
        "cloud_type": "normal",
    },

    # Rain showers
    80: {
        "description": "Light rain showers",
        "cloud_type": "normal",
    },
    81: {
        "description": "Rain showers",
        "cloud_type": "normal",
    },
    82: {
        "description": "Heavy rain showers",
        "cloud_type": "normal",
    },

    # Snow showers
    85: {
        "description": "Light snow showers",
        "cloud_type": "normal",
    },
    86: {
        "description": "Heavy snow showers",
        "cloud_type": "normal",
    },

    # Thunderstorms
    # Cloud coverage still controls how much of the sky is covered. Storm type
    # swaps in the darker thundercloud artwork, and this flag adds lightning.
    95: {
        "description": "Thunderstorm",
        "cloud_type": "storm",
        "thunderstorm": True,
    },
    96: {
        "description": "Thunderstorm with hail",
        "cloud_type": "storm",
        "thunderstorm": True,
        "hail": True,
    },
    99: {
        "description": "Thunderstorm with heavy hail",
        "cloud_type": "storm",
        "thunderstorm": True,
        "hail": True,
    },
}