from .gads_client import create_client, handleGoogleAdsException
from google.ads.googleads.errors import GoogleAdsException
# from client_auth_bridge.google.gads_client import create_client, handleGoogleAdsException

# from ..db_model.sql_models import ClientGoogleCredentials
# from ..connection import db

def list_accessible_customer(token, userid=None):
    # user = ClientGoogleCredentials.query.filter_by(workspace=userid).first() is not None

    # if not user and token:
    #     user = ClientGoogleCredentials(workspace=userid, _token=token)
    #     db.session.add(user)
    #     db.session.commit()

    # if user and not token:
    #     token = user._token

    client = create_client(token)
    try:
        customer_service = client.get_service("CustomerService")

        accessible_customers = customer_service.list_accessible_customers()
        resource_names = [resource_name for resource_name in accessible_customers.resource_names]
        return resource_names

    except GoogleAdsException as ex:
        handleGoogleAdsException(ex)