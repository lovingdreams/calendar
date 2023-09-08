import pytz
from datetime import datetime


def get_Time_Zone(date, staff_timeZone, booking_timeZone):
    currentZone = booking_timeZone
    convert_time = staff_timeZone
    date = date
    time_zone = convert_time
    compain_time = datetime.strptime(f"{date}", "%Y-%m-%d %H:%M")
    indian_timezone = pytz.timezone(currentZone)
    indian_time = indian_timezone.localize(compain_time)
    utc = indian_time.astimezone(pytz.utc)
    american_timezone = pytz.timezone(time_zone)
    american_time = utc.astimezone(american_timezone)
    american_time_formatted = american_time.strftime("%Y-%m-%d %H:%M")
    print("american_time_formatted-->", american_time_formatted)
    american_time_formatted = datetime.strptime(
        american_time_formatted, "%Y-%m-%d %H:%M"
    )
    return american_time_formatted


date = "2023-01-11 07:30"
staff_timeZone = "Asia/Kolkata"
booking_timeZone = "America/New_York"
value = get_Time_Zone(date, staff_timeZone, booking_timeZone)
print(value)
print(type(value))
