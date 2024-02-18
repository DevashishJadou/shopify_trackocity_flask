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
    import pdb
    pdb.set_trace()
    print(f'request:{request}')
    data = json.loads(request.data)
    headers = request.headers
    workspace = headers['workspace']

    # Create a Fernet cipher object with the key
    _key = os.environ.get("_Key")
    cipher_suite = Fernet(_key)
    account = data['accountid']

    user = ClientFacebookredentials.query.filter_by(workspace=workspace).first()
    if user:
        user.account = account
        db.session.commit()
        return jsonify({'message': 'Inforamtion Updated Succesfully'}), 200
    else:
        cipher_access_key = cipher_suite.encrypt(data['accessToken'].encode())
        cipher_email = cipher_suite.encrypt(data['email'].encode())
        workspace = headers['workspace']
        userid = data['userid']
        expireon = data['expireon']
        account = data['accountid']
        user_make = ClientFacebookredentials(account=account, email=cipher_email, userid=userid, expireon=expireon, _token=cipher_access_key, workspace=workspace)
        tablename = 'facebookads_'+workspace
        if not metadata.tables.get(tablename):
            facebook_table = facebookads_table(tablename)
            facebook_table.create(bind=db.engine)
        db.session.add(user_make)
        db.session.commit()

    return jsonify({'message': 'Succesfully'}), 200
