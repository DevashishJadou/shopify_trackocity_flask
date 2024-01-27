from flask import Blueprint, request, jsonify
from flask_cors import cross_origin

from cryptography.fernet import Fernet

# from ...db_model import sql_models
from db_model import sql_models


facebook_bp = Blueprint('facebook', __name__)

@facebook_bp.route("/clientcredentials", methods=['POST', 'OPTIONS'])
@cross_origin(origins='*', methods=['POST'], headers=['Content-Type'])
def authorize_endpoint():
    print(f'request:{request}')
    data = request.get('data')
    headers = request.headers

    # Create a Fernet cipher object with the key
    _key = os.environ.get("_Key")
    cipher_suite = Fernet(_key)
    cipher_access_key = cipher_suite.encrypt(data['accessToken'].encode())
    cipher_email = data['email']
    workspace = headers['workspace']
    userid = data['userID']

    return 200
