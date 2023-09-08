from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


from calendars.models import *


page = openapi.Parameter("page", openapi.IN_QUERY, type=openapi.TYPE_INTEGER)
limit = openapi.Parameter("limit", openapi.IN_QUERY, type=openapi.TYPE_INTEGER)


booking_api_documentation = swagger_auto_schema(
    operation_description="Form Fields Create/Update API",
    responses={400: "Bad Request", 200: "Success"},
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "start_time": openapi.Schema(type=openapi.TYPE_STRING),
            "end_time": openapi.Schema(type=openapi.TYPE_STRING),
            "staff": openapi.Schema(type=openapi.TYPE_STRING),
            "meeting": openapi.Schema(type=openapi.TYPE_STRING),
            "meeting_name": openapi.Schema(type=openapi.TYPE_STRING),
        },
    ),
)

woring_hour_api_documentation = swagger_auto_schema(
    operation_description="Form Fields Create/Update API",
    responses={400: "Bad Request", 200: "Success"},
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "staff": openapi.Schema(type=openapi.TYPE_STRING),
            "working_hours": openapi.Schema(type=openapi.TYPE_STRING),
        },
    ),
)

meeting_api_documentation = swagger_auto_schema(
    operation_description="Form Fields Create/Update API",
    responses={400: "Bad Request", 200: "Success"},
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "name": openapi.Schema(type=openapi.TYPE_STRING),
            "duration": openapi.Schema(type=openapi.TYPE_STRING),
        },
    ),
)

profile_api_documentation = swagger_auto_schema(
    operation_description="Form Fields Create/Update API",
    responses={400: "Bad Request", 200: "Success"},
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "title": openapi.Schema(type=openapi.TYPE_STRING),
            "description": openapi.Schema(type=openapi.TYPE_STRING),
            "image": openapi.Schema(type=openapi.TYPE_STRING),
            "staff": openapi.Schema(type=openapi.TYPE_STRING),
        },
    ),
)
