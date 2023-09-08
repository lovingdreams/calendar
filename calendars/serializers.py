from rest_framework import serializers
from .models import *
from BaseWorke.helpers.common_helper import get_uuid
from django.shortcuts import render, get_object_or_404
from django.core.exceptions import ValidationError
from datetime import datetime


class BookingSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    startStr = serializers.SerializerMethodField()
    endStr = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        exclude = ["booking_id"]

    def get_title(self, obj):
        # Custom logic to retrieve or compute the value for the "title" field

        return obj.booking_name

    def get_startStr(self, obj):
        original_datetime = datetime.strptime(
            obj.booking_start_time, "%Y-%m-%d %H:%M:%S"
        )
        formatted_datetime = original_datetime.strftime("%Y-%m-%dT%H:%M:%S")
        return formatted_datetime

    def get_endStr(self, obj):
        original_datetime = datetime.strptime(obj.booking_end_time, "%Y-%m-%d %H:%M:%S")
        formatted_datetime = original_datetime.strftime("%Y-%m-%dT%H:%M:%S")
        return formatted_datetime

    # def validate(self, data):
    #     staff = data["staff"]
    #     active_bookings = Booking.objects.filter(staff=staff)
    #     for booking in active_bookings:
    #         if slots_clash(
    #             booking.start_time,
    #             data["start_time"],
    #             booking.end_time,
    #             data["end_time"],
    #         ):
    #             raise ValidationError(("Invalid Time slot"), code="invalid")
    #     return data


def slots_clash(start_1, start_2, end_1, end_2):
    if (start_1 == start_2) and (end_1 == end_2):
        return True

    return (
        (start_1 < start_2 < end_1)
        or (start_1 < end_2 < end_1)
        or (start_2 < end_1 < end_2)
    )


def slots_clash_checking(start_1, start_2, end_1, end_2):
    # if (start_1 <= start_2 <= end_1 <= end_2):
    #     return True

    return (
        (start_1 <= start_2 < end_1)
        or (start_1 < end_2 < end_1)
        or (start_2 < end_1 < end_2)
    )


class WorkingHourSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkingHour
        fields = "__all__"


class MeetingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meeting
        fields = "__all__"


class ProfileSerializer(serializers.ModelSerializer):
    image = serializers.CharField(allow_blank=True, allow_null=True)

    class Meta:
        model = Profile
        fields = "__all__"


class ConsultationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        exclude = ["meeting_id"]


class MeetingorderSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeetingOrder
        fields = "__all__"

    # def validate(self, data):
    #     staff = data["staff"]
    #     active_bookings = Booking.objects.filter(staff=staff)
    #     for booking in active_bookings:
    #         if slots_clash(
    #             booking.start_time,
    #             data["start_time"],
    #             booking.end_time,
    #             data["end_time"],
    #         ):
    #             raise ValidationError(("Invalid Time slot"), code="invalid")
    #     return data


class DayoffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Day_off
        fields = "__all__"
