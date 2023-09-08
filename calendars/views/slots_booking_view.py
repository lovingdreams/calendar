from rest_framework.response import Response
from rest_framework.views import APIView
from sentry_sdk import capture_exception
from rest_framework import status, generics
from calendars.models import WorkingHour, Meeting, Booking, Day_off
import datetime
from calendars.serializers import BookingSerializer
from datetime import datetime
from common.configs.config import config as cfg
from rest_framework.permissions import AllowAny
from BaseWorke.middlewares.new_relic_middleware import get_logger
from common.events.publisher import publish_event
from common.helpers.status_message import Return400Required, getErrorMessage
from common.helpers.publisher_payload import slot_payload, contact_payload
from common.helpers.helper import *
from common.data.static import get_default_working_hour

logger = get_logger()


class GetSlotViews(generics.GenericAPIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        staff_id = request.data.get("staff", None)
        meeting_id = request.data.get("meeting_id", None)
        appointment_duration = request.data.get("appointment_duration", None)
        slot_duration = request.data.get("slot_duration", None)
        date = request.data.get("date", None)
        type = request.data.get("type", None)
        global meeting_duration, working_hour
        try:
            if request.data.get("type", None) is None:
                return Return400Required("type")
            if request.data.get("time_zone", None) is None:
                return Response(
                    {
                        "status": 400,
                        "message": "time zone required  ",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if staff_id is not None:
                try:
                    working_hour = WorkingHour.objects.get(
                        is_active=True, staff=request.data["staff"], type=type
                    )
                except Exception as Error:
                    if request.data.get("organisation", None) is None:
                        return Response(
                            {
                                "status": 400,
                                "message": "Please enter organisation also",
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    try:
                        org_workingHour = WorkingHour.objects.filter(
                            staff=request.data["organisation"],
                            is_active=True,
                            type="organisation",
                        )
                    except Exception as Error:
                        org_workingHour = WorkingHour.objects.create(
                            organisation=request.data["organisation"],
                            department=request.data["organisation"],
                            staff=request.data["organisation"],
                            is_active=True,
                            working_hours=get_default_working_hour(),
                            type="organisation",
                        )

                    data = {
                        "type": request.data["type"],
                        "staff": request.data.get("staff_id", None),
                        "time_zone": request.data.get("time_zone", None),
                        "working_hours": org_workingHour[0].working_hours,
                        "organisation": request.data.get("organisation", None),
                        "department": org_workingHour[0].department,
                    }
                    serializer = WorkingHourSerializer(data=data)
                    if serializer.is_valid():
                        serializer.save()
                        print("Saved....")
                    working_hour = WorkingHour.objects.get(
                        is_active=True, staff=request.data["staff"], type=type
                    )
            else:
                return Response(
                    {
                        "status": 400,
                        "message": "Staff id required  ",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if available(date, working_hour) == False:
                return Response(
                    {
                        "status": 200,
                        "message": "No available slots ",
                        "data": [],
                    },
                    status=status.HTTP_200_OK,
                )
            if appointment_duration is not None:
                meeting_duration = appointment_duration
            elif meeting_id is not None:
                try:
                    meeting = Meeting.objects.get(
                        is_active=True, id=request.data["meeting_id"]
                    )
                    meeting_duration = meeting.duration
                except:
                    return Response(
                        {
                            "status": 400,
                            "message": "Incorrect meeting_id ",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                return Response(
                    {
                        "status": 400,
                        "message": "Meeting id required ",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            queryset = Booking.objects.filter(
                type=type, is_active=True, staff=request.data["staff"]
            )
            slots = getGenerate_openapi_slot(
                working_hour,
                date,
                slot_duration,
                meeting_duration,
                queryset,
                request.data["time_zone"],
            )
            # ------------------  Checking the day of the slots----------
            source_id = request.data["staff"]
            organisation_day_off = Day_off.objects.filter(
                status=True,
                source_id=working_hour.organisation,
                start_date__lte=date,
                end_date__gte=date,
            )
            for i in range(len(organisation_day_off)):
                slots = block_day_off(organisation_day_off[i], slots)

            if type != "organisation":
                staff_day_off = Day_off.objects.filter(
                    status=True,
                    source_id=source_id,
                    start_date__lte=date,
                    end_date__gte=date,
                )
                for i in range(len(staff_day_off)):
                    slots = block_day_off(staff_day_off[i], slots)

            return Response(
                {"status": 200, "message": "Available Slots", "data": slots},
                status=status.HTTP_200_OK,
            )
        except Exception as Err:
            capture_exception(Err)
            return Response(
                {"status": 500, "message": "error", "data": str(Err)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class OpenapiBookingList(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        staff_id = request.data.get("staff", None)
        meeting_id = request.data.get("meeting_id", None)
        duration = request.data.get("duration", None)
        date = request.data.get("date", None)
        type = request.data.get("type", None)
        # global meeting_duration, working_hour
        try:
            if request.data.get("type", None) is None:
                return Return400Required("type")
            if request.data.get("time_zone", None) is None:
                return Response(
                    {
                        "status": 400,
                        "message": "time zone required  ",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                meeting = Meeting.objects.get(id=request.data["meeting_id"])

                zoommeeting_link = meeting.meeting_link
            except Exception as err:
                zoommeeting_link = ""

            if staff_id is not None:
                working_hour = WorkingHour.objects.filter(
                    type=type, is_active=True, staff=request.data["staff"]
                )

                if len(working_hour) == 0:
                    return Response(
                        {
                            "status": 428,
                            "message": "Working Hours Unavailable for Staff",
                        },
                        status=status.HTTP_428_PRECONDITION_REQUIRED,
                    )

            else:
                return Response(
                    {
                        "status": 400,
                        "message": "Staff id required  ",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if duration is not None:
                meeting_duration = duration
            queryset = Booking.objects.filter(
                type=type, is_active=True, staff=request.data["staff"]
            )

            date_obj = datetime.strptime(request.data["date"], "%Y-%m-%d").date()
            slots = getGenerate_Booking_slot(
                working_hour[0],
                date,
                meeting_duration,
                queryset,
                request.data["start_time"],
                request.data["time_zone"],
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

                if serializer.is_valid():
                    serializer.save()
                    original_format = "%Y-%m-%d %H:%M:%S"
                    desired_format = "%Y-%m-%dT%H:%M:%S"
                    start_datetime = datetime.strptime(
                        serializer.data["booking_start_time"], original_format
                    )
                    end_datetime = datetime.strptime(
                        serializer.data["booking_end_time"], original_format
                    )
                    start_converted_datetime_string = start_datetime.strftime(
                        desired_format
                    )
                    end_converted_datetime_string = end_datetime.strftime(
                        desired_format
                    )
                    serializer.data[
                        "booking_start_time"
                    ] = start_converted_datetime_string
                    serializer.data["booking_end_time"] = end_converted_datetime_string

                    guest_emails = request.data.get("guest_email", [])
                    email = []
                    if guest_emails != []:
                        if guest_emails[0]["mail"] == "":
                            email = [serializer.data["email"]]
                        else:
                            email = [guest_emails[0]["mail"]] + [
                                serializer.data["email"]
                            ]

                    date_time_string = serializer.data["booking_start_time"]
                    date_time_obj = datetime.strptime(
                        date_time_string, "%Y-%m-%d %H:%M:%S"
                    )

                    dates = date_time_obj.date()
                    time = date_time_obj.time()
                    try:
                        message = slot_payload(
                            email, serializer, zoommeeting_link, dates, time
                        )

                        publish_event(
                            message,
                            cfg.get("rabbit_mq", "EXCHANGE_NAME"),
                            cfg.get("rabbit_mq", "CREATE_ROUTING_KEY"),
                        )
                        logger.info(
                            "calendars/ published to-->"
                            + cfg.get("rabbit_mq", "EXCHANGE_NAME")
                            + "RoutingKey-->"
                            + cfg.get("rabbit_mq", "CREATE_ROUTING_KEY")
                            + "Payload-->"
                            + str(message)
                        )
                    except Exception as Err:
                        capture_exception(Err)
                        return Response(
                            {"status": 500, "message": "error", "data": str(Err)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        )
                    try:
                        message = contact_payload(serializer, request)

                        publish_event(
                            message,
                            cfg.get("rabbit_mq", "CONTACT_EXCHANGE_NAME"),
                            cfg.get("rabbit_mq", "CONTACT_ROUTING_KEY"),
                        )
                        logger.info(
                            "calendars/ published to-->"
                            + cfg.get("rabbit_mq", "CONTACT_EXCHANGE_NAME")
                            + "RoutingKey-->"
                            + cfg.get("rabbit_mq", "CONTACT_ROUTING_KEY")
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
            else:
                return Response(
                    {"status": 400, "message": "Check the duration of time"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Exception as Err:
            capture_exception(Err)
            return Response(
                {"status": 500, "message": "error", "data": str(Err)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
