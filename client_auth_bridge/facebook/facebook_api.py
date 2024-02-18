from facebook_business.adobjects.adset import AdSet
from facebook_business import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adsinsights import AdsInsights
from datetime import datetime
import time, os

from ...connection import db
from ...db_model.sql_models import ClientFacebookredentials, facebookads_table
from sqlalchemy.dialects.postgresql import insert

users = ClientFacebookredentials.query.filter_by(active=True)

current_time = datetime.now()
day = current_time.strftime("%Y-%m-%d")
hour = current_time.hour

for user in users:
    if user.id % 2 == hour % 2:
		
        #Facebook Crediantials
        _APP_ID = os.environ('_APP_ID')
        _APP_SCERET = os.environ('_SECRET_KEY')
        _ACCESS_TOKEN = user._token
        FacebookAdsApi.init(_APP_ID, _APP_SCERET, _ACCESS_TOKEN)
		
        ac_name = user.account

        account = AdAccount('act_'+ac_name)

        # Date List of last 3 days
        # base = datetime.today()
        # date_list = [base - timedelta(days=x) for x in range(5,10)]  
        # date_list = [x.strftime("%Y-%m-%d") for x in date_list]

        # today = date.today()
        # yesterday = today - timedelta(days = 1)
        #yesterday = yesterday.strftime("%Y-%m-%d")

        # for count, day in enumerate(date_list):
        # calling parameter from API 
        params={
                'level':'ad'
                }
        params['time_range'] = 'today'

        # if count == 0:
        #     params['date_preset'] = 'yesterday'
        # else:
        #     params['time_range'] = {'since': day, 'until': day}

            # To decide whether to insert or update
            # query = '''SELECT _date FROM `leadly-clients.meta_ads.fb_ads` WHERE account_id = \'''' + ac_name + '''\' and _date = \'''' + day + '''\' LIMIT 1'''
            # isexist = client.query(query)

        async_job = account.get_insights(params=params, is_async=True,
                    fields=[AdsInsights.Field.campaign_id,
                            AdsInsights.Field.campaign_name,
                            AdsInsights.Field.account_id,
                            AdsInsights.Field.account_name,
                            AdsInsights.Field.ad_id,
                            AdsInsights.Field.ad_name,
                            AdsInsights.Field.adset_id,
                            AdsInsights.Field.adset_name,                     
                            AdsInsights.Field.impressions,
                            AdsInsights.Field.inline_link_clicks,
                            AdsInsights.Field.spend												
                            ]
                    );

        async_job.api_get()
        #pdb.set_trace()
        while async_job['async_status'] != 'Job Completed' or async_job['async_percent_completion'] < 100:
            time.sleep(30)
            async_job.api_get()
        ads = async_job.get_result()

        for element in ads:
            # Define the insert statement
            stmt = insert(facebookads_table('facebookads_'+user.worksapce)).values(
                dated=day,
                account=element.get('account_id'),
                account_name=element.get('account_name'),
                campaignid=element.get('campaign_id'),
                campaign_name=element.get('campaign_name'),
                adsetid=element.get('adset_id'),
                adsetname=element.get('adset_name'),
                adid=element.get('ad_id'),
                adname=element.get('ad_name'),
                impression=element.get('impressions'),
                clicks=element.get('inline_link_clicks'),
                spend=element.get('spend')
            )

            # Specify the ON CONFLICT DO UPDATE behavior
            do_update_stmt = stmt.on_conflict_do_update(
                index_elements=['dated','adid'],  # Conflict target
                set_=dict(impression=stmt.excluded.impression, clicks=stmt.excluded.clicks, spend=stmt.excluded.spend)
            )
    db.session.commit()

