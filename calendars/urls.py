from django.urls import path

from calendars.views.openapi_views import (
    OpenapiProfileList,
    OpenapiBookingDetails,
    OpenapiMeetingList,
    OpenapiMeetingDetails,
)
from calendars.views.booking_view import BookingDateList, BookingList, BookingDetails
from calendars.views.profile_views import ProfileList, ProfileDetails
from calendars.views.meeting_view import MeetingList, MeetingDetails, MeetingOrderList
from calendars.views.restructure_view import BookingrestructureList
from calendars.views.slots_booking_view import GetSlotViews, OpenapiBookingList
from calendars.views.workinghour_views import WorkingHourList, WorkingHourDetails
from calendars.views.day_off_view import DayoffList, DayoffDetails


urlpatterns = [
    path("bookings/restructure/", BookingrestructureList.as_view()),
    path("bookings/date/", BookingDateList.as_view()),
    path("bookings/", BookingList.as_view()),
    path("bookings/<uuid:pk>/", BookingDetails.as_view()),
    path("workinghours/", WorkingHourList.as_view()),
    path("workinghours/<uuid:pk>/", WorkingHourDetails.as_view()),
    path("meetings/", MeetingList.as_view()),
    path("meetings/<uuid:pk>/", MeetingDetails.as_view()),
    path("meetingorder/", MeetingOrderList.as_view()),
    path("profiles/", ProfileList.as_view()),
    path("profiles/<uuid:pk>/", ProfileDetails.as_view()),
    path("slots/", GetSlotViews.as_view()),
    path("openapi/profiles/", OpenapiProfileList.as_view()),
    path("openapi/bookings/", OpenapiBookingList.as_view()),
    path("openapi/bookings/<uuid:pk>/", OpenapiBookingDetails.as_view()),
    path("openapi/meetings/", OpenapiMeetingList.as_view()),
    path("openapi/meetings/<uuid:pk>/", OpenapiMeetingDetails.as_view()),
    path("dayoff/", DayoffList.as_view()),
    path("dayoff/<uuid:pk>/", DayoffDetails.as_view()),
]
