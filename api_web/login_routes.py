# routes.py

from ..db_model.sql_models import UserRegister
from ..connection import db
# from db_model.sql_models import UserRegister
# from connection import db
# from ..logger  import auth_logger

from flask import Blueprint, request, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token

import random, string
from uuid import uuid4
from datetime import timedelta
import json
from flask_cors import cross_origin

from cryptography.fernet import Fernet

from google.cloud import logging
import os

root_dir = os.path.abspath(os.path.dirname(__file__))
_credential_path = "stagging-trackocity_logger_key.json"
_CLIENT_SECRET_PATH = os.path.join(root_dir, _credential_path)
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = _CLIENT_SECRET_PATH

auth_bp = Blueprint('auth', __name__)

# Instantiates a client
logging_client = logging.Client()

def auth_logger(log_name, text, functionality):
    # The name of the log to write to
    log_name = "signin"
    logger = logging_client.logger(log_name)

    log = {
            "logName": log_name,
            "resource": {"type": "global"},
            "textPayload": {text},
            "labels": {"functionality": {functionality}},
        }
    auth_logger.log_struct(log)

    return logger, log_name


def encrpyt(data):
    _key = str.encode(os.environ.get("_KEY"))
    cipher_suite = Fernet(_key)
    return cipher_suite.encrypt(data.encode())

def decrpyt(data):
    _key = str.encode(os.environ("_KEY"))
    cipher_suite = Fernet(_key)
    return cipher_suite.decrypt(data.encode())


def cros_handle():
    response = make_response()
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Methods', 'POST, PUT, OPTIONS')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Credentials', True)
    return response


@auth_bp.route('/create', methods=['POST', 'OPTIONS'])
@cross_origin(origins='*', methods=['POST', 'OPTIONS'], headers=['Content-Type'])
def user_registor():

    log_name = "signin"

    data = json.loads(request.data)
    # Check if the user exists
    user = UserRegister.query.filter_by(email=data['email']).first() is not None

    if user:
        # text = f"User already exist: {encrpyt(data['email'])}"
        # text = f"User already exist: {data['email']}"
        # auth_logger(log_name, text, "Signin")        
        return jsonify(message='User already exist'), 409

    workspace = uuid4().hex

    _hassed_password = generate_password_hash(str(data.get('password')))

    user = UserRegister(complete_name=data['name'], email=data['email'], phone=data['phone'], _password=_hassed_password, workspace=workspace)
    db.session.add(user)
    db.session.commit()

    
    # text = f"User created: email: {encrpyt(data['email'])}"
    text = f"User created: email: {data['email']}"
    # auth_logger(log_name, text, "Signup") 
    return jsonify(message='User created', user_id=user.workspace), 201




@auth_bp.route('/login', methods=['POST', 'OPTIONS'])
@cross_origin(origins='*', methods=['OPTIONS', 'POST'], headers=['Content-Type'])
def login_user():

    log_name = "signin"
    # auth_logger = logging_client.logger(log_name)

    data = json.loads(request.data)

    username = data.get('username')
    password = data.get('password')

    # Check if the user exists
    user = UserRegister.query.filter_by(email=username).first()

    if user is None:
        # text = f"User don't exist: email: {encrpyt(data['email'])}"
        # auth_logger(log_name, text, "Signin") 
        return jsonify({"message":'Invalid username or password', "user_id":None}), 404

    if not check_password_hash(user._password, str(password)):
        # text = f"Unauthorized: email:{sdata['email']}"
        # text = f"Unauthorized: email:{encrpyt(data['email'])}"
        # auth_logger(log_name, text, "Signin") 
        return jsonify({"message":'Unauthorized', "user_id":None}), 404
    else:
        access_token = create_access_token(identity=username, expires_delta=timedelta(hours=1))
        # refresh_token = create_refresh_token(identity=username)
        # text = f"Signin: email:{data['email']}"
        # text = f"Signin: email:{encrpyt(data['email'])}"
        # auth_logger(log_name, text, "Signin") 
        return jsonify({"message":"Logged In", 
            "tokens": {
                "access":access_token
                # "refresh": refresh_token
            },
            "user_id":user.workspace
            }), 200