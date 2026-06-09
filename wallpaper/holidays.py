import datetime

# Calculate the holidays that aren't on a set date each year
def calculate_easter(year):
    # Anonymous Gregorian algorithm (Computus)
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return datetime.date(year, month, day)

def second_sunday_of_may(year):
    # Start with the first day of May
    first_of_may = datetime.date(year, 5, 1)
    
    # Find the day of the week for May 1st (0 is Monday, 6 is Sunday)
    day_of_week = first_of_may.weekday()
    
    # Calculate how many days to add to get to the first Sunday
    days_until_first_sunday = (6 - day_of_week) % 7
    
    # Calculate the date of the first Sunday
    first_sunday = first_of_may + datetime.timedelta(days=days_until_first_sunday)
    
    # The second Sunday will be exactly one week after the first Sunday
    second_sunday = first_sunday + datetime.timedelta(days=7)
    
    # Return just the day of the month
    return second_sunday.day

def third_sunday_of_june(year):
    # Start with the first day of May
    first_of_june = datetime.date(year, 6, 1)
    
    # Find the day of the week for May 1st (0 is Monday, 6 is Sunday)
    day_of_week = first_of_june.weekday()
    
    # Calculate how many days to add to get to the first Sunday
    days_until_first_sunday = (6 - day_of_week) % 7
    
    # Calculate the date of the first Sunday
    first_sunday = first_of_june + datetime.timedelta(days=days_until_first_sunday)
    
    # The second Sunday will be exactly one week after the first Sunday
    third_sunday = first_sunday + datetime.timedelta(days=14)
    
    # Return just the day of the month
    return third_sunday.day

def fourth_thursday_of_november(year):
    # Start with the first day of November
    first_of_november = datetime.date(year, 11, 1)
    
    # Find the day of the week for November 1st (0 is Monday, 6 is Sunday)
    day_of_week = first_of_november.weekday()
    
    # Calculate how many days to add to get to the first Thursday
    # If November 1st is a Thursday (day_of_week == 3), we need to add 0 days, otherwise,
    # we add the necessary days to reach the upcoming Thursday
    days_until_first_thursday = (3 - day_of_week) % 7
    
    # Calculate the date of the first Thursday
    first_thursday = first_of_november + datetime.timedelta(days=days_until_first_thursday)
    
    # The fourth Thursday will be exactly three weeks after the first Thursday
    fourth_thursday = first_thursday + datetime.timedelta(days=21)
    
    # Return just the day of the month
    return fourth_thursday.day

def get_holiday(day, month, year):

    # Easter
    easter_date = calculate_easter(year)
    if month == easter_date.month and day == easter_date.day:
        return 'easter'       
    # January
    if month == 1:
        # New Year's Day
        if day == 1:
            return 'new_years_day'
    # February
    if month == 2:
        # Valentine's Day
        if day == 14:
            return 'valentines'
    # March
    if month == 3:
        # St. Patrick's Day
        if day == 17:
            return 'st_patricks_day'
    # April
    if month == 4:
        # April Fool's Day
        if day == 1:
            return 'april_fools'
    # May
    if month == 5:
        # 2nd Sunday (Mother's Day)
        if day == second_sunday_of_may(year):
            return 'mothers_day'
        # Cinco de Mayo
        if day == 5:
            return 'cinco_de_mayo'        
    # June
    if month == 6:
        # 3rd Sunday (Father's Day)
        if day == third_sunday_of_june(year):
            return 'fathers_day'  
        # Juneteenth
        if day == 19:
            return 'juneteenth'   
    # July
    if month == 7:
        # Fourth of July (Independence Day)
        if day == 4:
            return 'fourth_of_july'
    # August
    # September
    # October
    if month == 10:
        if day == 31:
            return 'halloween'
    # November
    if month == 11:
        # Dia de los Muertos
        if day == 1:
            return 'dia_de_los_muertos'
        # Thanksgiving
        if day == fourth_thursday_of_november(year):
            return 'thanksgiving'
    # December
    if month == 12:
        if day == 24:
            return 'christmas_eve'
        if day == 25:
            return 'christmas_day'
        if day == 31:
            return 'new_years_eve'   
    return 'none'