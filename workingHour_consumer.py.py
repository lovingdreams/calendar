import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.settings")
import django

django.setup()
import pika, json
import logging

from calendars.serializers import WorkingHourSerializer
from calendars.models import WorkingHour
from common.configs.config import config as cfg
from common.data.static import *
from BaseWorke.middlewares.new_relic_middleware import get_logger
from common.helpers.helper import get_default_working_hours

logger = get_logger()


def workingHour_consume(ch, method, properties, body):
    try:
        logger.info("Calender  consumer is started")
        data = json.loads(body)
        try:
            if method.routing_key == CALENDAR_USERPROFILE_CREATED_ROUTING_KEY:
                if data["type"] == "appointment":
                    try:
                        datas = {
                            "type": data["type"],
                            "staff": data.get("staff_id", None),
                            "time_zone": data.get("time_zone", None),
                            "working_hours": get_default_working_hours(),
                            "organisation": data.get("organisation", None),
                            "department": data.get("department", None),
                            "created_by": data.get("created_by", None),
                            "user_id": data.get("user_id", None),
                        }

                        if data["type"] == "appointment":
                            working_hour = WorkingHour.objects.filter(
                                staff=datas["organisation"], type="organisation"
                            )

                            datas["working_hours"] = working_hour[0].working_hours

                        working_hour = WorkingHour.objects.filter(
                            staff=datas["staff"], type=datas["type"]
                        )

                        if len(working_hour) != 0:
                            serializer = WorkingHourSerializer(
                                working_hour.first(), data=datas, partial=True
                            )
                            if serializer.is_valid():
                                serializer.save()
                                print("Saved..")
                        else:
                            serializer = WorkingHourSerializer(data=datas)
                            if serializer.is_valid():
                                serializer.save()
                                print("Saved....")

                    except Exception as Err:
                        logger.info("ERRORs--->", Err)

                elif data["type"] == "organisation":
                    organisation = {
                        "type": "organisation",
                        "staff": data.get("organisation", None),
                        "time_zone": data.get("time_zone", None),
                        "working_hours": get_default_working_hours(),
                        "organisation": data.get("organisation", None),
                        "department": data.get("department", None),
                        "created_by": data.get("created_by", None),
                        "user_id": data.get("user_id", None),
                    }
                    appoinment = {
                        "type": "appointment",
                        "staff": data.get("created_by", None),
                        "time_zone": data.get("time_zone", None),
                        "working_hours": get_default_working_hours(),
                        "organisation": data.get("organisation", None),
                        "department": data.get("department", None),
                        "created_by": data.get("created_by", None),
                        "user_id": data.get("user_id", None),
                    }

                    # <<<<<<<<<<< organisation serilizer >>>>>>>>>>
                    organisaion_serializer = WorkingHourSerializer(data=organisation)
                    if organisaion_serializer.is_valid():
                        organisaion_serializer.save()
                        print("organisaion_serializer Saved....")

                    # <<<<<<<<<<< appointment serilizer >>>>>>>>>>
                    appoinment_serializer = WorkingHourSerializer(data=appoinment)
                    if appoinment_serializer.is_valid():
                        appoinment_serializer.save()
                        print("appoinment_serializer Saved....")

            elif method.routing_key == CALENDAR_USERPROFILE_UPATED_ROUTING_KEY:
                if data["type"] == "organisation":
                    working_hour = WorkingHour.objects.filter(
                        staff=data["staff_id"], type=data["type"]
                    )
                    if len(working_hour) == 1:
                        serializer = WorkingHourSerializer(
                            working_hour.first(), data=datas, partial=True
                        )
                        if serializer.is_valid():
                            serializer.save()
                            working_hours = WorkingHour.objects.filter(
                                is_active=True, organisation=data.get("staff_id", None)
                            )
                            working_hours.update(time_zone=datas["time_zone"])

        except Exception as Err:
            logger.info("ERRORs--->", Err)
    except Exception as Err:
        logger.info("ERROR--->", Err)
    # logger.critical("Notification Error -->",Err)


credentials = pika.PlainCredentials("guest", "guest")
parameters = pika.ConnectionParameters(
    host=cfg.get("rabbit_mq", "HOST"),
    virtual_host=cfg.get("rabbit_mq", "VIRTUAL_HOST"),
    credentials=credentials,
    frame_max=int(cfg.get("rabbit_mq", "FRAME_MAX")),
    heartbeat=int(cfg.get("rabbit_mq", "HEART_BEAT")),
    connection_attempts=int(cfg.get("rabbit_mq", "CONNECTION_ATTEMPTS")),
)
conn = pika.BlockingConnection(parameters)
channel = conn.channel()
channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type="topic", durable=True)
channel.queue_declare(queue=QUEUE_NAME, durable=True)

channel.queue_bind(
    queue=QUEUE_NAME,
    exchange=EXCHANGE_NAME,
    routing_key=CALENDAR_USERPROFILE_CREATED_ROUTING_KEY,
)
channel.queue_bind(
    queue=QUEUE_NAME,
    exchange=EXCHANGE_NAME,
    routing_key=CALENDAR_USERPROFILE_UPATED_ROUTING_KEY,
)

channel.basic_consume(
    queue=QUEUE_NAME,
    on_message_callback=workingHour_consume,
    auto_ack=True,
)

logger.info("Calendar consumer is started...")
channel.start_consuming()
