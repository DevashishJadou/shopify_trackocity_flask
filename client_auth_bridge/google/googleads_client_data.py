from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.auth.exceptions import RefreshError
from google.ads.google_ads.client import GoogleAdsClient

import os
from datetime import datetime

from ...db_model.sql_models import ClientGoogleCredentials
from ...connection import db

users = ClientGoogleCredentials.query.filter_by(active=True)

current_time = datetime.now()
hour = current_time.hour

for user in users:
    if user.id % 2 == hour % 2:

        # Define your client-specific credentials
        client_id = os.environ.get("_CLIENT_ID")
        client_secret = os.environ.get("_CLIENT_SECRET")
        access_token = user._token  # Get the access token for each client

        # Set up the Google Ads client dynamically
        credentials = Credentials.from_authorized_user_info(
            client_id=client_id,
            client_secret=client_secret,
            scopes=['https://www.googleapis.com/auth/adwords'],
            access_token=access_token
        )

        google_ads_client = GoogleAdsClient.load_from_dict({
            'developer_token': os.environ.get("_DEVELOPER_TOKEN"),
            'login_customer_id': user.account_name,
            'load_strategy': 'sync',
            'oauth2_client_id': client_id,
            'oauth2_client_secret': client_secret,
            'oauth2_callback': lambda x: credentials,
            'use_proto_plus': False  # Set to True if you want to use Proto Plus
        })

        # Define a query to fetch data (e.g., campaigns)
        query = """
            SELECT
            customer.id AS account_id,
            customer.descriptive_name AS account_name,
            segments.date,
            campaign.id,
            campaign.name,
            ad_group.id,
            ad_group.name,
            ad.id,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros / 1000000.0 AS spend
        FROM
            keyword_view
        WHERE
            segments.date DURING LAST_7_DAYS
        """

        # Initialize a Google Ads API service client
        google_ads_service = google_ads_client.service.google_ads

        try:
            response = google_ads_service.search(customer_id=os.environ.get("_LOGIN_CUSTOMER_ID"), query=query)

            
            for row in response:
                print(f"Campaign ID: {row.campaign.id}, Campaign Name: {row.campaign.name}")
                print(f"Ad Group ID: {row.ad_group.id}, Ad Group Name: {row.ad_group.name}")

        except RefreshError:
            print("Authentication token refresh failed. Please check your credentials.")

        except Exception as e:
            print(f"An error occurred: {e}")
