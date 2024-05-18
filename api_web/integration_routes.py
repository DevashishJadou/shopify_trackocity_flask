# integration pg

from ..db_model.sql_models import UserRegister, ClientFacebookredentials, ClientGoogleCredentials
from ..connection import db

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin


intgration_cd = Blueprint('integration', __name__)

@intgration_cd.route('/code', methods=['GET', 'OPTIONS'])
@cross_origin(origins='*', methods=['GET', 'POST', 'OPTIONS'], headers=['Content-Type'])
def code_productid():
    headers = request.headers
    workspace = headers.get('workspaceId')

    user = UserRegister.query.filter_by(workspace=workspace).first()

    if user:
        return jsonify({"productid":user.productid}), 200
    else:
        return jsonify({"message":"Workspace don't found"}), 400


@intgration_cd.route('/facebook', methods=['GET', 'OPTIONS'])
@cross_origin(origins='*', methods=['GET', 'OPTIONS'], headers=['Content-Type'])
def integration_facebbok():
    headers = request.headers
    workspace = headers.get('workspaceId')

    user = ClientFacebookredentials.query.filter_by(workspace=workspace).all()

    if user:
        accounts = {}
        for acc in user:
            accounts[acc.id] = [acc.account, acc.account_name]
        return jsonify({"accounts":accounts}), 200
    else:
        return jsonify({"message":"no account found"}), 400
    

@intgration_cd.route('/google', methods=['GET', 'OPTIONS'])
@cross_origin(origins='*', methods=['GET', 'OPTIONS'], headers=['Content-Type'])
def integration_google():
    headers = request.headers
    workspace = headers.get('workspaceId')

    user = ClientGoogleCredentials.query.filter_by(workspace=workspace).all()

    if user:
        accounts = {}
        for acc in user:
            accounts[acc.id] = [acc.account_name, acc.account_name]
        return jsonify({"accounts":accounts}), 200
    else:
        return jsonify({"message":"no account found"}), 400