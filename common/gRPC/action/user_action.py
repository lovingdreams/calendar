from common.gRPC.protopys import user_service_pb2
from common.gRPC.protopys import user_service_pb2_grpc
from common.configs.config import config as cfg
import grpc
import json
from sentry_sdk import capture_exception


def get_user_data(
    id, organisation, user_additional, user_permissions, user_working_hours
):
    try:
        # print("user_id --->", id)
        # with grpc.insecure_channel(cfg.get("grpc", "urls")) as channel:
        with grpc.insecure_channel(
            cfg.get("grpc", "GRPC_USER_SERVER")
            + ":"
            + cfg.get("grpc", "GRPC_USER_PORT")
        ) as channel:
            # with grpc.insecure_channel("54.214.227.85:8001") as channel:
            stub = user_service_pb2_grpc.UserServicesStub(channel)
            end_user_info_request = user_service_pb2.UserItem(
                id=id,
                organisation=organisation,
                user_additional=user_additional,
                user_permissions=user_permissions,
                user_working_hours=user_working_hours,
            )
            print("end_user_info_request --->", end_user_info_request)
            end_user_info_reply = stub.GetUserData(end_user_info_request)
            print("end_user_info_reply --->", end_user_info_reply)
            return {
                "email": end_user_info_reply.email,
                "fname": end_user_info_reply.fname,
                "lname": end_user_info_reply.lname,
                "username": end_user_info_reply.username,
                "phone_number": end_user_info_reply.phone_number,
            }
    except Exception as Err:
        capture_exception(Err)
