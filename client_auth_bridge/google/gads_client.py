import os
import json

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

REFRESH_ERROR = "INVAILD REFRESH TOKEN"

_VERSION = "v16"

def create_client(token):
    try:
        credentials = {
            "developer_token": os.environ.get("_DEVELOPER_TOKEN"),
            "client_id": os.environ.get("_CLIENT_ID"),
            "client_secret": os.environ.get("_CLIENT_SECRET"),
            "refresh_token": token,
            "token_uri": "https://oauth2.googleapis.com/token",
            "use_proto_plus": "true" 
        }
        return GoogleAdsClient.load_from_dict(credentials, version=_VERSION)
    except Exception as e:
        print(f'error in google create_client: {e.args}')
        raise ValueError(REFRESH_ERROR)


def handleGoogleAdsException(ex: GoogleAdsException):
    print(
        f'Request with ID "{ex.request_id}" failed with status '
        f'"{ex.error.code().name}" and includes the following errors:'
    )
    for error in ex.failure.errors:
        if error.location:
            for field_path_element in error.location.field_path_elements:
                print(f"\t\tOn field: {field_path_element.field_name}")


def handleException(ex):
    error = str(ex)
    if error == REFRESH_ERROR:
        return json.dumps({
            "code": 401,
            "name": "INVALID_REFRESH_TOKEN",
            "description": error          
        })
    else:
        return json.dumps({
            "code": 500,
            "name": "INTERNAL_SERVER_ERROR",
            "description": error          
        })