def notification_profile(serializer, request):
    return {
        "title": serializer.data["description_title"],
        "recipients": [],
        "source_type": "profile",
        "source_id": serializer.data["id"],
        "department": serializer.data["department"],
        "organisation": serializer.data["organisation"],
        "created_by": serializer.data["created_by"],
        "updated_by": serializer.data["updated_by"],
        "user_id": serializer.data["created_by"],
        "description": serializer.data["meeting_description"],
        "info": serializer.data["info"],
        "token": request.headers.get("Authorization", None),
    }


def notification_meeting(serializer, request):
    return {
        "title": serializer.data["meeting_name"],
        "recipients": [],
        "source_type": "meetings",
        "source_id": serializer.data["id"],
        "meeting_link": serializer.data["meeting_link"],
        "meeting_type": serializer.data["type"],
        "staff_id": serializer.data["staff"],
        "department": serializer.data["department"],
        "organisation": serializer.data["organisation"],
        "created_by": serializer.data["created_by"],
        "updated_by": serializer.data["updated_by"],
        "user_id": serializer.data["created_by"],
        "description": serializer.data["description"],
        "info": serializer.data["info"],
        "token": request.headers.get("Authorization", None),
    }


def notification_workingHour(serializer, request):
    return {
        "source_type": "schedule",
        "source_id": serializer.data["id"],
        "staff_id": serializer.data["staff"],
        "time_zone": serializer.data["time_zone"],
        "department": serializer.data["department"],
        "organisation": serializer.data["organisation"],
        "created_by": serializer.data["created_by"],
        "updated_by": serializer.data["updated_by"],
        "user_id": serializer.data["created_by"],
        "working_hours": serializer.data["working_hours"],
        "info": serializer.data["info"],
        "token": request.headers.get("Authorization", None),
    }


def slot_payload(email, serializer, zoommeeting_link, dates, time):
    return {
        "type": "both",
        "message": {
            "to": email,
            "from": "support@worke.io",
            "subject": "Meeting scheduled",
            "body": f"<!DOCTYPE html><html><head><meta charset='UTF-8'></head><body><h2>Subject: Meeting Successfully scheduled</h2><p>Dear {serializer.data['name']},</p><p>I am pleased to inform you that the meeting has been successfully booked. Here are the details:</p><ul><li><strong>Date:</strong> {dates}</li><li><strong>Time:</strong> {time}</li><li><strong>Duration:</strong> {serializer.data['duration']} minutes</li><li><strong>Meeting link:</strong> {zoommeeting_link}</li></ul><p>Please make a note of these details and ensure your availability for the meeting. If you have any specific requirements or agenda items you would like to discuss, kindly let me know in advance.</p><p>Should you have any questions or need further assistance, please feel free to reach out to me. Looking forward to a productive and engaging meeting.</p><p>Best regards,</p></body></html>",
        },
        "date": serializer.data["date"],
        "organisation": serializer.data["organisation"],
        "source_type": "calendar",
        "source_id": serializer.data["id"],
        "start_time": serializer.data["booking_start_time"],
        "end_time": serializer.data["booking_end_time"],
        "user_id": serializer.data["created_by"],
        "user": serializer.data["staff"],
        "info": serializer.data["info"],
        "time_zone": serializer.data["time_zone"],
    }


def contact_payload(serializer, request):
    return {
        "first_name": serializer.data["name"],
        "last_name": "",
        "source":"Meeting",
        "organisation": serializer.data["organisation"],
        "department": serializer.data["department"],
        "phone": request.data.get("phone_number", "1234567890"),
        "email": serializer.data["email"],
        "owner": serializer.data["staff"],
        "ccode": request.data.get("ccode", "+91"),
        "user_id": "",
    }
