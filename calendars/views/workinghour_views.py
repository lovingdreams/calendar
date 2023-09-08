from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from sentry_sdk import capture_exception
from rest_framework import status
from common.helpers.pagination import pagination
from django.core.paginator import Paginator
from calendars.models import WorkingHour
import datetime
from calendars.serializers import WorkingHourSerializer
from common.swagger.swagger_documentation import (
    woring_hour_api_documentation,
    swagger_auto_schema,
    page,
    limit,
)
from common.helpers.helper import auto_create_workingHour
from common.helpers.publisher_payload import notification_workingHour
from common.events.publisher import publish_event
from datetime import datetime
from common.configs.config import config as cfg
from common.helpers.helper import *
from BaseWorke.helpers.errors_helper import *
from BaseWorke.middlewares.new_relic_middleware import get_logger
from common.helpers.status_message import Return400Required

logger = get_logger()


def slots_clash(start_1, start_2, end_1, end_2):
    if (start_1 == start_2) or (end_1 == end_2):
        return True
    return (
        (start_1 < start_2 < end_1)
        or (start_1 < end_2 < end_1)
        or (start_2 < end_1 < end_2)
    )


def has_overlapping_slots(slots):
    slots = [
        (datetime.strptime(slot[0], "%H:%M"), datetime.strptime(slot[1], "%H:%M"))
        for slot in slots
    ]

    for i in range(len(slots)):
        for j in range(i + 1, len(slots)):
            if slots_clash(slots[i][0], slots[j][0], slots[i][1], slots[j][1]):
                return True
    # No overlapping slots found
    return False


def validateWorkinghours(hours):
    for day in hours:
        print(day["days"], "-->", day["slots"], len(day["slots"]))
        if len(day["slots"]) > 1:
            if has_overlapping_slots((day["slots"])):
                return False
        else:
            pass
    return True


class WorkingHourList(APIView):
    @swagger_auto_schema(manual_parameters=[page, limit])
    def get(self, request):
        page = request.GET.get("page", 1)
        limit = request.GET.get("limit", 20)

        staff = request.GET.get("staff_id", None)
        type = request.GET.get("type", None)
        try:
            if request.data["role"] in ["MANAGER", "STAFF", "AGENT", "ADMIN"]:
                if type is None:
                    return Return400Required("Type")

                if request.data["role"] in ["ADMIN"]:
                    if staff is None:
                        return Return400Required("Staff_id")

                    working_hour = WorkingHour.objects.filter(
                        is_active=True,
                        type=type,
                        staff=staff,
                        organisation=request.data.get("organisation", None),
                    ).order_by("-created_at")
                    if len(working_hour) == 0:
                        if staff == request.data.get(
                            "organisation", None
                        ) or staff == request.data.get("user", None):
                            working_hour = auto_create_workingHour(
                                working_hour, request
                            )

                elif request.data["role"] in ["MANAGER"]:
                    if staff is None:
                        return Return400Required("Staff_id")
                    working_hour = WorkingHour.objects.filter(
                        is_active=True,
                        type=type,
                        staff=staff,
                        department=request.data.get("department", None),
                        organisation=request.data.get("organisation", None),
                    ).order_by("-created_at")
                    if len(working_hour) == 0:
                        working_hour = auto_create_workingHour(working_hour, request)

                else:
                    working_hour = WorkingHour.objects.filter(
                        is_active=True,
                        type=type,
                        staff=request.data.get("user", None),
                        department=request.data.get("department", None),
                        organisation=request.data.get("organisation", None),
                    ).order_by("-created_at")
                    if len(working_hour) == 0:
                        working_hour = auto_create_workingHour(working_hour, request)
                if len(working_hour) > 0:
                    paginator = Paginator(working_hour, limit)
                    result = pagination(page, paginator)
                    serializer = WorkingHourSerializer(result, many=True)
                    return Response(
                        {
                            "status": 200,
                            "message": "Working_hour info",
                            "data": serializer.data,
                            "count": working_hour.count(),
                            "page": int(page),
                            "pages": paginator.num_pages,
                        },
                        status=status.HTTP_200_OK,
                    )
                else:
                    return Response(
                        {
                            "status": 428,
                            "message": "Not register Working Hour data",
                        },
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
                {"status": 500, "message": "Error", "data": str(Err)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @woring_hour_api_documentation
    def post(self, request):
        # try:
        if request.data["role"] in ["MANAGER", "STAFF", "AGENT", "ADMIN"]:
            request.data["created_by"] = request.data.get("user", None)
            request.data["is_active"] = True
            if request.data.get("type", None) is None:
                return Response(
                    {
                        "status": 400,
                        "message": "type required  ",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if request.data.get("time_zone", None) is None:
                return Response(
                    {
                        "status": 400,
                        "message": "time zone required  ",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if request.data["role"] in ["MANAGER", "ADMIN"]:
                if request.data.get("staff_id", None) is None:
                    return Response(
                        {
                            "status": 400,
                            "message": "staff_id required  ",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            staff = request.data.get("staff_id", None)
            if staff is None:
                request.data["staff"] = request.data.get("user", None)
            else:
                request.data["staff"] = staff
            validworkinghours = validateWorkinghours(request.data["working_hours"])
            if not validworkinghours:
                return Response(
                    {
                        "status": 400,
                        "message": "Invalid working hours",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            working_hour = WorkingHour.objects.filter(
                staff=request.data["staff"], type=request.data.get("type", "meeting")
            )
            if len(working_hour) == 1:
                serializer = WorkingHourSerializer(
                    working_hour.first(), data=request.data, partial=True
                )
                if serializer.is_valid():
                    serializer.save()
                    working_hour.first().updated_at = datetime.now()
                    working_hour.first().updated_by = request.data.get("user", None)
                    working_hour.first().save()
                    message = notification_workingHour(serializer, request)
                    try:
                        publish_event(
                            message,
                            cfg.get("rabbit_mq", "NOTIFICATION_EXCHANGE_NAME"),
                            cfg.get("rabbit_mq", "WORKINGHOUR_CREATE_ROUTING_KEY"),
                        )
                        logger.info(
                            "calendars/ published to-->"
                            + cfg.get("rabbit_mq", "NOTIFICATION_EXCHANGE_NAME")
                            + "RoutingKey-->"
                            + cfg.get("rabbit_mq", "WORKINGHOUR_CREATE_ROUTING_KEY")
                            + "Payload-->"
                            + str(message)
                        )
                    except Exception as Err:
                        capture_exception(Err)
                        return Response(
                            {"status": 500, "message": "error", "data": str(Err)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        )
                    return Response(
                        {
                            "status": 200,
                            "message": " Updated Successfully",
                            "data": serializer.data,
                        },
                        status=status.HTTP_200_OK,
                    )
            else:
                serializer = WorkingHourSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    message = notification_workingHour(serializer, request)
                    try:
                        publish_event(
                            message,
                            cfg.get("rabbit_mq", "NOTIFICATION_EXCHANGE_NAME"),
                            cfg.get("rabbit_mq", "WORKINGHOUR_CREATE_ROUTING_KEY"),
                        )
                        logger.info(
                            "calendars/ published to-->"
                            + cfg.get("rabbit_mq", "NOTIFICATION_EXCHANGE_NAME")
                            + "RoutingKey-->"
                            + cfg.get("rabbit_mq", "WORKINGHOUR_CREATE_ROUTING_KEY")
                            + "Payload-->"
                            + str(message)
                        )
                    except Exception as Err:
                        capture_exception(Err)
                        return Response(
                            {"status": 500, "message": "error", "data": str(Err)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        )
                    return Response(
                        {
                            "status": 201,
                            "message": " Created Successfully",
                            "data": serializer.data,
                        },
                        status=status.HTTP_201_CREATED,
                    )
                return Response(
                    {
                        "status": 400,
                        "message": "Working hours not created",
                        "data": getErrorMessage(serializer.errors),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(
                {
                    "status": 403,
                    "message": "No Permissions",
                },
                status=status.HTTP_403_FORBIDDEN,
            )


class WorkingHourDetails(APIView):
    def get(self, request, pk):
        type = request.GET.get("type", None)
        department = request.GET.get("department", None)
        try:
            if request.data["role"] in ["ADMIN"]:
                if department is None:
                    return Response(
                        {
                            "status": 400,
                            "message": "department required  ",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                else:
                    request.data["department"] = department

            if request.data["role"] in ["MANAGER", "STAFF", "AGENT", "ADMIN"]:
                if type is None:
                    return Response(
                        {
                            "status": 400,
                            "message": "type required  ",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                try:
                    Working_hour = WorkingHour.objects.get(staff=pk, type=type)
                except:
                    department = request.data.get("department", None)
                    organisation = request.data.get("organisation", None)
                    user = request.data.get("user", None)

                    org_workingHour = WorkingHour.objects.filter(
                        staff=organisation, type="organisation"
                    )
                    Working_hour = WorkingHour.objects.create(
                        staff=pk,
                        type=type,
                        working_hours=org_workingHour[0].working_hours,
                        organisation=organisation,
                        department=department,
                        created_by=user,
                    )
                serializer = WorkingHourSerializer(Working_hour)
                return Response(
                    {
                        "status": 200,
                        "message": "Meeting details",
                        "data": serializer.data,
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

    def delete(self, request, pk):
        try:
            is_active = request.GET.get("is_active", None)
            if request.data["role"] in ["MANAGER", "STAFF", "AGENT", "ADMIN"]:
                if is_active is not None:
                    WorkingHour.objects.filter(is_active=False).delete()
                    return Response(
                        {"status": 428, "message": "   Deleted Successfully all"},
                        status=status.HTTP_428_PRECONDITION_REQUIRED,
                    )

                Working_hour = get_object_or_404(
                    WorkingHour,
                    id=pk,
                    is_active=True,
                    organisation=request.data.get("organisation", None),
                )
                Working_hour.is_active = False
                Working_hour.deleted_at = datetime.now()
                Working_hour.deleted_by = request.data.get("user", None)
                Working_hour.save()
                return Response(
                    {"status": 428, "message": "   Deleted Successfully"},
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
