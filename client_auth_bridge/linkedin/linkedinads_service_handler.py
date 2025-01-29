from flask import Blueprint, request, session, redirect, jsonify
from ...db_model.sql_models import ClientLinkedinCredentials, otherads_table
import os
from sqlalchemy import MetaData
from ...connection import db

from flask_cors import cross_origin
import requests
import json

linkedinads_bp = Blueprint('linkedinads', __name__)

metadata = MetaData()





@linkedinads_bp.route("/getaccounts", methods=['POST','OPTIONS'])
@cross_origin(origins='*', methods=['POST', 'OPTIONS'], headers=['Content-Type'])
def fetch_authenticated_user_details():
    headers = request.headers
    body = request.args
    token = body.get('token')
    op = {}

    url_accesstoken = "https://www.linkedin.com/oauth/v2/accessToken?grant_type=authorization_code&code="+token+"&redirect_uri=https%3A%2F%2Fapp.trackocity.io%2Fintegration&client_id=86ldwctf7zb6a0&client_secret=WPL_AP1.63N7ClabLLvPTMJX.7dHt6A=="
    response = requests.get(url_accesstoken)
    result = response.json()
    
    access_token = result.get('access_token')
    
    
    url = 'https://api.linkedin.com/rest/adAccountUsers?q=authenticatedUser'
    headers = {
        'X-Restli-Protocol-Version': '2.0.0',
        'LinkedIn-Version': '202409',
        'Authorization': f'Bearer {access_token}'
    }

    try:
        response = requests.get(url, headers=headers)
        op['account'] = response.json()
        op['auth'] = result
        return op
    except requests.exceptions.RequestException as e:
        print(f"Error fetching authenticated user details: {e}")
        return {"error": str(e)}




@linkedinads_bp.route("/createaccount", methods=['POST', 'OPTIONS'])
@cross_origin(origins='*', methods=['POST', 'OPTIONS'], headers=['Content-Type'])
def linkedinads_clientcreate():
    headers = request.headers
    workspace = headers.get('workspaceId')
    row = json.loads(request.data)
    systemid = row.get("systemid", request.args.get("systemid",None))

    if systemid:
        user = ClientLinkedinCredentials.query.filter_by(id=systemid).first()
        user.access_token = row.get('token')
        user.account_name = row.get('account_name')
        user.account = row.get('account')
        user.expire_in = row.get('expire_in')
        user.refresh_token = row.get('refresh_token')
        user.refresh_token_expire_in = row.get('refresh_token_expire_in')
        db.session.commit()
    else:
        user = ClientLinkedinCredentials(workspace=workspace, access_token=row.get('token'), account_name=row.get('account_name'), account=row.get('account'), expire_in=row.get('expire_in'), refresh_token=row.get('refresh_token'), refresh_token_expire_in=row.get('refresh_token_expire_in'))
        tablename = 'otherads_'+workspace
        try:
            if not metadata.tables.get(tablename):
                linkedin_table = otherads_table(tablename)
                linkedin_table.create(bind=db.engine)
        except:
            pass
        db.session.add(user)
        db.session.commit()

    return jsonify(message='Account added'), 201