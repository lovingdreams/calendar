from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import render, get_object_or_404
from sentry_sdk import capture_exception
from rest_framework import status
from common.helpers.pagination import pagination
from django.core.paginator import Paginator
from calendars.models import Profile, WorkingHour, Booking, Meeting
import datetime
from calendars.serializers import (
    ProfileSerializer,
    BookingSerializer,
    MeetingSerializer,
)
from common.swagger.swagger_documentation import swagger_auto_schema, page, limit
from datetime import datetime, timezone
from common.configs.config import config as cfg
from common.helpers.helper import getGenerate_Booking_slot
from rest_framework.permissions import AllowAny
from BaseWorke.helpers.errors_helper import getErrorMessage
from BaseWorke.middlewares.new_relic_middleware import get_logger


logger = get_logger()


class OpenapiProfileList(APIView):
    permission_classes = (AllowAny,)

    @swagger_auto_schema(manual_parameters=[page, limit])
    def get(self, request):
        page = request.GET.get("page", 1)
        limit = request.GET.get("limit", 20)
        staff_id = request.GET.get("staff_id", None)
        identifier = request.GET.get("identifier", None)
        try:
            if staff_id is not None:
                profile = Profile.objects.filter(
                    is_active=True, staff=staff_id
                ).order_by("-created_at")
            elif identifier is not None:
                profile = Profile.objects.filter(
                    is_active=True,
                    identifier=identifier,
                )
            else:
                return Response(
                    {"status": 400, "message": "staff id required"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            paginator = Paginator(profile, limit)
            result = pagination(page, paginator)
            serializer = ProfileSerializer(result, many=True)
            return Response(
                {
                    "status": 200,
                    "message": "profile info",
                    "data": serializer.data,
                    "count": profile.count(),
                    # "page": paginator.count,
                    "page": int(page),
                    "pages": paginator.num_pages,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as Err:
            capture_exception(Err)
            return Response(
                {"status": 500, "message": "error", "data": str(Err)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class OpenapiBookingDetails(APIView):
    permission_classes = (AllowAny,)

    def put(self, request, pk):
        try:
            booking = Booking.objects.get(
                appointment_id=pk,
                is_active=True,
            )
            time_zone = request.data.get("time_zone", booking.time_zone)
            duration = request.data.get("duration", booking.duration)
            date = request.data.get("date", booking.date)
            working_hour = WorkingHour.objects.filter(
                is_active=True, staff=booking.staff, type=booking.type
            )
            if len(working_hour) == 0:
                return Response(
                    {
                        "status": 428,
                        "message": "Working Hours Unavailable for Staff",
                    },
                    status=status.HTTP_428_PRECONDITION_REQUIRED,
                )
            if duration is not None:
                meeting_duration = duration
            queryset = Booking.objects.filter(is_active=True, staff=booking.staff)
            date_obj = datetime.strptime(request.data["date"], "%Y-%m-%d").date()
            slots = getGenerate_Booking_slot(
                working_hour[0],
                date,
                meeting_duration,
                queryset,
                request.data["start_time"],
                time_zone,
            )
            request.data["organisation"] = working_hour[0].organisation
            request.data["department"] = working_hour[0].department
            serializer = BookingSerializer(data=request.data)
            if slots == False:
                return Response(
                    {
                        "status": 400,
                        "message": "Slots are already booked",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                request.data["booking_start_time"] = str(slots["user_start_time"])
                request.data["date"] = str(slots["date"])
                request.data["booking_end_time"] = str(slots["user_end_time"])
                request.data["end_time"] = str(slots["end"])[:-3]
                request.data["start_time"] = str(slots["start"])[:-3]
                serializer = BookingSerializer(booking, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(
                        {
                            "status": 200,
                            "message": " Updated Successfully",
                            "data": serializer.data,
                        },
                        status=status.HTTP_200_OK,
                    )
                return Response(
                    {
                        "status": 400,
                        "message": "Booking hours not available",
                        "data": getErrorMessage(serializer.errors),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except Exception as err:
                return Response(
                    {
                        "status": 400,
                        "message": "No slot available" + str(err),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Exception as Err:
            capture_exception(Err)
            return Response(
                {"status": 500, "message": "error", "data": str(Err)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    def delete(self,request,pk):
        try:
            booking = get_object_or_404(Booking,appointment_id=pk,is_active=True)
            booking.is_active = False
            booking.deleted_at = datetime.now()
            booking.deleted_by = request.data.get("user", None)
            booking.save()
            return Response(
                        {"status": 200, "message": "Deleted Successfully"},
                        status=status.HTTP_200_OK,
                    )
        except Exception as Err:
            capture_exception(Err)
            return Response(
                {"status": 500, "message": "error", "data": str(Err)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )



class OpenapiMeetingList(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        page = request.GET.get("page", 1)
        limit = request.GET.get("limit", 20)
        staff_id = request.GET.get("staff_id", None)
        try:
            if staff_id is not None:
                meeting = Meeting.objects.filter(
                    is_active=True, staff=staff_id
                ).order_by("-created_at")
                paginator = Paginator(meeting, limit)
                result = pagination(page, paginator)
                serializer = MeetingSerializer(result, many=True)
                return Response(
                    {
                        "status": 200,
                        "message": "Meeting info",
                        "data": serializer.data,
                        "count": meeting.count(),
                        # "page": paginator.count,
                        "page": int(page),
                        "pages": paginator.num_pages,
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"status": 400, "message": "Staff id required"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        except Exception as Err:
            capture_exception(Err)
            return Response(
                {"status": 500, "message": "Error", "data": str(Err)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class OpenapiMeetingDetails(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, pk):
        try:
            meeting = Meeting.objects.get(
                id=pk,
                is_active=True,
            )
            serializer = MeetingSerializer(meeting)
            return Response(
                {
                    "status": 200,
                    "message": "Profile details",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as Err:
            capture_exception(Err)
            return Response(
                {"status": 500, "message": "Error", "data": str(Err)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
