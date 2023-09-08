from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from sentry_sdk import capture_exception
from calendars.models import Day_off, WorkingHour
import datetime
from calendars.serializers import DayoffSerializer
from datetime import datetime
from common.configs.config import config as cfg
from BaseWorke.middlewares.new_relic_middleware import get_logger
from common.helpers.status_message import (
    Return403Permition,
    Return200,
    Return400Errors,
    Return400Required,
    Return500Exception,
    Return400Bad,
    Return201Create,
    Return200Details,
    checking_validation,
)
from django.db.models import Q
from django.core.paginator import Paginator
from common.helpers.pagination import pagination
from common.gRPC.action.user_action import get_user_data
from common.helpers.helper import getuserdetails

logger = get_logger()


class DayoffList(APIView):
    def get(self, request):
        page = request.GET.get("page", 1)
        limit = request.GET.get("limit", 20)
        start_date = request.GET.get("start_date", None)
        end_date = request.GET.get("end_date", None)
        time = request.GET.get("time", None)
        staff_id = request.GET.get("staff_id", None)
        status = request.GET.get("status", None)

        try:
            org = request.data.get("organisation", None)

            if request.data["role"] in ["MANAGER", "STAFF", "AGENT", "ADMIN"]:
                if request.data["role"] in ["ADMIN"]:
                    if staff_id is not None:
                        dayoff = Day_off.objects.filter(
                            Q(source_id=staff_id)
                            | Q(source_id=request.data.get("organisation", None)),
                            is_active=True,
                        ).order_by("-created_at")
                    else:
                        dayoff = Day_off.objects.filter(
                            is_active=True,
                            organisation=request.data.get("organisation", None),
                        ).order_by("-created_at")

                elif request.data["role"] in ["MANAGER"]:
                    # if source_id is None:
                    #     return
                    if staff_id is not None:
                        dayoff = Day_off.objects.filter(
                            Q(source_id=staff_id)
                            | Q(source_id=request.data.get("organisation", None)),
                        ).order_by("-created_at")
                    else:
                        dayoff = Day_off.objects.filter(
                            is_active=True,
                            type="staff",
                            source_id=request.data.get("source_id", None),
                            department=request.data.get("department", None),
                            organisation=request.data.get("organisation", None),
                        ).order_by("-created_at")
                elif request.data["role"] in ["STAFF", "AGENT"]:
                    if staff_id is not None:
                        dayoff = Day_off.objects.filter(
                            Q(source_id=request.data.get("user", None))
                            | Q(source_id=request.data.get("organisation", None))
                        ).order_by("-created_at")
                    else:
                        dayoff = Day_off.objects.filter(
                            is_active=True,
                            type="staff",
                            source_id=request.data.get("user", None),
                        ).order_by("-created_at")
                else:
                    return Return403Permition()

                # ------- Date & time filtering---------
                if start_date is not None and end_date is not None:
                    dayoff = dayoff.filter(
                        Q(start_date__range=(start_date, end_date))
                        | Q(end_date__range=(start_date, end_date))
                    )
                elif start_date is not None and end_date is None:
                    dayoff = dayoff.filter(
                        start_date__lte=start_date, end_date__gte=start_date
                    )
                elif start_date is not None and time is not None:
                    dayoff = dayoff.filter(
                        start_date__lte=start_date,
                        end_date__gte=start_date,
                        start_time__lte=time,
                        end_time__gte=time,
                    )

                if status is not None:
                    dayoff = dayoff.filter(status=status)

                paginator = Paginator(dayoff, limit)
                result = pagination(page, paginator)
                serializer = DayoffSerializer(result, many=True)
                message = "Day_off info"

                return Return200(
                    message, serializer.data, dayoff.count(), page, paginator.num_pages
                )
            else:
                return Return403Permition()
        except Exception as Err:
            capture_exception(Err)
            return Return500Exception(Err)

    def post(self, request):
        try:
            if request.data["type"] == "staff":
                working_hour = WorkingHour.objects.get(
                    is_active=True,
                    type="appointment",
                    staff=request.data["source_id"],
                )
            else:
                working_hour = WorkingHour.objects.get(
                    is_active=True,
                    type="organisation",
                    staff=request.data["source_id"],
                )
            error = checking_validation(request, working_hour)
            if error:
                return error

            request.data["created_by"] = request.data.get("user", None)

            if request.data["type"] == "staff":
                user_details = get_user_data(
                    request.data["source_id"], False, False, False, False
                )

                if user_details is None:
                    user_details = getuserdetails(
                        request.data["source_id"],
                        request.headers.get("Authorization", None),
                    )
                    user_details = user_details["data"]

                request.data["staff_name"] = user_details.get(
                    "fname", "invalid source_id"
                )

            elif request.data["type"] == "organisation":
                request.data["staff_name"] = "Complete day of organisation"

            if request.data["role"] in ["ADMIN"]:
                if request.data.get("source_id", None) is None:
                    return Return400Required("Source_id")

                serializer = DayoffSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Return201Create(serializer.data)
                else:
                    return Return400Bad("Day_off is not created", serializer)

            elif request.data["role"] in ["MANAGER"]:
                if request.data.get("source_id", None) is None:
                    return Return400Required("Source_id")
                if request.data["type"] == "organisation":
                    return Return403Permition()

                serializer = DayoffSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Return201Create(serializer.data)
                else:
                    return Return400Bad("Day_off is not created", serializer)

            elif (
                request.data["role"] in ["STAFF", "AGENT"]
                and request.data["type"] == "staff"
            ):
                serializer = DayoffSerializer(data=request.data)
                request.data["source_id"] = request.data["user"]
                if serializer.is_valid():
                    serializer.save()
                    return Return201Create(serializer.data)
                else:
                    return Return400Bad("Day_off is not created", serializer)
            else:
                return Return403Permition()
        except Exception as Err:
            capture_exception(Err)
            return Return500Exception(Err)


class DayoffDetails(APIView):
    def get(self, request, pk):
        try:
            if request.data["role"] in ["ADMIN"]:
                dayoff = get_object_or_404(
                    Day_off,
                    id=pk,
                    is_active=True,
                    organisation=request.data.get("organisation", None),
                )
            elif request.data["role"] in ["MANAGER"]:
                dayoff = get_object_or_404(
                    Day_off,
                    id=pk,
                    is_active=True,
                    type="staff",
                    organisation=request.data.get("organisation", None),
                    department=request.data.get("department", None),
                )
            elif request.data["role"] in ["STAFF", "AGENT"]:
                dayoff = get_object_or_404(
                    Day_off,
                    id=pk,
                    is_active=True,
                    type="staff",
                    source_id=request.data.get("user", None),
                    organisation=request.data.get("organisation", None),
                    department=request.data.get("department", None),
                )
            else:
                return Return403Permition()
            serializer = DayoffSerializer(dayoff)
            return Return200Details(
                "Day_off details",
                serializer.data,
            )
        except Exception as Err:
            capture_exception(Err)
            return Return500Exception(Err)

    def put(self, request, pk):
        try:
            if request.data["role"] in ["ADMIN"]:
                dayoff = get_object_or_404(
                    Day_off,
                    id=pk,
                    is_active=True,
                    organisation=request.data.get("organisation", None),
                )
            elif request.data["role"] in ["MANAGER"]:
                dayoff = get_object_or_404(
                    Day_off,
                    id=pk,
                    is_active=True,
                    organisation=request.data.get("organisation", None),
                )
            elif request.data["role"] in ["STAFF", "AGENT"]:
                dayoff = get_object_or_404(
                    Day_off,
                    id=pk,
                    is_active=True,
                    type="staff",
                    source_id=request.data.get("user", None),
                    organisation=request.data.get("organisation", None),
                )
            else:
                return Return403Permition()
            serializer = DayoffSerializer(dayoff, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Return200Details(" Updated Successfully", serializer.data)
            else:
                return Return400Bad("Day_off is not updated", serializer)
        except Exception as Err:
            capture_exception(Err)
            return Return500Exception(Err)

    def delete(self, request, pk):
        try:
            if request.data["role"] in ["ADMIN"]:
                dayoff = get_object_or_404(
                    Day_off,
                    id=pk,
                    is_active=True,
                    organisation=request.data.get("organisation", None),
                )
            elif request.data["role"] in ["MANAGER"]:
                dayoff = get_object_or_404(
                    Day_off,
                    id=pk,
                    is_active=True,
                    organisation=request.data.get("organisation", None),
                    department=request.data.get("department", None),
                )
            elif request.data["role"] in ["STAFF", "AGENT"]:
                dayoff = get_object_or_404(
                    Day_off,
                    id=pk,
                    is_active=True,
                    type="staff",
                    source_id=request.data.get("user", None),
                    organisation=request.data.get("organisation", None),
                )
            else:
                return Return403Permition()
            dayoff.is_active = False
            dayoff.deleted_at = datetime.now()
            dayoff.deleted_by = request.data.get("user", None)
            dayoff.save()
            return Return200Details(" Delete Successfully", [])

        except Exception as Err:
            capture_exception(Err)
            return Return500Exception(Err)
