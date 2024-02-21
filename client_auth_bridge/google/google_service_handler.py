# from db_model.sql_models import UserRegister
# from connection import db
from flask import Blueprint, request, jsonify, session, redirect
from ...db_model.sql_models import UserRegister
from ...connection import db
import random, string
import os

from flask_cors import cross_origin

# from client_auth_bridge.google.auth import authorize, oauth2client
# from client_auth_bridge.google.gads_account_access import list_accessible_customer
# from client_auth_bridge.google.gads_client import handleException
from .auth import authorize, oauth2client
from .gads_account_access import list_accessible_customer
from .gads_client import handleException

_CLIENT_URL = os.environ.get("_CLIENT_URL")

google_bp = Blueprint('google', __name__)
sess = {}

@google_bp.route("/authorize")
def authorize_endpoint():
    auth_info = authorize()
    passthrough_val = auth_info['passthrough_val']
    sess['passthrough_val'] = passthrough_val
    url = auth_info['authorization_url']
    return redirect(url)



@google_bp.route("/oauth2callback")   
def oauth2callback_endpoint():
    token = request.args.get("token")
    passthrough_val = sess.get("passthrough_val")
    state = request.args.get("state")
    code = request.args.get("code")
    refresh_token = oauth2client(passthrough_val, state, code, token)
    session['refresh_token'] = refresh_token
    resource_names = customers()
    return redirect(_CLIENT_URL+"/integration?resource_names="+str(resource_names.json))

    

@google_bp.route("/customers")
@cross_origin()
def customers():
    headers =  request.headers
    try:
        token = session['refresh_token']
    except:
        token = request.args.get("refresh_token")
    if not sess.get('userid'):
        sess['userid'] = headers.get("workSpaceId")
    try:
        resource_names = list_accessible_customer(token, sess['userid'])
        return resource_names
    except Exception as ex:
        return handleException(ex)
