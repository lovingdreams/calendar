QUEUE_NAME = "CALENDAR_SERVICE"
# "AUDIT"
EXCHANGE_NAME = "CALENDER"

CALENDAR_USERPROFILE_CREATED_ROUTING_KEY = "Calendar.Workinghour.Create"
CALENDAR_USERPROFILE_UPATED_ROUTING_KEY = "Calendar.Workinghour.Update"


def get_default_working_hour():
    return [
        {"days": "MONDAY", "status": True, "slots": [["09:00", "17:00"]]},
        {"days": "TUESDAY", "status": True, "slots": [["09:00", "17:00"]]},
        {"days": "WEDNESDAY", "status": True, "slots": [["09:00", "17:00"]]},
        {"days": "THURSDAY", "status": True, "slots": [["09:00", "17:00"]]},
        {"days": "FRIDAY", "status": True, "slots": [["09:00", "17:00"]]},
        {"days": "SATURDAY", "status": True, "slots": [["09:00", "17:00"]]},
        {"days": "SUNDAY", "status": True, "slots": [["09:00", "17:00"]]},
    ]
