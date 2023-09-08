from rest_framework.response import Response
from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from sentry_sdk import capture_exception
from rest_framework import status, generics
from common.helpers.pagination import pagination
from django.core.paginator import Paginator
from calendars.models import Booking
import datetime
from common.helpers.error_response_helper import *
from common.helpers.success_response_helper import *

from calendars.serializers import BookingSerializer
from common.swagger.swagger_documentation import (
    swagger_auto_schema,
    page,
    limit,
    booking_api_documentation,
)
from datetime import datetime, timezone
from common.configs.config import config as cfg
from common.helpers.helper import get_Time_Zone, get_month_find, timedelta
from BaseWorke.helpers.errors_helper import getErrorMessage
from BaseWorke.middlewares.new_relic_middleware import get_logger

logger = get_logger()


class BookingList(APIView):
    @swagger_auto_schema(manual_parameters=[page, limit])
    def get(self, request):
        page = request.GET.get("page", 1)
        limit = request.GET.get("limit", 20)
        # id = request.GET.get("id", None)
        staff = request.GET.get("staff", None)

        type = request.GET.get("type", "meeting")
        try:
            if request.data["role"] in ["ADMIN"]:
                booking = Booking.objects.filter(
                    is_active=True,
                    organisation=request.data.get("organisation", None),
                ).order_by("-created_at")

            elif request.data["role"] in ["MANAGER"]:
                booking = Booking.objects.filter(
                    is_active=True,
                    organisation=request.data.get("organisation", None),
                    department=request.data.get("department", None),
                ).order_by("-created_at")

            elif request.data["role"] in [
                "STAFF",
                "AGENT",
            ]:
                booking = Booking.objects.filter(
                    is_active=True,
                    organisation=request.data.get("organisation", None),
                    department=request.data.get("department", None),
                    staff=request.data.get("user", None),
                ).order_by("-created_at")

            else:
                return Response(
                    {
                        "status": 403,
                        "message": "No Permissions",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
            if staff is not None:
                booking = booking.filter(staff=staff)
            if type is not None:
                booking = booking.filter(type=type)

            paginator = Paginator(booking, limit)
            result = pagination(page, paginator)
            serializer = BookingSerializer(result, many=True)
            return Response(
                {
                    "status": 200,
                    "message": "Booking info",
                    "data": serializer.data,
                    "count": booking.count(),
                    # booking.count()
                    # "page": paginator.count,
                    "page": int(page),
                    "pages": paginator.num_pages,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as Err:
            capture_exception(Err)
            return Response(
                {"status": 500, "message": "Error", "data": str(Err)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class BookingDetails(APIView):
    def get(self, request, pk):
        time_zone = request.GET.get("time_zone", None)
        try:
            if request.data["role"] in ["MANAGER", "STAFF", "AGENT", "ADMIN"]:
                if time_zone is None:
                    return Response(
                        {
                            "status": 400,
                            "message": "time zone required  ",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                booking = get_object_or_404(
                    Booking,
                    id=pk,
                    is_active=True,
                    organisation=request.data.get("organisation", None),
                )
                serializer = BookingSerializer(booking)
                start_data = get_Time_Zone(
                    serializer.data["booking_start_time"],
                    time_zone,
                    serializer.data["time_zone"],
                )
                end_data = get_Time_Zone(
                    serializer.data["booking_end_time"],
                    time_zone,
                    serializer.data["time_zone"],
                )
                serializer_data = serializer.data

                serializer_data["booking_start_time"] = start_data
                serializer_data["booking_end_time"] = end_data
                serializer_data["startStr"] = start_data
                serializer_data["endStr"] = end_data

                return Response(
                    {
                        "status": 200,
                        "message": "Booking details",
                        "data": serializer_data,
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {
                        "status": 403,
                        "message": "No Permissions",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
        except Exception as Err:
            capture_exception(Err)
            return Response(
                {"status": 500, "message": "Error", "data": str(Err)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @booking_api_documentation
    def put(self, request, pk):
        try:
            if request.data["role"] in ["MANAGER", "STAFF", "AGENT", "ADMIN"]:
                booking = get_object_or_404(
                    Booking,
                    id=pk,
                    is_active=True,
                    organisation=request.data.get("organisation", None),
                    department=request.data.get("department", None),
                )

                serializer = BookingSerializer(booking, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    booking.updated_at = datetime.now()
                    booking.updated_by = request.data.get("user", None)
                    booking.save()
                    return Response(
                        {
                            "status": 202,
                            "message": " Updated Successfully",
                            "data": serializer.data,
                        },
                        status=status.HTTP_202_ACCEPTED,
                    )
                return Response(
                    {
                        "status": 406,
                        "message": "not updated",
                        "data": getErrorMessage(serializer.errors),
                    },
                    status=status.HTTP_406_NOT_ACCEPTABLE,
                )
            else:
                return Response(
                    {
                        "status": 403,
                        "message": "No Permissions",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
        except Exception as Err:
            capture_exception(Err)
            return Response(
                {"status": 500, "message": "error", "data": str(Err)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request, pk):
        try:
            if request.data["role"] in ["MANAGER", "STAFF", "AGENT", "ADMIN"]:
                booking = get_object_or_404(
                    Booking,
                    id=pk,
                    is_active=True,
                    organisation=request.data.get("organisation", None),
                )
                booking.is_active = False
                booking.booking_status = "cancelled"
                booking.deleted_at = datetime.now()
                booking.deleted_by = request.data.get("user", None)
                booking.save()
                return Response(
                    {"status": 428, "message": " Deleted Successfully"},
                    status=status.HTTP_428_PRECONDITION_REQUIRED,
                )
            else:
                return Response(
                    {
                        "status": 403,
                        "message": "No Permissions",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
        except Exception as Err:
            capture_exception(Err)
            return Response(
                {"status": 500, "message": "error", "data": str(Err)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class BookingDateList(APIView):
    @swagger_auto_schema(manual_parameters=[page, limit])
    def get(self, request):
        day = request.GET.get("day", None)
        week = request.GET.get("week", None)
        month = request.GET.get("month", None)
        time_zone = request.GET.get("time_zone", None)
        type = request.GET.get("type", None)

        try:
            if time_zone is None:
                return Response(
                    {
                        "status": 400,
                        "message": "time zone required  ",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if request.data["role"] in ["ADMIN"]:
                booking = Booking.objects.filter(
                    is_active=True, organisation=request.data["organisation"]
                ).order_by("-created_at")

            if request.data["role"] in ["MANAGER", "STAFF", "AGENT"]:
                booking = Booking.objects.filter(
                    staff=request.data["user"],
                    is_active=True,
                ).order_by("-created_at")

            if day is not None:
                booking = booking.filter(date=day)
            elif week is not None:
                dates = datetime.strptime(week, "%Y-%m-%d")
                new_date = dates + timedelta(days=7)
                new_date_str = new_date.strftime("%Y-%m-%d")
                booking = booking.filter(date__range=(week, new_date_str))
            elif month is not None:
                data = get_month_find(month)
                first_date = month
                last_date = data
                booking = booking.filter(date__range=(first_date, last_date))
            else:
                booking = booking.filter(type="meeting")

            for i in range(len(booking)):
                booking_time_start = booking[i].booking_start_time.split("T")
                booking_time_end = booking[i].booking_end_time.split("T")

                if len(booking_time_start) > 1:
                    booking[i].booking_start_time = booking[
                        i
                    ].booking_start_time.replace("T", " ")
                    booking[i].save()

                if len(booking_time_end) > 1:
                    booking[i].booking_end_time = booking[i].booking_end_time.replace(
                        "T", " "
                    )
                    booking[i].save()

            if type is not None:
                booking.filter(type=type)
            serializer = BookingSerializer(booking, many=True)

            for recods in range(len(serializer.data)):
                start_datas = get_Time_Zone(
                    serializer.data[recods]["booking_start_time"],
                    time_zone,
                    serializer.data[recods]["time_zone"],
                )
                end_datas = get_Time_Zone(
                    serializer.data[recods]["booking_end_time"],
                    time_zone,
                    serializer.data[recods]["time_zone"],
                )
                serializer.data[recods]["booking_start_time"] = start_datas
                serializer.data[recods]["booking_end_time"] = end_datas
            return Response(
                {
                    "status": 200,
                    "message": "Booked slots",
                    "data": serializer.data,
                    "count": booking.count(),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as Err:
            capture_exception(Err)
            return Response(
                {"status": 500, "message": "Error", "data": str(Err)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
