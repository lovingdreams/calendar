from rest_framework.response import Response
from rest_framework import status
from BaseWorke.helpers.errors_helper import *


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


def Return400Bad(message, data):
    return Response(
        {
            "status": 400,
            "message": message,
            "data": getErrorMessage(data.errors),
        },
        status=status.HTTP_400_BAD_REQUEST,
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


def Return400Errors(data):
    return Response(
        {
            "status": 400,
            "message": "Error",
            "data": data,
        },
        status=status.HTTP_400_BAD_REQUEST,
    )


def checking_validation(request):
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
