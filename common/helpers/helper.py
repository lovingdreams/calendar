from rest_framework import status
from rest_framework.response import Response
from dateutil.parser import parse
from datetime import timedelta
from calendars.serializers import *
import pytz
from datetime import datetime

from datetime import datetime

from common.configs.config import config as cfg
from BaseWorke.middlewares.new_relic_middleware import get_logger
import requests
from calendars.models import WorkingHour


logger = get_logger()

# import datetime
import calendar

expected_format = "%Y-%m-%d"


def check_week(week):
    date_str = week
    date_obj = parse(date_str)

    day_of_week = date_obj.weekday()
    import calendar

    day_name = calendar.day_name[day_of_week]
    return day_name


def available(date, working_hour):
    date = check_week(date).upper()
    day = date
    data = working_hour.working_hours
    for obj in data:
        if day == obj["days"]:
            return obj["status"]


def check_working_hours(week, workinghours):
    output = []
    day = week
    data = workinghours.working_hours
    for obj in data:
        if day == obj["days"]:
            for slot in obj["slots"]:
                value = (
                    datetime.strptime(slot[0], "%H:%M").time(),
                    datetime.strptime(slot[1], "%H:%M").time(),
                )
                output.append(value)
                output = sorted(output, key=lambda x: x[0])
    return output


def getGenerate_Booking_slot(
    workinghours, date, duration, queryset, user_time, time_zone
):
    day = check_week(date).upper()
    output = check_working_hours(day, workinghours)
    today_date = date
    date = datetime.strptime(date, "%Y-%m-%d")
    slots = []
    user_time = datetime.strptime(user_time, "%H:%M")
    user_time = user_time.time()
    val = datetime.combine(date, user_time)
    user_time = get_Time_Zone(val, workinghours.time_zone, time_zone)
    user_time_duration = (user_time + timedelta(minutes=duration)).time()
    date = user_time
    user_time = user_time.time()
    for working_hour_start, working_hour_end in output:
        if working_hour_start <= user_time < user_time_duration <= working_hour_end:
            st = datetime.combine(date, working_hour_start)
            for booking in queryset:
                booking_start_time = datetime.strptime(
                    booking.start_time, "%H:%M"
                ).time()
                booking_end_time = datetime.strptime(booking.end_time, "%H:%M").time()

                if booking.date == str(date.date()):
                    if (
                        user_time >= booking_start_time and user_time < booking_end_time
                    ) or (
                        user_time_duration > booking_start_time
                        and user_time_duration <= booking_end_time
                    ):
                        return False
    user_stat_time = datetime.combine(date, user_time)
    user_end_time = datetime.combine(date, user_time_duration)
    booking_start_time = get_Time_Zone(
        user_stat_time, time_zone, workinghours.time_zone
    )
    booking_end_time = get_Time_Zone(user_end_time, time_zone, workinghours.time_zone)
    print("booking_end_time---->", booking_end_time)
    date = get_Time_Zone(booking_start_time, workinghours.time_zone, time_zone)
    value = {
        "date": date.date(),
        "start": user_time,
        "end": user_time_duration,
        "user_start_time": booking_start_time,
        "user_end_time": booking_end_time,
    }
    return value


def getGenerate_openapi_slot(
    workinghours, date, duration, slot_duration, Bookings, time_zone
):
    date_convert_datetime = get_default_datetime(date)
    inda_working = get_Time_Zone(
        date_convert_datetime, workinghours.time_zone, time_zone
    )
    indan_working_1 = inda_working + timedelta(days=1)

    output = check_working_hours_staff(inda_working, workinghours, indan_working_1)

    user_date = date
    slots = []

    for working_hour_start, working_hour_end in output:
        slot_start = working_hour_start
        slot_end = slot_start + timedelta(minutes=duration)
        print(slot_start)

        while slot_end <= working_hour_end:
            available = True
            extra_duration = slot_start + timedelta(minutes=slot_duration)

            for booking in Bookings:
                booking_start_time = datetime.combine(
                    working_hour_start.date(),
                    datetime.strptime(booking.start_time, "%H:%M").time(),
                )
                booking_end_time = datetime.combine(
                    working_hour_start.date(),
                    datetime.strptime(booking.end_time, "%H:%M").time(),
                )
                if duration >= slot_duration:
                    if booking.date == str(working_hour_start.date()):
                        if (
                            slot_start >= booking_start_time
                            and slot_start < booking_end_time
                        ) or (
                            slot_end > booking_start_time
                            and slot_end <= booking_end_time
                        ):
                            available = False
                            slots.append(
                                {
                                    "start_time": get_Time_Zone(
                                        slot_start, time_zone, workinghours.time_zone
                                    ),
                                    "end_time": get_Time_Zone(
                                        extra_duration,
                                        time_zone,
                                        workinghours.time_zone,
                                    ),
                                    "slot_status": available,
                                }
                            )
                            break
                else:
                    if booking.date == str(working_hour_start.date()):
                        if (
                            slot_start + timedelta(minutes=duration)
                            >= booking_start_time
                            and slot_start + timedelta(minutes=duration)
                            <= booking_end_time
                        ) or (
                            extra_duration > booking_start_time
                            and extra_duration <= booking_end_time
                        ):
                            available = False
                            slots.append(
                                {
                                    "start_time": get_Time_Zone(
                                        slot_start,
                                        time_zone,
                                        workinghours.time_zone,
                                    ),
                                    "end_time": get_Time_Zone(
                                        extra_duration,
                                        time_zone,
                                        workinghours.time_zone,
                                    ),
                                    "slot_status": available,
                                }
                            )
                            break

            else:
                slots.append(
                    {
                        "start_time": get_Time_Zone(
                            slot_start, time_zone, workinghours.time_zone
                        ),
                        "end_time": get_Time_Zone(
                            extra_duration, time_zone, workinghours.time_zone
                        ),
                        "slot_status": available,
                    }
                )
            slot_start = slot_end + timedelta()
            slot_end = slot_start + timedelta(minutes=duration)
            # else:
            #     break
    return slots


def get_Time_Zone(date, staff_timeZone, booking_timeZone):
    currentZone = booking_timeZone
    convert_time = staff_timeZone
    date = date
    time_zone = convert_time
    compain_time = datetime.strptime(f"{date}", "%Y-%m-%d %H:%M:%S")
    indian_timezone = pytz.timezone(currentZone)
    indian_time = indian_timezone.localize(compain_time)
    utc = indian_time.astimezone(pytz.utc)
    american_timezone = pytz.timezone(time_zone)
    american_time = utc.astimezone(american_timezone)
    american_time_formatted = american_time.strftime("%Y-%m-%d %H:%M:%S")
    american_time_formatted = datetime.strptime(
        american_time_formatted, "%Y-%m-%d %H:%M:%S"
    )
    return american_time_formatted


def get_Time_Zone_T(date, staff_timeZone, booking_timeZone):
    currentZone = booking_timeZone
    convert_time = staff_timeZone
    date = date
    time_zone = convert_time
    compain_time = datetime.strptime(f"{date}", "%Y-%m-%d %H:%M:%S")
    indian_timezone = pytz.timezone(currentZone)
    indian_time = indian_timezone.localize(compain_time)
    utc = indian_time.astimezone(pytz.utc)
    american_timezone = pytz.timezone(time_zone)
    american_time = utc.astimezone(american_timezone)
    american_time_formatted = american_time.strftime("%Y-%m-%d %H:%M:%S")
    original_format = "%Y-%m-%dT%H:%M:%S"
    desired_format = "%Y-%m-%dT%H:%M:%S"
    original_datetime = datetime.strptime(american_time_formatted, original_format)
    converted_datetime_string = original_datetime.strftime(desired_format)
    print("converted_datetime_string----->", converted_datetime_string)
    return converted_datetime_string


def get_default_datetime(date):
    date_format = "%Y-%m-%d"
    datetime_format = "%Y-%m-%d %H:%M:%S"
    converted_date = datetime.strptime(date, date_format)
    formatted_date = converted_date.strftime(datetime_format)
    converted_date = datetime.strptime(formatted_date, datetime_format)
    print(converted_date)
    return converted_date


def check_working_hours_staff(indan_working, workinghours, indan_working_1):
    week1 = str(indan_working.date())
    week2 = str(indan_working_1.date())
    day = [check_week(week1).upper(), check_week(week2).upper()]
    output = []
    data = workinghours.working_hours
    for obj in data:
        if obj["days"] == day[0]:
            for slot in obj["slots"]:
                start_time = datetime.strptime(slot[0], "%H:%M").time()
                end_time = datetime.strptime(slot[1], "%H:%M").time()
                if indan_working.time() <= end_time:
                    if indan_working.time() > start_time:
                        start_time = indan_working.time()
                    start = datetime.combine(indan_working.date(), start_time)
                    end = datetime.combine(indan_working.date(), end_time)
                    value = (start, end)

                    output.append(value)
                output = sorted(output, key=lambda x: x[0])
        elif obj["days"] == day[1]:
            for slot in obj["slots"]:
                start_time = datetime.strptime(slot[0], "%H:%M").time()
                end_time = datetime.strptime(slot[1], "%H:%M").time()
                if indan_working_1.time() >= start_time:
                    if indan_working_1.time() < end_time:
                        end_time = indan_working_1.time()

                    start = datetime.combine(indan_working_1.date(), start_time)
                    end = datetime.combine(indan_working_1.date(), end_time)
                    value = (start, end)

                    output.append(value)
                output = sorted(output, key=lambda x: x[0])
    print("output--->", output)

    return output


def get_month_find(date):
    import calendar

    year, month, _ = date.split("-")
    last_day = calendar.monthrange(int(year), int(month))[1]
    last_full_date = f"{year}-{month}-{last_day}"
    return last_full_date


def Return400Error(message, data=[]):
    return Response(
        {"status": 400, "message": message, "data": data},
        status=status.HTTP_400_BAD_REQUEST,
    )


def block_day_off(day_off, slots):
    val = f"{day_off.start_date}T{day_off.start_time}"
    val2 = f"{day_off.end_date}T{day_off.end_time}"
    block_start_time = datetime.strptime(val, "%Y-%m-%dT%H:%M")
    block_end_time = datetime.strptime(val2, "%Y-%m-%dT%H:%M")

    # Iterate through the slots and block the relevant ones
    print(len(slots))
    for slot in slots:
        print(slot)
        start_time = slot["start_time"]
        end_time = slot["end_time"]

        if (
            block_start_time <= start_time + timedelta(minutes=1) <= block_end_time
            or block_start_time <= end_time - timedelta(minutes=1) <= block_end_time
        ):
            slot["slot_status"] = False
    print(slots)
    return slots

    # Print the updated slots
    # print(slots)


def get_default_working_hours():
    return [
        {"days": "MONDAY", "status": True, "slots": [["09:00", "17:00"]]},
        {"days": "TUESDAY", "status": True, "slots": [["09:00", "17:00"]]},
        {"days": "WEDNESDAY", "status": True, "slots": [["09:00", "17:00"]]},
        {"days": "THURSDAY", "status": True, "slots": [["09:00", "17:00"]]},
        {"days": "FRIDAY", "status": True, "slots": [["09:00", "17:00"]]},
        {"days": "SATURDAY", "status": False, "slots": [["09:00", "17:00"]]},
        {"days": "SUNDAY", "status": False, "slots": [["09:00", "17:00"]]},
    ]


def getuserdetails(staff_id, token):
    try:
        url = cfg.get("grpc", "USER_HTTP_REQUEST") + f"{staff_id}/"
        headers = {"Authorization": token}
        logger.info(f"url --->{url}")
        logger.info(f"headers --->{headers}")
        staff_info_api_response = requests.get(url, headers=headers)
        logger.info(f"staff_info_api_response ---> {staff_info_api_response}")
        response_json = staff_info_api_response.json()
        logger.info(f"response_json ---> {response_json}")
        return response_json
    except Exception as err:
        logger.info(f"Http Error----->{err}")
        return str(err)


def auto_create_workingHour(working_hour, request):
    if len(working_hour) > 0:
        return working_hour
    else:
        if request.data["role"] in ["ADMIN"]:
            WorkingHour.objects.create(
                type=request.GET.get("type", None),
                staff=request.GET.get("staff_id", None),
                department=request.data.get("department", None),
                working_hours=get_default_working_hours(),
                organisation=request.data.get("organisation", None),
                created_by=request.data.get("user", None),
            )
            print("save...")
            working_hour = WorkingHour.objects.filter(
                type=request.GET.get("type", None),
                staff=request.GET.get("staff_id", None),
                department=request.data.get("department", None),
                working_hours=get_default_working_hours(),
                organisation=request.data.get("organisation", None),
                created_by=request.data.get("user", None),
            )
            return working_hour
        elif request.data["role"] in ["MANAGER"]:
            WorkingHour.objects.create(
                type="appointment",
                staff=request.GET.get("staff_id", None),
                department=request.data.get("department", None),
                working_hours=get_default_working_hours(),
                organisation=request.data.get("organisation", None),
                created_by=request.data.get("user", None),
            )
            working_hour = WorkingHour.objects.filter(
                type="appointment",
                staff=request.GET.get("staff_id", None),
                department=request.data.get("department", None),
                working_hours=get_default_working_hours(),
                organisation=request.data.get("organisation", None),
                created_by=request.data.get("user", None),
            )
            print("save...")
            return working_hour
        else:
            WorkingHour.objects.create(
                type="appointment",
                staff=request.data.get("user", None),
                department=request.data.get("department", None),
                working_hours=get_default_working_hours(),
                organisation=request.data.get("organisation", None),
                created_by=request.data.get("user", None),
            )
            working_hour = WorkingHour.objects.filter(
                type="appointment",
                staff=request.data.get("user", None),
                department=request.data.get("department", None),
                working_hours=get_default_working_hours(),
                organisation=request.data.get("organisation", None),
                created_by=request.data.get("user", None),
            )
            print("save...")
            return working_hour
