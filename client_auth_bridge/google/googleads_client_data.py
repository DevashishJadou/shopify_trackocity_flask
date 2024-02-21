from google.oauth2.credentials import Credentials
from google.ads.google_ads.client import GoogleAdsClient

import os
from datetime import datetime

from ...db_model.sql_models import ClientGoogleCredentials, googleads_table
from ...connection import db
from sqlalchemy.dialects.postgresql import insert

users = ClientGoogleCredentials.query.filter_by(active=True)

current_time = datetime.now()
day = current_time.strftime("%Y-%m-%d")
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
            segments.date as dated,
            campaign.id as campaign_id,
            campaign.name as campaign_name,
            ad_group.id as ad_group_id,
            ad_group.name as ad_group_name,
            ad.id as ad_id,
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
                # Define the insert statement
                stmt = insert(googleads_table('googleads_'+user.worksapce)).values(
                    dated=day,
                    account=row.get('account_id'),
                    account_name=row.get('account_name'),
                    campaignid=row.get('campaign_id'),
                    campaign_name=row.get('campaign_name'),
                    adgroupid=row.get('ad_group_id'),
                    adgroup_name=row.get('ad_group_name'),
                    adid=row.get('ad_id'),
                    adname=row.get('ad_name'),
                    impression=row.get('impressions'),
                    clicks=row.get('clicks'),
                    spend=row.get('spend')
                )

                # Specify the ON CONFLICT DO UPDATE behavior
                do_update_stmt = stmt.on_conflict_do_update(
                    index_elements=['dated','adid'],  # Conflict target
                    set_=dict(impression=stmt.excluded.impression, clicks=stmt.excluded.clicks, spend=stmt.excluded.spend)
                )
        except Exception as e:
            print(f'Error: {e.msg}')
    db.session.commit()

