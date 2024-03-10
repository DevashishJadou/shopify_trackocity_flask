from flask import Blueprint, request, jsonify
from flask_cors import cross_origin

from cryptography.fernet import Fernet

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
    print(f'request:{request}')
    data = json.loads(request.data)
    headers = request.headers
    workspace = headers['workspaceId']

    # Create a Fernet cipher object with the key
    _key = os.environ.get("_KEY")
    cipher_suite = Fernet(_key)
    account = data['accountid']
    account_name = data['accountname']
    userid = data['userid']
    cipher_access_key = cipher_suite.encrypt(data['accessToken'].encode())
    cipher_email = cipher_suite.encrypt(data['email'].encode())
    expireon = data['expireon']

    user = ClientFacebookredentials.query.filter_by(workspace=workspace).first()
    if user:
        user.account = account
        user.account_name = account_name
        user.userid = userid
        user.accessToken = cipher_access_key
        user.email = cipher_email
        user.expireon = expireon
        db.session.commit()
        return jsonify({'message': 'Inforamtion Updated Succesfully'}), 200
    else:
        user_make = ClientFacebookredentials(account=account, account_name=account_name, email=cipher_email, userid=userid, expireon=expireon, _token=cipher_access_key, workspace=workspace)
        tablename = 'facebookads_'+workspace
        if not metadata.tables.get(tablename):
            facebook_table = facebookads_table(tablename)
            facebook_table.create(bind=db.engine)
        db.session.add(user_make)
        db.session.commit()

    return jsonify({'message': 'Succesfully'}), 200
