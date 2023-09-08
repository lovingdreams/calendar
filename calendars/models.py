from django.db import models
from BaseWorke.WorkeBaseModel import BaseModel


# Create your models here.
class Booking(BaseModel):
    class Calendar_Type(models.TextChoices):
        APPOINTMENT = "appointment", "Appointment"
        MEETING = "meeting", "Meeting"
        ORGANISATION = "organisation", "Organisation"

    class BOOKINGTypes(models.TextChoices):
        HOLD = "hold", "Hold"
        ACCCEPTED = "accepted", "Accepted"
        COMPLETED = "completed", "Completed"
        REJECTED = "rejected", "Rejected"
        UPDATED = "updated", "Updated"
        CANCELLED = "cancelled", "Cancelled"

    booking_status = models.CharField(
        max_length=20, choices=BOOKINGTypes.choices, default="hold"
    )
    booking_name = models.CharField(
        max_length=100, null=False, blank=False, default=""
    )  # consultation name is changed
    duration = models.PositiveIntegerField(null=False, blank=False, default=30)
    date = models.CharField(max_length=100, null=False, blank=False, default="")
    start_time = models.CharField(max_length=100, null=False, blank=False, default="")
    end_time = models.CharField(max_length=100, null=False, blank=False, default="")
    staff = models.CharField(max_length=100, null=False, blank=False, default="")
    name = models.CharField(max_length=100, null=False, blank=False, default="")
    email = models.CharField(max_length=100, null=False, blank=False, default="")
    guest_email = models.JSONField(blank=True, null=True, default=dict)

    meeting_id = models.CharField(max_length=100, null=True, blank=True, default="")
    description = models.TextField(null=True, blank=True)
    booking_id = models.CharField(max_length=100, null=True, blank=True, default="")
    appointment_id = models.CharField(max_length=100, null=True, blank=True, default="")
    time_zone = models.CharField(
        max_length=100, null=False, blank=False, default="Asia/Kolkata"
    )
    booking_start_time = models.CharField(
        max_length=100, null=False, blank=False, default=""
    )
    booking_end_time = models.CharField(
        max_length=100, null=False, blank=False, default=""
    )
    type = models.CharField(
        max_length=20, choices=Calendar_Type.choices, default=Calendar_Type.MEETING
    )


class WorkingHour(BaseModel):
    class Calendar_Type(models.TextChoices):
        APPOINTMENT = "appointment", "Appointment"
        MEETING = "meeting", "Meeting"
        ORGANISATION = "organisation", "Organisation"

    staff = models.CharField(max_length=100, null=False, blank=False, default="")
    working_hours = models.JSONField(blank=False, null=False, default=dict)
    time_zone = models.CharField(
        max_length=100, null=False, blank=False, default="Asia/Kolkata"
    )
    type = models.CharField(
        max_length=20, choices=Calendar_Type.choices, default=Calendar_Type.MEETING
    )


class Meeting(BaseModel):
    meeting_name = models.CharField(max_length=100, null=False, blank=False, default="")
    duration = models.PositiveIntegerField(null=False, blank=False, default=30)
    type = models.CharField(max_length=100, null=False, blank=False, default="")
    meeting_link = models.CharField(max_length=300, null=True, blank=True, default="")
    staff = models.CharField(max_length=100, null=False, blank=False, default="")
    description = models.TextField(null=True, blank=True)
    tags = models.CharField(max_length=100, null=True, blank=True)


class MeetingOrder(BaseModel):
    staff_id = models.CharField(max_length=100, null=False, blank=False)
    meeting_order = models.JSONField(blank=True, null=True, default=list)


class Profile(BaseModel):
    identifier = models.CharField(
        max_length=50, null=False, unique=True, blank=False, default=True
    )
    description_title = models.TextField(blank=False, null=False, default="")
    description = models.TextField(blank=False, null=False, default="")
    meeting_description_title = models.TextField(blank=False, null=False, default="")
    meeting_description = models.TextField(blank=False, null=False, default="")
    image = models.TextField(blank=False, null=False, default="")

    staff = models.CharField(max_length=100, null=False, blank=False, default="")

    linkdin_url = models.CharField(max_length=100, null=True, blank=True, default="")
    twitter_url = models.CharField(max_length=100, null=True, blank=True, default="")
    instagram_url = models.CharField(max_length=100, null=True, blank=True, default="")
    facebook_url = models.CharField(max_length=100, null=True, blank=True, default="")


class Day_off(BaseModel):
    class Calendar_Type(models.TextChoices):
        STAFF = "staff", "Staff"
        ORGANISATION = "organisation", "Organisation"

    title = models.CharField(max_length=100, null=False, blank=False)
    start_time = models.CharField(max_length=100, null=False, blank=False)
    end_time = models.CharField(max_length=100, null=False, blank=False)
    start_date = models.CharField(max_length=100, null=False, blank=False)
    end_date = models.CharField(max_length=100, null=False, blank=False)
    source_id = models.CharField(max_length=100, null=False, blank=False)
    company_name = models.CharField(max_length=100, null=True, blank=True, default="")
    staff_name = models.CharField(max_length=100, null=True, blank=True, default="")
    type = models.CharField(
        max_length=20, choices=Calendar_Type.choices, null=False, blank=False
    )
