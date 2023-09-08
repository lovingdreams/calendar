from rest_framework.response import Response
from rest_framework import status
from BaseWorke.helpers.errors_helper import *
from datetime import datetime
import pytz


def Return403Permition():
    return Response(
        {
            "status": 403,
            "message": "No Permissions",
        },
        status=status.HTTP_403_FORBIDDEN,
    )


def Return500Exception(Message):
    return Response(
        {"status": 500, "message": "Error", "data": str(Message)},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def Return201Create(data):
    return Response(
        {
            "status": 201,
            "message": " Created Successfully",
            "data": data,
        },
        status=status.HTTP_201_CREATED,
    )


def Return400Bad(message, data):
    return Response(
        {
            "status": 400,
            "message": message,
            "data": getErrorMessage(data.errors),
        },
        status=status.HTTP_400_BAD_REQUEST,
    )


def Return200(message, data, count, page, num_pages):
    return Response(
        {
            "status": 200,
            "message": message,
            "data": data,
            "count": count,
            "page": int(page),
            "pages": num_pages,
        },
        status=status.HTTP_200_OK,
    )


def Return400Required(data):
    return Response(
        {
            "status": 400,
            "message": "Error",
            "data": f"{data} is required",
        },
        status=status.HTTP_400_BAD_REQUEST,
    )


def Return400Valid(data):
    return Response(
        {
            "status": 400,
            "message": "Error",
            "data": f"{data}",
        },
        status=status.HTTP_400_BAD_REQUEST,
    )


def Return400Errors(data):
    return Response(
        {
            "status": 400,
            "message": "Error",
            "data": data,
        },
        status=status.HTTP_400_BAD_REQUEST,
    )


def Return200Details(message, data):
    return Response(
        {
            "status": 200,
            "message": message,
            "data": data,
        },
        status=status.HTTP_200_OK,
    )


def checking_validation(request, working_hour):
    print("value----->", working_hour.time_zone)
    if request.data.get("title", None) is None:
        return Return400Required("Title")
    if request.data.get("start_time", None) is None:
        return Return400Required("Start_time")
    if request.data.get("end_time", None) is None:
        return Return400Required("End_time")
    if request.data.get("start_date", None) is None:
        return Return400Required("Start_date")
    if request.data.get("end_date", None) is None:
        return Return400Required("End_date")
    if request.data.get("type", None) is None:
        return Return400Required("Type")
    current_timezone = pytz.timezone(working_hour.time_zone)
    current_date_in_india = datetime.now(current_timezone).date()
    current_time_in_india = datetime.now(current_timezone).time()
    print("current_timezone--->", current_timezone)
    print("current_date_in_india--->", current_date_in_india)
    print("current_time_in_india--->", current_time_in_india)

    if (
        datetime.strptime(request.data["start_date"], "%Y-%m-%d").date()
        < current_date_in_india
    ):
        return Return400Valid("Check the date")
    if (
        datetime.strptime(request.data["end_date"], "%Y-%m-%d").date()
        < current_date_in_india
    ):
        return Return400Valid("Check the date")
    if request.data.get("start_date", None) <= request.data.get("end_date", None):
        pass
    else:
        return Return400Valid("Please enter valied date")
    if request.data.get("start_date", None) == request.data.get("end_date", None):
        if request.data.get("start_time", None) < request.data.get("end_time", None):
            pass
        else:
            return Return400Valid("Please enter valied time")
        if (
            datetime.strptime(request.data["start_time"], "%H:%M").time()
            < current_time_in_india
        ):
            return Return400Valid("Please enter valied time")
        if (
            datetime.strptime(request.data["end_time"], "%H:%M").time()
            < current_time_in_india
        ):
            return Return400Valid("Please enter valied time")
