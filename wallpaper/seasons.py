# Get the season
# def get_season(month, debug=False, debug_season_override=None):
#     if debug and debug_season_override is not None:
#         return debug_season_override
#     if month in (3, 4, 5):
#         return "spring"
#     if month in (6, 7, 8):
#         return "summer"
#     if month in (9, 10, 11):
#         return "autumn"
#     return "winter"

def get_season(month):
    if month == 3:
        return "early_spring"
    if month == 4:
        return "mid_spring"
    if month == 5:
        return "late_spring"
    if month == 6:
        return "early_summer"
    if month == 7:
        return "mid_summer"
    if month == 8:
        return "late_summer"
    if month == 9:
        return "early_autumn"
    if month == 10:
        return "mid_autumn"
    if month == 11:
        return "late_autumn"
    if month == 12:
        return "early_winter"
    if month == 1:
        return "mid_winter"
    if month == 2:
        return "late_winter"