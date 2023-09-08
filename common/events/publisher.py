import pika, json
import logging
from common.configs.config import config as cfg
from BaseWorke.middlewares.new_relic_middleware import get_logger


def publish_event(message, exchange_name, routing_key):
    try:
        logging.info(f"message : {message}")
        logging.info(f"routing_key : {routing_key}")
        logging.info("Publisher_message ----->", message)
        credentials = pika.PlainCredentials(
            cfg.get("rabbit_mq", "USER_NAME"), cfg.get("rabbit_mq", "PASSWORD")
        )
        parameters = pika.ConnectionParameters(
            host=cfg.get("rabbit_mq", "HOST"),
            virtual_host=cfg.get("rabbit_mq", "VIRTUAL_HOST"),
            credentials=credentials,
            frame_max=int(cfg.get("rabbit_mq", "FRAME_MAX")),
            heartbeat=int(cfg.get("rabbit_mq", "HEART_BEAT")),
            connection_attempts=int(cfg.get("rabbit_mq", "CONNECTION_ATTEMPTS")),
        )
        conn = pika.BlockingConnection(parameters)
        logging.info(f"conn: {conn}")
        logging.info("message --->", message)
        channel = conn.channel()
        channel.exchange_declare(
            exchange=exchange_name, exchange_type="topic", durable=True
        )
        channel.basic_publish(
            exchange=exchange_name, routing_key=routing_key, body=json.dumps(message)
        )
        logger = get_logger()
        logger.info(
            "EVENT SUCCESFULLY PUBLISHED TO "
            + cfg.get("rabbit_mq", "EXCHANGE_NAME")
            + "\n ROUTING KEY"
            + cfg.get("rabbit_mq", "CREATE_ROUTING_KEY")
            + "\n CURRENT PAYLOAD \n"
            + str(message)
        )
        logging.info("compleated")
        conn.close()
    except Exception as Err:
        logging.info(f"publish_event exception : {Err}")
