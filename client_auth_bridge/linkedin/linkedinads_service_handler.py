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
    workspace = headers.get('workspaceId')
    body = request.args
    token = body.get('token')
    # token = f"AQX3I-nZUjvRiFp0MU5eka7TAxMT0AZx3etESEf1M2qTBQU8-keNaHL6L1zEQNklhsOlBBuYgj7gxuB-4LNL4wCf3BTi_t3yLe47UnmBRMhu7V7tx8LndMsUI55eIruXDZrSD8v6bDz8V2iRnit0WzFIZ_74obNuooEYpW2fOM19c32YVfdAMBSl7Q9jWQdg9XI_cJRin1Yzu0Fhsy1O8VYagC2MrN8St6KvLFpKmgRV_nGnp5APy9uxa8O-23Q9TIXz9mFGV2bsCgoIs-InAAzf-ZfkrCZVVuzrxCftHQiA4vX1rKOfYseUpW1fJOIZyXXP7Gn4IaJzMFnG8SR2N_5756UgJg"
    
    url = 'https://api.linkedin.com/rest/adAccountUsers?q=authenticatedUser'
    headers = {
        'X-Restli-Protocol-Version': '2.0.0',
        'LinkedIn-Version': '202409',
        'Authorization': f'Bearer {token}'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for HTTP codes 4xx/5xx
        return response.json()
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