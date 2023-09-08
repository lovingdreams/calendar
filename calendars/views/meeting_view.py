from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from sentry_sdk import capture_exception
from rest_framework import status
from calendars.models import Meeting, MeetingOrder
import datetime
from calendars.serializers import MeetingSerializer, MeetingorderSerializer
from common.swagger.swagger_documentation import (
    swagger_auto_schema,
    page,
    limit,
    meeting_api_documentation,
)
from common.events.publisher import publish_event
from datetime import datetime
from common.configs.config import config as cfg
from BaseWorke.helpers.errors_helper import getErrorMessage
from BaseWorke.middlewares.new_relic_middleware import get_logger
from common.helpers.publisher_payload import notification_meeting

logger = get_logger()


class MeetingList(APIView):
    @swagger_auto_schema(manual_parameters=[page, limit])
    def get(self, request):
        try:
            if request.data["role"] in ["MANAGER", "STAFF", "AGENT", "ADMIN"]:
                staff_id = request.data.get("user", None)

                meetingorder, is_created = MeetingOrder.objects.get_or_create(
                    staff_id=request.data.get("user", None),
                    organisation=request.data.get("organisation", None),
                    department=request.data.get("department", None),
                )
                meetings = Meeting.objects.filter(
                    staff=request.data.get("user", None),
                    is_active=True,
                    organisation=request.data.get("organisation", None),
                    department=request.data.get("department", None),
                ).order_by("-created_at")
                if is_created == False:
                    meetingorder = MeetingOrder.objects.get(
                        is_active=True,
                        staff_id=staff_id,
                        organisation=request.data.get("organisation", None),
                        department=request.data.get("department", None),
                    )

                    if len(meetings) != len(meetingorder.meeting_order):
                        for i in meetings:
                            if str(i.id) not in meetingorder.meeting_order:
                                meetingorder.meeting_order = (
                                    meetingorder.meeting_order + [str(i.id)]
                                )
                                meetingorder.save()

                    get_meetingorder_data = []
                    for i in meetingorder.meeting_order:
                        for meeting in meetings:
                            if i == str(meeting.id):
                                get_meetingorder_data.append(meeting)
                else:
                    get_meetingorder_data = meetings

                serializer = MeetingSerializer(get_meetingorder_data, many=True)
                return Response(
                    {
                        "status": 200,
                        "message": "Meeting info",
                        "data": serializer.data,
                        "count": meetings.count(),
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

    @meeting_api_documentation
    def post(self, request):
        try:
            if request.data["role"] in ["MANAGER", "STAFF", "AGENT", "ADMIN"]:
                if len(request.data["description"]) >= 500:
                    return Response(
                        {
                            "status": 400,
                            "message": "Ensure this field has no more than 500 characters",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                request.data["created_by"] = request.data.get("user", None)
                request.data["staff"] = request.data.get("user", None)
                serializer = MeetingSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    message = notification_meeting(serializer, request)
                    try:
                        publish_event(
                            message,
                            cfg.get("rabbit_mq", "NOTIFICATION_EXCHANGE_NAME"),
                            cfg.get("rabbit_mq", "MEETING_CREATE_ROUTING_KEY"),
                        )
                        logger.info(
                            "calendars/ published to-->"
                            + cfg.get("rabbit_mq", "NOTIFICATION_EXCHANGE_NAME")
                            + "RoutingKey-->"
                            + cfg.get("rabbit_mq", "MEETING_CREATE_ROUTING_KEY")
                            + "Payload-->"
                            + str(message)
                        )
                    except Exception as Err:
                        capture_exception(Err)
                        return Response(
                            {"status": 500, "message": "error", "data": str(Err)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        )

                    meetingorder, is_created = MeetingOrder.objects.get_or_create(
                        staff_id=request.data.get("user", None),
                        organisation=request.data.get("organisation", None),
                        department=request.data.get("department", None),
                    )
                    meetingorder.meeting_order.append(serializer.data["id"])
                    meetingorder.save()

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
                        "message": "Meeting is not created",
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


class MeetingDetails(APIView):
    def get(self, request, pk):
        try:
            if request.data["role"] in ["MANAGER", "STAFF", "AGENT", "ADMIN"]:
                meeting = get_object_or_404(
                    Meeting,
                    id=pk,
                    is_active=True,
                    organisation=request.data.get("organisation", None),
                    department=request.data.get("department", None),
                )
                serializer = MeetingSerializer(meeting)
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

    @meeting_api_documentation
    def put(self, request, pk):
        try:
            if request.data["role"] in ["MANAGER", "STAFF", "AGENT", "ADMIN"]:
                meeting = get_object_or_404(
                    Meeting,
                    id=pk,
                    is_active=True,
                    organisation=request.data.get("organisation", None),
                    department=request.data.get("department", None),
                )
                serializer = MeetingSerializer(meeting, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    meeting.updated_at = datetime.now()
                    meeting.updated_by = request.data.get("user", None)
                    meeting.save()
                    message = notification_meeting(serializer, request)
                    try:
                        publish_event(
                            message,
                            cfg.get("rabbit_mq", "NOTIFICATION_EXCHANGE_NAME"),
                            cfg.get("rabbit_mq", "MEETING_UPDATE_ROUTING_KEY"),
                        )
                        logger.info(
                            "calendars/ published to-->"
                            + cfg.get("rabbit_mq", "NOTIFICATION_EXCHANGE_NAME")
                            + "RoutingKey-->"
                            + cfg.get("rabbit_mq", "MEETING_UPDATE_ROUTING_KEY")
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
                return Response(
                    {
                        "status": 400,
                        "message": "Something went wrong, try after sometime",
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

    def delete(self, request, pk):
        try:
            if request.data["role"] in ["MANAGER", "STAFF", "AGENT", "ADMIN"]:
                meeting = get_object_or_404(
                    Meeting,
                    id=pk,
                    is_active=True,
                    staff=request.data.get("user", None),
                    organisation=request.data.get("organisation", None),
                )
                meeting.is_active = False
                meeting.deleted_at = datetime.now()
                meeting.deleted_by = request.data.get("user", None)
                meeting.save()
                try:
                    meetingorder = MeetingOrder.objects.get(
                        is_active=True,
                        staff_id=request.data.get("user", None),
                        organisation=request.data.get("organisation", None),
                    )
                    if pk in meetingorder.meeting_order:
                        meeting_sequence = meetingorder.meeting_order.remove(pk)
                except MeetingOrder.DoesNotExist:
                    return Response(
                        {"status": 200, "message": " Deleted Successfully"},
                        status=status.HTTP_200_OK,
                    )

                return Response(
                    {"status": 200, "message": " Deleted Successfully"},
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


class MeetingOrderList(APIView):
    def put(self, request):
        try:
            meeting_order = MeetingOrder.objects.get(
                is_active=True, staff_id=request.data.get("user", None)
            )
            serializer = MeetingorderSerializer(
                meeting_order, data=request.data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {
                        "status": 200,
                        "message": "meeting order",
                        "data": serializer.data,
                    },
                    status=status.HTTP_200_OK,
                )
            return Response(
                {
                    "status": 400,
                    "message": serializer.errors,
                    "data": [],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as Err:
            capture_exception(Err)
            return Response(
                {"status": 500, "message": "Error", "data": str(Err)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
