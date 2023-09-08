from rest_framework.response import Response
from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from sentry_sdk import capture_exception
from rest_framework import status, generics
from common.helpers.pagination import pagination
from django.core.paginator import Paginator
from calendars.models import Profile, Meeting, MeetingOrder, WorkingHour
import datetime
from calendars.serializers import ProfileSerializer
from common.helpers.publisher_payload import notification_profile
from common.swagger.swagger_documentation import (
    swagger_auto_schema,
    limit,
    page,
    profile_api_documentation,
)
from common.events.publisher import publish_event
from datetime import datetime
from common.configs.config import config as cfg

from BaseWorke.helpers.errors_helper import getErrorMessage
from BaseWorke.middlewares.new_relic_middleware import get_logger

logger = get_logger()


class ProfileList(APIView):
    @swagger_auto_schema(manual_parameters=[page, limit])
    def get(self, request):
        page = request.GET.get("page", 1)
        limit = request.GET.get("limit", 20)
        try:
            if request.data["role"] in ["MANAGER", "STAFF", "AGENT", "ADMIN"]:
                profile = Profile.objects.filter(
                    is_active=True,
                    staff=request.data.get("user", None),
                    organisation=request.data.get("organisation", None),
                    department=request.data.get("department", None),
                ).order_by("-created_at")
                paginator = Paginator(profile, limit)
                result = pagination(page, paginator)
                serializer = ProfileSerializer(result, many=True)
                return Response(
                    {
                        "status": 200,
                        "message": "profile info",
                        "data": serializer.data,
                        "count": profile.count(),
                        "page": int(page),
                        "pages": paginator.num_pages,
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
                {"status": 500, "message": "error", "data": str(Err)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @profile_api_documentation
    def post(self, request):
        try:
            if request.data["role"] in ["MANAGER", "STAFF", "AGENT", "ADMIN"]:
                request.data["created_by"] = request.data.get("user", None)
                request.data["staff"] = request.data.get("user", None)
                identifier = request.data.get("identifier", None)
                profile = Profile.objects.filter(is_active=True, identifier=identifier)
                meeting = Meeting.objects.filter(
                    is_active=True, staff=request.data.get("user", None)
                )
                working_hours = WorkingHour.objects.filter(
                    is_active=True, staff=request.data.get("user", None), type="meeting"
                )

                if identifier is not None:
                    if profile.exists():
                        return Response(
                            {
                                "status": 400,
                                "message": " identifier already exists ",
                                "data": [],
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                else:
                    return Response(
                        {
                            "status": 400,
                            "message": " identifier required ",
                            "data": [],
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                serializer = ProfileSerializer(data=request.data)

                if serializer.is_valid():
                    serializer.save()

                    # -------------------- Default Meeting creations----------
                    if len(meeting) == 0:
                        for i in range(2):
                            meeting = Meeting.objects.create(
                                meeting_name=f"Meeting-0{i+1}",
                                duration=30 * (i + 1),
                                description="",
                                organisation=request.data["organisation"],
                                department=request.data["department"],
                                created_by=request.data["user"],
                                staff=request.data["user"],
                                is_active=True,
                            )
                            meeting.save()

                            meetingorder, created = MeetingOrder.objects.get_or_create(
                                staff_id=request.data.get("user", None),
                                organisation=request.data.get("organisation", None),
                                department=request.data.get("department", None),
                            )
                            if created:
                                meetingorder.meeting_order = [
                                    str(meeting.id)
                                ]  # Create a new list with the meeting ID as string
                            else:
                                meetingorder.meeting_order.append(
                                    str(meeting.id)
                                )  # Convert the meeting ID to a string and append to the existing list
                            meetingorder.save()

                    # ------------------- Default meeting working hour creation --------------

                    if len(working_hours) == 0:
                        organisation_workingHour = WorkingHour.objects.filter(
                            is_active=True,
                            staff=request.data.get("organisation", None),
                            type="organisation",
                        )

                        working_hours = WorkingHour.objects.create(
                            organisation=request.data["organisation"],
                            department=request.data["department"],
                            created_by=request.data["user"],
                            staff=request.data["user"],
                            working_hours=organisation_workingHour[0].working_hours,
                            is_active=True,
                        )

                    message = notification_profile(serializer, request)
                    try:
                        publish_event(
                            message,
                            cfg.get("rabbit_mq", "NOTIFICATION_EXCHANGE_NAME"),
                            cfg.get("rabbit_mq", "NOTIFICATION_CREATE_ROUTING_KEY"),
                        )
                        logger.info(
                            "calendars/ published to-->"
                            + cfg.get("rabbit_mq", "NOTIFICATION_EXCHANGE_NAME")
                            + "RoutingKey-->"
                            + cfg.get("rabbit_mq", "NOTIFICATION_CREATE_ROUTING_KEY")
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
                        "message": "Some fields are missing",
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
        except Exception as Err:
            capture_exception(Err)
            return Response(
                {"status": 500, "message": "error", "data": str(Err)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ProfileDetails(APIView):
    def get(self, request, pk):
        try:
            if request.data["role"] in ["MANAGER", "STAFF", "AGENT", "ADMIN"]:
                profile = get_object_or_404(
                    Profile,
                    id=pk,
                    staff=request.data.get("user", None),
                    is_active=True,
                    organisation=request.data.get("organisation", None),
                    department=request.data.get("department", None),
                )
                serializer = ProfileSerializer(profile)
                return Response(
                    {
                        "status": 200,
                        "message": "Profile details",
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
                {"status": 500, "message": "error", "data": str(Err)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @profile_api_documentation
    def put(self, request, pk):
        try:
            if request.data["role"] in ["MANAGER", "STAFF", "AGENT", "ADMIN"]:
                request.data["staff"] = request.data.get("user", None)
                profile = get_object_or_404(
                    Profile,
                    id=pk,
                    staff=request.data.get("user", None),
                    is_active=True,
                    organisation=request.data.get("organisation", None),
                    department=request.data.get("department", None),
                )
                serializer = ProfileSerializer(profile, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    profile.updated_at = datetime.now()
                    profile.updated_by = request.data.get("user", None)
                    profile.save()
                    try:
                        profile_message = notification_profile(serializer, request)
                        publish_event(
                            profile_message,
                            cfg.get("rabbit_mq", "NOTIFICATION_EXCHANGE_NAME"),
                            cfg.get("rabbit_mq", "NOTIFICATION_UPDATE_ROUTING_KEY"),
                        )
                        logger.info(
                            "calendars/ published to-->"
                            + cfg.get("rabbit_mq", "NOTIFICATION_EXCHANGE_NAME")
                            + "RoutingKey-->"
                            + cfg.get("rabbit_mq", "NOTIFICATION_UPDATE_ROUTING_KEY")
                            + "Payload-->"
                            + str(profile_message)
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
                return Response(
                    {
                        "status": 406,
                        "message": "Not updated",
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
                profile = get_object_or_404(
                    Profile,
                    id=pk,
                    staff=request.data.get("user", None),
                    is_active=True,
                    organisation=request.data.get("organisation", None),
                    department=request.data.get("department", None),
                )
                profile.is_active = False
                profile.deleted_at = datetime.now()
                profile.deleted_by = request.data.get("user", None)
                profile.save()
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
