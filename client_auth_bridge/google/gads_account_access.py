from .gads_client import create_client, handleGoogleAdsException
from google.ads.googleads.errors import GoogleAdsException
# from client_auth_bridge.google.gads_client import create_client, handleGoogleAdsException
# from db_model.sql_models import ClientGoogleCredentials
# from connection import db
from ...db_model.sql_models import ClientGoogleCredentials, googleads_table
from ...connection import db
from sqlalchemy import MetaData
from flask import jsonify

metadata = MetaData()

def list_accessible_customer(token, userid=None):
    user = ClientGoogleCredentials.query.filter_by(workspace=userid).first()
    query = """
            SELECT
                customer_client.client_customer,
                customer_client.level,
                customer_client.manager,
                customer_client.descriptive_name,
                customer_client.currency_code,
                customer_client.time_zone,
                customer_client.id
            FROM
                customer_client
            WHERE
                customer_client.level <= 1
        """

    if not user and token:
        user = ClientGoogleCredentials(workspace=userid, _token=token)
        tablename = 'googleads_'+userid
        if not metadata.tables.get(tablename):
            google_table = googleads_table(tablename)
            google_table.create(bind=db.engine)
        db.session.add(user)
        db.session.commit()

    if user and not token:
        token = user._token


    client = create_client(token)
    try:
        google_ads_service = client.get_service("GoogleAdsService")
        customer_service = client.get_service("CustomerService")

        accessible_customers = customer_service.list_accessible_customers()
        resource_names=[]
        # resource_names = [resource_name for resource_name in accessible_customers.resource_names]

        for customer_resource_names in accessible_customers.resource_names:
            customer_id = customer_resource_names.split('/')[-1]
            try:
                response = google_ads_service.search_stream(customer_id=customer_id, query=query)
                for batch in response:
                    for row in batch.results:
                        client_customer = row.customer_client.client_customer
                        descriptive_name = row.customer_client.descriptive_name
                        resource_names.append(descriptive_name+' / '+client_customer.split('/')[-1])
            except Exception as ex:
                pass
        return resource_names

    except GoogleAdsException as ex:
        handleGoogleAdsException(ex)


def clientaccount_googleads(userid, account, token):
    user = ClientGoogleCredentials.query.filter_by(workspace=userid).first()

    if user:
        user.account_name = account
        user._token = token
    else:
        return jsonify({'status': 'Error'}), 500
    
    db.session.commit()
    return jsonify({'status': 'success'}), 200