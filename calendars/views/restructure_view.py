from rest_framework.response import Response
from rest_framework.views import APIView
from sentry_sdk import capture_exception
from rest_framework import status
from calendars.models import Booking
import datetime
from datetime import datetime
from common.configs.config import config as cfg
from common.helpers.helper import get_Time_Zone, timedelta
from rest_framework.permissions import AllowAny


class BookingrestructureList(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        try:
            booking = Booking.objects.all()
            print(len(booking))
            for i in range(len(booking)):
                date = datetime.strptime(booking[i].date, "%Y-%m-%d")
                user_time = datetime.strptime(booking[i].start_time, "%H:%M").time()
                date_and_time = datetime.combine(date, user_time)
                user_time_duration = date_and_time + timedelta(
                    minutes=booking[i].duration
                )

                if booking[i].booking_start_time in ["", None]:
                    start_time = get_Time_Zone(
                        date_and_time, "Asia/Kolkata", booking[i].time_zone
                    )
                    booking[i].booking_start_time = start_time
                    booking[i].save()
                if booking[i].booking_end_time == "":
                    end_time = get_Time_Zone(
                        user_time_duration, "Asia/Kolkata", booking[i].time_zone
                    )
                    booking[i].booking_end_time = end_time
                    booking[i].save()

            return Response(
                {
                    "status": 200,
                    "message": "Updated booking_start_date and booking_end_date",
                },
                status=status.HTTP_200_OK,
            )

        except Exception as Err:
            capture_exception(Err)
            return Response(
                {"status": 500, "message": "Error", "data": str(Err)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
