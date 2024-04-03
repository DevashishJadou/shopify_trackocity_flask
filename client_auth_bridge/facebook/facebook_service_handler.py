from flask import Blueprint, request, jsonify, session, redirect
from flask_cors import cross_origin

from cryptography.fernet import Fernet
import requests

from ...db_model.sql_models import ClientFacebookredentials, facebookads_table
from ...connection import db
# from db_model import sql_models, facebookads

import os, json
from sqlalchemy import MetaData

metadata = MetaData()


facebook_bp = Blueprint('facebook', __name__)

@facebook_bp.route("/clientcredentials", methods=['POST', 'OPTIONS'])
@cross_origin(origins='*', methods=['POST'], headers=['Content-Type'])
def authorize_endpoint():
    data = json.loads(request.data)
    headers = request.headers
    workspace = headers['workspaceId']

    # Create a Fernet cipher object with the key
    _key = os.environ.get("_KEY")
    cipher_suite = Fernet(_key)
    account = data['accountid']
    account_name = data['accountname']
    userid = data['userid']
    cipher_access_key = cipher_suite.encrypt(data['accessToken'].encode()).decode()
    # cipher_access_key=data['accessToken']
    # cipher_email = cipher_suite.encrypt(data['email'].encode()).decode()
    # cipher_email=data['email']
    expireon = data['expireon']

    user = ClientFacebookredentials.query.filter_by(workspace=workspace).first()
    if user:
        user.account = account
        user.account_name = account_name
        user.userid = userid
        user.accesstoken = cipher_access_key
        # user.email = cipher_email
        user.expireon = expireon
        db.session.commit()
        return jsonify({'message': 'Inforamtion Updated Succesfully'}), 200
    else:
        user_make = ClientFacebookredentials(account=account, account_name=account_name, userid=userid, expireon=expireon, accesstoken=cipher_access_key, workspace=workspace)
        tablename = 'facebookads_'+workspace
        if not metadata.tables.get(tablename):
            facebook_table = facebookads_table(tablename)
            facebook_table.create(bind=db.engine)
        db.session.add(user_make)
        db.session.commit()

    return jsonify({'message': 'Succesfully'}), 200


_APP_ID = os.environ.get("_APP_ID")
_FBREDIRECT_URI = os.environ.get("_FBREDIRECT_URI")
_FB_VER = os.environ.get("_FB_VER")
_SECRET_KEY = os.environ.get("_SECRET_KEY")
_CLIENT_URL = os.environ.get("_CLIENT_URL")
@facebook_bp.route('/login')
def login():
    # Generate a random string for the state parameter
    state = os.urandom(16).hex()
    session['state'] = state

    # Redirect to Facebook's OAuth Dialog
    oauth_dialog_url = (
        f'https://www.facebook.com/{_FB_VER}/dialog/oauth?client_id={_APP_ID}'
        f'&redirect_uri={_FBREDIRECT_URI}&state={state}&scope=email,ads_read'
    )
    return redirect(oauth_dialog_url)



@facebook_bp.route('/callback')
def callback():
    # Verify the state parameter to protect against CSRF attacks
    state = request.args.get('state')
    if state != session.get('state'):
        return 'State mismatch. Authentication failed.', 400

    # Exchange the code for an access token
    code = request.args.get('code')
    token_exchange_url = (
        f'https://graph.facebook.com/{_FB_VER}/oauth/access_token?client_id={_APP_ID}'
        f'&redirect_uri={_FBREDIRECT_URI}&client_secret={_SECRET_KEY}&code={code}'
    )
    response = requests.get(token_exchange_url)
    data = response.json()

    if 'access_token' not in data:
        return 'Failed to obtain access token.', 400

    short_lived_token = data['access_token']

    # Exchange the short-lived token for a long-lived token
    long_lived_token_url = (
        f'https://graph.facebook.com/{_FB_VER}/oauth/access_token?grant_type=fb_exchange_token'
        f'&client_id={_APP_ID}&client_secret={_SECRET_KEY}'
        f'&fb_exchange_token={short_lived_token}'
    )
    response = requests.get(long_lived_token_url)
    long_lived_data = response.json()

    if 'access_token' in long_lived_data:
        # Store the long-lived access token in the session and redirect to the profile page
        session['access_token'] = long_lived_data['access_token']
        return redirect('/facebook/profile')
    else:
        return 'Failed to obtain long-lived access token.', 400

@facebook_bp.route('/profile')
def profile():
    # Use the access token to access the user's profile
    access_token = session.get('access_token')
    if not access_token:
        return redirect(os.environ.get("_CLIENT_URL")+"/integration")

    ad_accounts_url = f'https://graph.facebook.com/me/adaccounts?access_token={access_token}&fields=id,name'
    response = requests.get(ad_accounts_url)
    ad_accounts = response.json()

    if 'data' in ad_accounts:
        ad_accounts_list = [f"{account['name']}/{account['id']}" for account in ad_accounts['data']]

    return redirect(_CLIENT_URL+"/integration?resource_names="+str(ad_accounts_list.json)) 
