# routes.py

from ..db_model.sql_models import UserRegister
from ..connection import db, mail, app
# from db_model.sql_models import UserRegister
# from connection import db
# from ..logger  import auth_logger

from flask import Blueprint, request, redirect, jsonify, make_response, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token

from uuid import uuid4
from datetime import timedelta
import os, json, random

from flask_cors import cross_origin
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired

from cryptography.fernet import Fernet

s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
_SERVER=os.environ.get("_SERVER")
_CLIENT_URL=os.environ.get("_CLIENT_URL")
root_dir = os.path.abspath(os.path.dirname(__file__))

auth_bp = Blueprint('auth', __name__)


def encrpyt(data):
    _key = str.encode(os.environ.get("_KEY"))
    cipher_suite = Fernet(_key)
    return cipher_suite.encrypt(data.encode())

def decrpyt(data):
    _key = str.encode(os.environ("_KEY"))
    cipher_suite = Fernet(_key)
    return cipher_suite.decrypt(data.encode())


def send_verification_email(user_email, token):
    msg = Message('Email Verification', sender="integation@trackocity.io", recipients=[user_email])
    msg.body = f'Please click on the link to verify your email. This Link is active for 2 days: {_SERVER}/auth/verify/{token}'
    mail.send(msg)

def send_forgetpassword_email(user_email, token):
    msg = Message('Reset Password', sender="integation@trackocity.io", recipients=[user_email])
    msg.body = f'Click the link to reset your password: {_CLIENT_URL}/reset-password?{token}'
    mail.send(msg)

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
    data = json.loads(request.data)
    # Check if the user exists
    user = UserRegister.query.filter_by(email=data['email']).first() is not None

    if user:       
        return jsonify(message='User already exist'), 409

    workspace = uuid4().hex
    _hassed_password = generate_password_hash(str(data.get('password')))
    productid = random.randint(100000000, 999999999)

    user = UserRegister(complete_name=data['name'], email=data['email'], phone=data['phone'], _password=_hassed_password, workspace=workspace, productid=productid)
    db.session.add(user)
    db.session.commit()

    token = s.dumps(data['email'], salt='email-verify')
    send_verification_email(data['email'], token)

    return jsonify(message='Please check your email to verify your account', user_id=user.workspace), 201




@auth_bp.route('/login', methods=['POST', 'OPTIONS'])
@cross_origin(origins='*', methods=['OPTIONS', 'POST'], headers=['Content-Type'])
def login_user():
    data = json.loads(request.data)

    username = data.get('username')
    password = data.get('password')

    # Check if the user exists
    user = UserRegister.query.filter_by(email=username).first()

    if user is None:
        return jsonify({"message":'Invalid username or password', "user_id":None}), 404
    if not check_password_hash(user._password, str(password)):
        return jsonify({"message":'Invalid username or password', "user_id":None}), 401
    if user.isverify is None or user.isverify is False:
        return jsonify({"message":'Please verify your email address by clicking the verification link sent to your email inbox', "user_id":None}), 401
    else:
        access_token = create_access_token(identity=username, expires_delta=timedelta(hours=6))
        refresh_token = create_refresh_token(identity=username, expires_delta=timedelta(days=1))
        return jsonify({"message":"Logged In", 
            "tokens": {
                "access":access_token,
                "refresh": refresh_token
            },
            "user_id":user.workspace
            }), 200




@auth_bp.route('/verify/<token>')
def verify_email(token):
    try:
        email = s.loads(token, salt='email-verify', max_age=72000)  # Token expires in 1 hour
        user = UserRegister.query.filter_by(email=email).first()
        user.isverify = True
        db.session.commit()
        return redirect(_CLIENT_URL+"/sign-in")
    except:
        db.session.rollback()
        return 'The verification link is invalid or has expired.'
    


@auth_bp.route('/forgetpassword', methods=['POST', 'OPTIONS'])
@cross_origin(origins='*', methods=['OPTIONS', 'POST'], headers=['Content-Type'])
def forget_password():
    data = json.loads(request.data)
    username = data.get('username')

    user = UserRegister.query.filter_by(email=username).first()
    if user:
        token = s.dumps(username, salt='password-reset')
        send_forgetpassword_email(username, token)
        return jsonify({"message":"An email with instructions to reset your password has been sent"}),200
    else:
        return jsonify({"message":"Email not found"}),400



@auth_bp.route('/resetpassword', methods=['GET', 'POST', 'OPTIONS'])
@cross_origin()
def reset_password(token):
    data = json.loads(request.data)
    token = data.get('refreshtoken')
    try:
        email = s.loads(token, salt='password-reset', max_age=7200)
    except SignatureExpired:
        return jsonify({"message":"The password reset link has expired. Please request a new link"}), 400
  
    if request.method == 'POST':
        user = UserRegister.query.filter_by(email=email).first()
        user.password = generate_password_hash(str(data.get('newpassword')))
        return jsonify({"message":"Your password has been reset"}),200






@auth_bp.route('/profile', methods=['POST', 'OPTIONS'])
@cross_origin(origins='*', methods=['OPTIONS', 'POST'], headers=['Content-Type'])
def profile_user():
    headers = request.header
    userid = headers.get('workspaceId')
    data = json.loads(request.data)

    email = data.get('email')
    password = data.get('phone')

    # Check if the user exists
    user = UserRegister.query.filter_by(workspace=userid).first()

    if user is None:
        return jsonify({"message":'Invalid username or password', "user_id":None}), 404
    if not check_password_hash(user._password, str(password)):
        return jsonify({"message":'Invalid username or password', "user_id":None}), 401
    if user.isverify is None or user.isverify is False:
        return jsonify({"message":'Please verify your email address by clicking the verification link sent to your email inbox', "user_id":None}), 401
    else:
        access_token = create_access_token(identity=userid, expires_delta=timedelta(hours=6))
        refresh_token = create_refresh_token(identity=userid, expires_delta=timedelta(days=1))
        return jsonify({"message":"Logged In", 
            "tokens": {
                "access":access_token,
                "refresh": refresh_token
            },
            "user_id":user.workspace
            }), 200