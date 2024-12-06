from flask import Blueprint, request, session, redirect
import os

from flask_cors import cross_origin

# from client_auth_bridge.google.auth import authorize, oauth2client
# from client_auth_bridge.google.gads_account_access import list_accessible_customer
# from client_auth_bridge.google.gads_client import handleException
from .auth import authorize, oauth2client
from .gads_account_access import list_accessible_customer, clientaccount_googleads
from .gads_client import handleException

_CLIENT_URL = os.environ.get("_CLIENT_URL")

google_bp = Blueprint('google', __name__)
sess = {}


@google_bp.route("/authorize/<id>")
def authorize_endpoint(id):
    auth_info = authorize()
    passthrough_val = auth_info['passthrough_val']
    sess['passthrough_val'] = passthrough_val
    session['passthrough_val'] = passthrough_val
    url = auth_info['authorization_url']
    sess['systemid'] = id
    session['systemid'] = id
    return redirect(url)



@google_bp.route("/oauth2callback")   
def oauth2callback_endpoint():
    token = request.args.get("token")
    passthrough_val = sess.get("passthrough_val")
    state = request.args.get("state")
    code = request.args.get("code")
    refresh_token = oauth2client(passthrough_val, state, code, token)
    session['refresh_token'] = refresh_token
    systemeid = sess.get('systemid', session.get('systemid', None))
    resource_names = customers()
    return redirect(_CLIENT_URL+"/integration?resource_names="+str(resource_names.json)+"&refresh_token="+str(refresh_token)+"&systemid="+systemeid)

    

@google_bp.route("/customers")
@cross_origin()
def customers():
    try:
        token = session['refresh_token']
    except:
        token = request.args.get("refresh_token")
    try:
        resource_names = list_accessible_customer(token)
        return resource_names
    except Exception as ex:
        return handleException(ex)


@google_bp.route("/clientaccount", methods=['POST', 'OPTIONS'])
@cross_origin(origins='*', methods=['OPTIONS', 'POST'], headers=['Content-Type'])
def clientaccount():
    headers =  request.headers
    userid = headers.get("workSpaceId")
    token = request.args.get("refresh_token")
    systemid = request.args.get("systemid")
    if systemid in ('undefined', 'Null', 'null'):
        systemid = None
    id = int(systemid) if systemid else None
    accounts = request.args.get("customerId")
    for acc in accounts.split(','):
        account = (acc.split('/')[-1]).strip()
        accname = (acc.split('/')[-2]).strip()
        accname = accname[:32]
        status = clientaccount_googleads(userid, account, accname, token, id)
    return status

