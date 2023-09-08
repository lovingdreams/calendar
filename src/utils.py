import requests
import json

TEST_CASES_USERS_AUTH_LOGIN_ENDPOINT = (
    "https://services.worke.io/users/authorisation/login/"
)
TEST_CASES_USERS_AUTH_EMAIL = "prasanthi@yopmail.com"
TEST_CASES_USERS_AUTH_PASSWORD = "Abcd@123"


def api_testcase_login(email, password):
    url = TEST_CASES_USERS_AUTH_LOGIN_ENDPOINT
    payload = json.dumps({"email": email, "password": password})
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    response = requests.request("POST", url, headers=headers, data=payload)
    return response
