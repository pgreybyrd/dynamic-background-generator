# Get the season based on the month. This assumes season PNG filenames match these names.
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