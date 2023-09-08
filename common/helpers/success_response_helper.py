from rest_framework.response import Response
from rest_framework import status
from BaseWorke.helpers.errors_helper import *


def Return201Create(data):
    return Response(
        {
            "status": 201,
            "message": " Created Successfully",
            "data": data,
        },
        status=status.HTTP_201_CREATED,
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


def Return200Details(message, data):
    return Response(
        {
            "status": 200,
            "message": message,
            "data": data,
        },
        status=status.HTTP_200_OK,
    )
