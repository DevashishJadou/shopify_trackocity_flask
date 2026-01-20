# routes.py

from ..db_model.sql_models import UserRegister, AgencyRegister, UserSubaccountRegister,UserSubaccountRelation,EmailChange, order_table_dynamic, UserSubdomain, UserOnboarding,AdminUser
from ..connection import db, mail, app
# from db_model.sql_models import UserRegister
# from connection import db
# from ..logger  import auth_logger

from flask import Blueprint, request, redirect, jsonify, make_response
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token, decode_token

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from uuid import uuid4
from datetime import timedelta, datetime
import os, json, random
from collections import defaultdict

from flask_cors import cross_origin
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired

from cryptography.fernet import Fernet

from sqlalchemy import desc, asc

s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
_SERVER=os.environ.get("_SERVER")
_CLIENT_URL=os.environ.get("_CLIENT_URL")
_LOGIN_CLIENT_ID = os.environ.get("_GOOGLE_LOGIN")
# _LOGIN_CLIENT_ID="584653501344-crmnj96c8eq4kp2j7rki31rbtb5flmuf.apps.googleusercontent.com"
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


# def send_verification_email(user_email, token):
#     msg = Message('Email Verification', sender="integation@trackocity.io", recipients=[user_email])
#     msg.body = f"""
#     Please click on the link to verify your email. 
#     This Link is active for 2 days: {_SERVER}/auth/verify/{token}

#     Regards,
#     Team Trackocity
#     """
#     mail.send(msg)

def send_verification_email(user_email, token, user_name=None):
    """
    Professional email verification with Trackocity branding
    """
    
    # HTML email template with your brand colors
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Email Verification - Trackocity</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 0; background-color: #f4f4f4;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 0; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
            
            <!-- Header with Trackocity Branding -->
            <div style="background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="margin: 0 0 15px 0; font-size: 32px; font-weight: 600; text-align: center;">Trackocity</h1>
                <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">Welcome to our platform!</p>
            </div>
            
            <!-- Main Content -->
            <div style="padding: 40px 30px;">
                <h2 style="color: #333; font-size: 24px; margin-bottom: 20px;">
                    {"Hello " + user_name + "!" if user_name else "Hello!"}
                </h2>
                
                <p style="color: #666; font-size: 16px; margin-bottom: 20px;">
                    Thank you for signing up with <strong>Trackocity</strong>! We're excited to have you on board.
                </p>
                
                <p style="color: #666; font-size: 16px; margin-bottom: 30px;">
                    To complete your registration and secure your account, please verify your email address by clicking the button below:
                </p>
                
                <!-- Verification Button -->
                <div style="text-align: center; margin: 40px 0;">
                    <a href="{_SERVER}/auth/verify/{token}" 
                       style="display: inline-block; background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%); 
                              color: white; padding: 15px 30px; text-decoration: none; border-radius: 50px; 
                              font-size: 16px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;
                              box-shadow: 0 4px 15px rgba(255, 107, 53, 0.4);">
                        Verify Email Address
                    </a>
                </div>
                
                <!-- Security Notice -->
                <div style="border-left: 4px solid #ffc107; background-color: #fff8e1; padding: 15px; margin: 30px 0; border-radius: 0 8px 8px 0;">
                    <p style="color: #333; font-size: 14px; margin: 0;">
                        <strong>⚡ Important:</strong> This verification link will expire in <strong>48 hours</strong> for security reasons. 
                        If you didn't create an account with Trackocity, please ignore this email.
                    </p>
                </div>
                
                <!-- Important Password Reset Note -->
                <div style="border-left: 4px solid #28a745; background-color: #f8fff9; padding: 15px; margin: 30px 0; border-radius: 0 8px 8px 0;">
                    <p style="color: #333; font-size: 14px; margin: 0;">
                        <strong>📝 Important Note:</strong> After completing verification, click <strong>Forgot Password</strong> to reset your password, and then log in with the new credentials.
                    </p>
                </div>
                
                <p style="color: #666; font-size: 16px; margin: 30px 0 20px 0;">
                    Once verified, you'll have access to Trackocity features and can start exploring our platform.
                </p>
                
                <p style="color: #666; font-size: 16px;">
                    Need help? Feel free to <a href="mailto:contact@trackocity.io" style="color: #ff6b35; text-decoration: none; font-weight: 500;">contact our support team</a> - we're here to assist you!
                </p>
            </div>
            
            <!-- Footer -->
            <div style="background-color: #f8f9fa; padding: 30px; text-align: center; border-radius: 0 0 10px 10px; border-top: 1px solid #e9ecef;">
                <p style="color: #666; font-size: 14px; margin: 0 0 15px 0;">
                    Best regards,<br>
                    <strong>The Trackocity Team</strong>
                </p>
                
                <p style="color: #999; font-size: 12px; margin: 15px 0 0 0;">
                    © 2024 Trackocity. All rights reserved.<br>
                    This email was sent to {user_email}
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text fallback for email clients that don't support HTML
    text_template = f"""
    Welcome to Trackocity!
    
    {"Hello " + user_name + "!" if user_name else "Hello!"}
    
    Thank you for signing up with Trackocity! We're excited to have you on board.
    
    To complete your registration and secure your account, please verify your email address by clicking the link below:
    
    {_SERVER}/auth/verify/{token}
    
    Important: This verification link will expire in 48 hours for security reasons.
    
    Once verified, you'll have full access to all Trackocity features and can start exploring our platform.
    
    Need help? Contact our support team at contact@trackocity.io
    
    Best regards,
    The Trackocity Team
    
    © 2025 Trackocity. All rights reserved.
    This email was sent to {user_email}
    """
    
    # Create the message with professional sender display
    msg = Message(
        subject='Welcome to Trackocity - Please Verify Your Email',
        sender=("Trackocity", "noreply@trackocity.io"),  # Display name + email
        recipients=[user_email],
        reply_to="contact@trackocity.io"  # Where replies go
    )
    
    msg.body = text_template  # Plain text version (fallback)
    msg.html = html_template  # HTML version (main)
    
    try:
        mail.send(msg)
        print(f"✅ Professional verification email sent to {user_email}")
        return True
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
        return False



# def send_forgetpassword_email(user_email, token):
#     msg = Message('Reset Password', sender="integation@trackocity.io", recipients=[user_email])
#     msg.body = f'Click the link to reset your password: {_CLIENT_URL}/reset-password?{token}'
#     mail.send(msg)

def send_forgetpassword_email(user_email, token, user_name=None):
    """
    Professional password reset email with Trackocity branding
    """
    
    # HTML email template with Trackocity theme
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Password Reset - Trackocity</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 0; background-color: #f4f4f4;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 0; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
            
            <!-- Header with Trackocity Branding -->
            <div style="background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="margin: 0 0 15px 0; font-size: 32px; font-weight: 600; text-align: center;">Trackocity</h1>
                <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">Password Reset Request</p>
            </div>
            
            <!-- Main Content -->
            <div style="padding: 40px 30px;">
                <h2 style="color: #333; font-size: 24px; margin-bottom: 20px;">
                    {"Hello " + user_name + "!" if user_name else "Hello!"}
                </h2>
                
                <p style="color: #666; font-size: 16px; margin-bottom: 20px;">
                    We received a request to reset the password for your <strong>Trackocity</strong> account.
                </p>
                
                <p style="color: #666; font-size: 16px; margin-bottom: 30px;">
                    If you requested this password reset, please click the button below to create a new password:
                </p>
                
                <!-- Reset Password Button -->
                <div style="text-align: center; margin: 40px 0;">
                    <a href="{_CLIENT_URL}/reset-password?{token}" 
                       style="display: inline-block; background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%); 
                              color: white; padding: 15px 30px; text-decoration: none; border-radius: 50px; 
                              font-size: 16px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;
                              box-shadow: 0 4px 15px rgba(255, 107, 53, 0.4);">
                        Reset My Password
                    </a>
                </div>
                
                <!-- Security Notice -->
                <div style="border-left: 4px solid #dc3545; background-color: #fff5f5; padding: 15px; margin: 30px 0; border-radius: 0 8px 8px 0;">
                    <p style="color: #333; font-size: 14px; margin: 0;">
                        If you didn't request this password reset, please ignore this email or contact our support team immediately.
                    </p>
                </div>
                
                <p style="color: #666; font-size: 16px;">
                    Need help? Feel free to <a href="mailto:contact@trackocity.io" style="color: #ff6b35; text-decoration: none; font-weight: 500;">contact our support team</a> - we're here to assist you!
                </p>
            </div>
            
            <!-- Footer -->
            <div style="background-color: #f8f9fa; padding: 30px; text-align: center; border-radius: 0 0 10px 10px; border-top: 1px solid #e9ecef;">
                <p style="color: #666; font-size: 14px; margin: 0 0 15px 0;">
                    Best regards,<br>
                    <strong>The Trackocity Team</strong>
                </p>
                
                <p style="color: #999; font-size: 12px; margin: 15px 0 0 0;">
                    © 2024 Trackocity. All rights reserved.<br>
                    This email was sent to {user_email}
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text fallback
    text_template = f"""
    Password Reset Request - Trackocity
    
    {"Hello " + user_name + "!" if user_name else "Hello!"}
    
    We received a request to reset the password for your Trackocity account.
    
    If you requested this password reset, please click the link below to create a new password:
    
    {_CLIENT_URL}/reset-password?{token}
    
    If you didn't request this password reset, please ignore this email or contact our support team immediately.
    
    Need help? Contact our support team at contact@trackocity.io
    
    Best regards,
    The Trackocity Team
    
    © 2024 Trackocity. All rights reserved.
    This email was sent to {user_email}
    """
    
    # Create the message with professional sender display
    msg = Message(
        subject='Reset Your Trackocity Password',
        sender=("Trackocity", "noreply@trackocity.io"),
        recipients=[user_email],
        reply_to="contact@trackocity.io"
    )
    
    msg.body = text_template
    msg.html = html_template
    
    try:
        mail.send(msg)
        print(f"✅ Professional password reset email sent to {user_email}")
        return True
    except Exception as e:
        print(f"❌ Error sending password reset email: {str(e)}")
        return False

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
    email = data['email'].lower()
    islead = data.get('isLead', None)

    # Check if the user exists
    user = UserRegister.query.filter_by(email=email).first() is not None
    agency = AgencyRegister.query.filter_by(email=email).first() is not None
    subaccount = UserSubaccountRegister.query.filter_by(email=email).first() is not None
    if user or agency or subaccount:       
        return jsonify(message='User already exist'), 409

    if data.get('account_type', None) == 'agency':
        workspace = uuid4().hex
        _hassed_password = generate_password_hash(str(data.get('password')))
        productid = random.randint(100000000, 999999999)
        
        user = AgencyRegister(complete_name=data['name'], email=email, phone=data['phone'], _password=_hassed_password, workspace=workspace, productid=productid)
        db.session.add(user)
        db.session.commit()

        token = s.dumps(email, salt='email-verify')
        send_verification_email(email, token)

        return jsonify(message='Please check your email', user_id=user.workspace), 201

    elif data.get('account_type',None) == 'individual':
        workspace = uuid4().hex
        _hassed_password = generate_password_hash(str(data.get('password')))
        productid = random.randint(100000000, 999999999)
        plantill = datetime.now() + timedelta(days=14)

        subdomain = UserSubdomain.query.filter_by(status=False).first()
        subdomain.status = True

        user = UserRegister(complete_name=data['name'], email=email, phone=data['phone'], _password=_hassed_password, workspace=workspace, productid=productid, plan_till=plantill, subdomain=subdomain.subdomain, isleadgen=islead)
        db.session.add(user)
        db.session.commit()
        
        user_onboarding = UserOnboarding(user_id=workspace,onboarding_status='not_started',created_at=datetime.now())
        db.session.add(user_onboarding)
        db.session.commit()
        

        token = s.dumps(email, salt='email-verify')
        send_verification_email(email, token)

        return jsonify(message='Please check your email to verify your account', user_id=user.workspace), 201
    
    else:
        subaccount = UserSubaccountRegister(complete_name=data['name'],email=email,created_at=datetime.now(),access_level=data.get('role'))
        db.session.add(subaccount)
        db.session.flush()
            
        subaccount = UserSubaccountRegister.query.filter_by(email=email).first()
            
        # Adding data to relation table
        for selected_user in data.get('account access'):
            user = UserRegister.query.filter_by(workspace=selected_user).first()
            relation = UserSubaccountRelation(user_register_id=user.id , user_subaccount_id=subaccount.id)    
            db.session.add(relation) 
            
        db.session.commit()       
                            
        # Send verification email
        token = s.dumps(email, salt='email-verify')
        send_verification_email(email, token)
            
        return jsonify(message='Please check your email to verify your account'), 201




@auth_bp.route('/login', methods=['POST', 'OPTIONS'])
@cross_origin(origins='*', methods=['OPTIONS', 'POST'], headers=['Content-Type'])
def login_user():
    data = json.loads(request.data)

    username = data.get('username')
    password = data.get('password')
    token = data.get("token")
    email_verified = False

    if token:
        idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), _LOGIN_CLIENT_ID)
        username = idinfo['email']
        email_verified = idinfo.get('email_verified', False)

    username = username.lower()		       
    # ============================================
    # NEW: CHECK IF THIS IS AN ADMIN LOGIN FIRST
    # ============================================
    
    admin = AdminUser.query.filter_by(email=username).first()
    if admin and admin.is_active:
        if email_verified:
            # Update last login timestamp
            admin.last_login = datetime.now()
            db.session.commit()
        
            # Get most recently active client (same as agency behavior)
            client = UserRegister.query.filter(UserRegister.isactive.is_(True)).order_by(desc(UserRegister.last_activity)).first()
        
            # If no active clients exist, return error
            if not client:
                return jsonify({"message": "No active clients found"}), 404
                             
            # Get client onboarding status
            onboarding = UserOnboarding.query.filter_by(user_id=client.workspace).first()
            onboarding_status = onboarding.onboarding_status if onboarding else None
        
            # Create admin JWT tokens (6 hours access, 15 days refresh)
            admin_access_token = create_access_token(identity=username,expires_delta=timedelta(hours=6))
            admin_refresh_token = create_refresh_token(identity=username,expires_delta=timedelta(days=15))
        
            # Return admin login response (agency-style behavior)
            return jsonify({
                "message": "Logged In",
                "tokens": {
                    "access": admin_access_token,
                    "refresh": admin_refresh_token
                },
                "user_id": client.workspace,       
                "is_admin": True,                  
                "adminid": admin.email,            
                "isleadgen": client.isleadgen,
                "onboarding_status": onboarding_status
            }), 200
    
        if check_password_hash(admin._password, str(password)):
            # Update last login timestamp
            admin.last_login = datetime.now()
            db.session.commit()
        
            # Get most recently active client (same as agency behavior)
            client = UserRegister.query.filter(UserRegister.isactive.is_(True)).order_by(desc(UserRegister.last_activity)).first()
        
            # If no active clients exist, return error
            if not client:
                return jsonify({"message": "No active clients found"}), 404
            
            # Get client onboarding status
            onboarding = UserOnboarding.query.filter_by(user_id=client.workspace).first()
            onboarding_status = onboarding.onboarding_status if onboarding else None
        
            # Create admin JWT tokens (6 hours access, 15 days refresh)
            admin_access_token = create_access_token(identity=username,expires_delta=timedelta(hours=6))
            admin_refresh_token = create_refresh_token(identity=username,expires_delta=timedelta(days=15))
        
            # Return admin login response (agency-style behavior)
            return jsonify({
                "message": "Logged In",
                "tokens": {
                    "access": admin_access_token,
                    "refresh": admin_refresh_token
                },
                "user_id": client.workspace,       
                "is_admin": True,                  
                "adminid": admin.email,            
                "isleadgen": client.isleadgen,
                "onboarding_status": onboarding_status
            }), 200
        
        else:
            # Password verification failed
            return jsonify({"message": "Invalid username or password", "user_id": None})  						  
    # Check if the user exists
    user = UserRegister.query.filter_by(email=username).first()
    agency = AgencyRegister.query.filter_by(email=username).first()
    subaccount = UserSubaccountRegister.query.filter_by(email=username).first()
    

    if user is None and agency is None and subaccount is None and email_verified:
        return jsonify({"message":'User Not Found', "user_id":None}), 404

    if user is None and agency is None and subaccount is None:
        return jsonify({"message":'Invalid Username or Password', "user_id":None}), 404
    
    if user:
        onboarding = UserOnboarding.query.filter_by(user_id=user.workspace).first()
        onboarding_status = onboarding.onboarding_status if onboarding else None

        if email_verified:
            access_token = create_access_token(identity=username, expires_delta=timedelta(minutes=5))
            refresh_token = create_refresh_token(identity=username, expires_delta=timedelta(days=2))
            return jsonify({"message":"Logged In", 
                "tokens": {
                    "access":access_token,
                    "refresh": refresh_token
                },
                "user_id":user.workspace,
                "isleadgen": user.isleadgen,
                "onboarding_status": onboarding_status
                }), 200

        if not check_password_hash(user._password, str(password)):
            return jsonify({"message":'Invalid username or password', "user_id":None}), 406
        if user.isverify is None or user.isverify is False:
            return jsonify({"message":'Please verify your email address by clicking the verification link sent to your email inbox', "user_id":None}), 406
        else:
            access_token = create_access_token(identity=username, expires_delta=timedelta(hours=6))
            refresh_token = create_refresh_token(identity=username, expires_delta=timedelta(days=15))
            return jsonify({"message":"Logged In", 
                "tokens": {
                    "access":access_token,
                    "refresh": refresh_token
                },
                "user_id":user.workspace,
                "isleadgen": user.isleadgen,
                "onboarding_status": onboarding_status
                }), 200
    
    if agency:
        if email_verified:
            access_token = create_access_token(identity=username, expires_delta=timedelta(hours=6))
            refresh_token = create_refresh_token(identity=username, expires_delta=timedelta(days=15))
            return jsonify({"message":"Logged In", 
                "tokens": {
                    "access":access_token,
                    "refresh": refresh_token
                },
                "user_id":user.workspace if user else None,
                "isagency":True,
                "agency_id": agency.workspace
                }), 200
        user = UserRegister.query.filter_by(agencyid=agency.id).order_by(desc(UserRegister.last_activity)).first()
        
        if not check_password_hash(agency._password, str(password)):
            return jsonify({"message":'Invalid username or password', "user_id":None}), 406
        if agency.isverify is None or agency.isverify is False:
            return jsonify({"message":'Please verify your email address by clicking the verification link sent to your email inbox', "user_id":None}), 406
        else:
            access_token = create_access_token(identity=username, expires_delta=timedelta(hours=6))
            refresh_token = create_refresh_token(identity=username, expires_delta=timedelta(days=15))
            return jsonify({"message":"Logged In", 
                "tokens": {
                    "access":access_token,
                    "refresh": refresh_token
                },
                "user_id":user.workspace if user else None,
                "isagency":True,
                "agency_id": agency.workspace
                }), 200

    if subaccount:
        if email_verified:
            accessible_relations = UserSubaccountRelation.query.filter_by(user_subaccount_id=subaccount.id).all()
            accessible_user_ids = [rel.user_register_id for rel in accessible_relations]
        
            user = UserRegister.query.filter(UserRegister.id.in_(accessible_user_ids)).order_by(desc(UserRegister.last_activity)).first()
        
            if not user:
                return jsonify({"message": "No accessible accounts found", "user_id": None}), 403
                    
            access_token = create_access_token(identity=username, expires_delta=timedelta(hours=6))
            refresh_token = create_refresh_token(identity=username, expires_delta=timedelta(days=15))
            
            # Scenario 1:-
            if user.agencyid is None:
                return jsonify({
                "message":"Logged In", 
                "tokens": {
                    "access":access_token,
                    "refresh": refresh_token
                },
                "user_id": user.workspace,
                "subaccountid":subaccount.id,
                "issubaccount":True,
                "role": subaccount.access_level
            }), 200
            
            # Scenario 2 :-
            else:
                agency = AgencyRegister.query.filter_by(id=user.agencyid).first()
                return jsonify({
                "message":"Logged In", 
                "tokens": {
                    "access":access_token,
                    "refresh": refresh_token
                },
                "user_id": user.workspace,
                "subaccountid":subaccount.id,
                "issubaccount":True,
                "role": subaccount.access_level,
                "isagency":True,
                "agency_id": agency.workspace
            }), 200
                
        if subaccount.isverify is None or subaccount.isverify is False:
            return jsonify({"message":'Please verify your email address by clicking the verification link sent to your email inbox', "user_id":None}), 406
        if subaccount._password is None:
            return jsonify({"message":'Please reset your password by clicking the forget password link', "user_id":None}), 406
        if not check_password_hash(subaccount._password, str(password)):
            return jsonify({"message": "Invalid username or password", "user_id": None}), 406
        if subaccount.isverify is None or subaccount.isverify is False:
            return jsonify({"message":'Please verify your email address by clicking the verification link sent to your email inbox', "user_id":None}), 406
        else:
            accessible_relations = UserSubaccountRelation.query.filter_by(user_subaccount_id=subaccount.id).all()
            accessible_user_ids = [rel.user_register_id for rel in accessible_relations]
        
            user = UserRegister.query.filter(UserRegister.id.in_(accessible_user_ids)).order_by(desc(UserRegister.last_activity)).first()
        
            if not user:
                return jsonify({"message": "No accessible accounts found", "user_id": None}), 403
                    
            access_token = create_access_token(identity=username, expires_delta=timedelta(hours=6))
            refresh_token = create_refresh_token(identity=username, expires_delta=timedelta(days=15))
            
            # Scenario 1:-
            if user.agencyid is None:
                return jsonify({
                "message":"Logged In", 
                "tokens": {
                    "access":access_token,
                    "refresh": refresh_token
                },
                "user_id": user.workspace,
                "subaccountid":subaccount.id,
                "issubaccount":True,
                "role": subaccount.access_level
            }), 200
            
            # Scenario 2 :-
            else:
                agency = AgencyRegister.query.filter_by(id=user.agencyid).first()
                return jsonify({
                "message":"Logged In", 
                "tokens": {
                    "access":access_token,
                    "refresh": refresh_token
                },
                "user_id": user.workspace,
                "subaccountid":subaccount.id,
                "issubaccount":True,
                "role": subaccount.access_level,
                "isagency":True,
                "agency_id": agency.workspace
            }), 200



@auth_bp.route('/verify/<token>')
def verify_email(token):
    try:
        email = s.loads(token, salt='email-verify', max_age=7*24*3600)  # Token expires in 7 days
        user = UserRegister.query.filter_by(email=email).first()
        if user is None:
           user = AgencyRegister.query.filter_by(email=email).first()            
        if user is None:
            user = UserSubaccountRegister.query.filter_by(email=email).first()																												   
        user.isverify = True
        user.isactive = True
        db.session.commit()
        return redirect(_CLIENT_URL+"/email-verify")
    except:
        db.session.rollback()
        return 'The verification link is invalid or has expired.'
    


@auth_bp.route('/forgetpassword', methods=['POST', 'OPTIONS'])
@cross_origin(origins='*', methods=['OPTIONS', 'POST'], headers=['Content-Type'])
def forget_password():
    data = json.loads(request.data)
    username = data.get('username')

    user = UserRegister.query.filter_by(email=username).first()
    if user is None:
        user = AgencyRegister.query.filter_by(email=username).first()
    if user is None:
        user = UserSubaccountRegister.query.filter_by(email=username).first()																								 
    if user is None:
        user = AdminUser.query.filter_by(email=username).first()				
    if user:
        token = s.dumps(username, salt='password-reset')
        send_forgetpassword_email(username, token)
        return jsonify({"message":"An email with instructions to reset your password has been sent"}),200
    else:
        return jsonify({"message":"Email not found"}),400



@auth_bp.route('/resetpassword', methods=['GET', 'POST', 'OPTIONS'])
@cross_origin()
def reset_password():
    data = json.loads(request.data)
    token = data.get('refreshtoken')
    try:
        email = s.loads(token, salt='password-reset', max_age=7200)
    except SignatureExpired:
        return jsonify({"message":"The password reset link has expired. Please request a new link"}), 400
  
    if request.method == 'POST':
        user = UserRegister.query.filter_by(email=email).first()
        if user is None:
            user = AgencyRegister.query.filter_by(email=email).first()
        if user is None:
            user = UserSubaccountRegister.query.filter_by(email=email).first()				
        if user is None:
            user = AdminUser.query.filter_by(email=email).first() 																							 
        user._password = generate_password_hash(str(data.get('newpassword')))
        user.isactive = True
        db.session.commit()
        return jsonify({"message":"Your password has been reset"}),200


@auth_bp.route('/subaccountusers', methods=['GET', 'OPTIONS'])
@cross_origin()
def subaccount_users():
    headers = request.headers
    userid = headers.get('workspaceId')
    data = []
    
    user = UserRegister.query.filter_by(workspace=userid).first()
    agency = AgencyRegister.query.filter_by(workspace=userid).first()
    
    if user:
        subaccount_ids = UserSubaccountRelation.query.filter_by(user_register_id=user.id).all()
        for subaccount_id in subaccount_ids:
            subaccount = UserSubaccountRegister.query.filter_by(id=subaccount_id.user_subaccount_id).first()
            data.append({
                "subaccountid":subaccount.id,
                "email":subaccount.email,
                "name":subaccount.complete_name,
                "role":subaccount.access_level,
                "status":subaccount.isactive,
                "account access":"All Accounts",
                "last active":subaccount.last_activity.strftime('%Y-%m-%d') if subaccount.last_activity else None
            })
            
        return jsonify(data), 200
    
    if agency:
        # Get all ids from user_register table that belong to that agency
        agency_user_ids = [user.id for user in UserRegister.query.filter_by(agencyid=agency.id).all()]
        
        # Now , this will returns ALL rows from relation table where user_register_id 
        subaccount_relations = UserSubaccountRelation.query.filter(UserSubaccountRelation.user_register_id.in_(agency_user_ids)).all()
        
        # extracts subaccount IDs
        subaccount_ids = list(set([rel.user_subaccount_id for rel in subaccount_relations]))
        
        for subaccount_id in subaccount_ids:
            
            subaccount = UserSubaccountRegister.query.filter_by(id=subaccount_id).first()
            
            accessible_relations = UserSubaccountRelation.query.filter_by(user_subaccount_id=subaccount_id).filter(UserSubaccountRelation.user_register_id.in_(agency_user_ids)).all()
            
            accessible_users = []
            
            for rel in accessible_relations:
                user = UserRegister.query.filter_by(id=rel.user_register_id).first()
                accessible_users.append({
                    "name":user.complete_name,
                    "workspace":user.workspace
                })
                
            data.append({
                "subaccountid":subaccount.id,
                "email":subaccount.email,
                "name":subaccount.complete_name,
                "role":subaccount.access_level,
                "status":subaccount.isactive,
                "account access":accessible_users,
                "last active":subaccount.last_activity.strftime('%Y-%m-%d') if subaccount.last_activity else None
            })
        
        return jsonify(data), 200    
            
            
    
@auth_bp.route('/updatesubaccountusers', methods=['PUT', 'OPTIONS'])
@cross_origin()
def subaccount_user_change():
    headers = request.headers
    userid = headers.get('workspaceId')
    subaccountid = headers.get('subaccountid')
    data = json.loads(request.data)
    
    # Get subaccount
    subaccount = UserSubaccountRegister.query.filter_by(id=subaccountid).first()
    
    if not subaccount:
        return jsonify({"message": "Subaccount not found"}), 404
    
    if subaccount.access_level != data.get('role'):
        subaccount.is_role_changed = True
        
    # Update basic fields
    subaccount.complete_name = data.get('name')
    subaccount.access_level = data.get('role')
    
    # Check if requester is an agency
    agency = AgencyRegister.query.filter_by(workspace=userid).first()
    
    if agency:
        # Get all clients of this agency
        agency_clients = UserRegister.query.filter_by(agencyid=agency.id).all()
        agency_client_ids = [client.id for client in agency_clients]
        
        # Delete old relations (only for this agency's clients)
        UserSubaccountRelation.query.filter(
            UserSubaccountRelation.user_subaccount_id == subaccountid,
            UserSubaccountRelation.user_register_id.in_(agency_client_ids)
        ).delete(synchronize_session=False)
        
        # Add new relations based on accessible_accounts
        accessible_workspaces = data.get('account access', [])
        
        for workspace in accessible_workspaces:
            client = UserRegister.query.filter_by(workspace=workspace).first()
            if client and client.agencyid == agency.id:  # Ensure client belongs to this agency
                new_relation = UserSubaccountRelation(
                    user_register_id=client.id,
                    user_subaccount_id=subaccount.id
                )
                db.session.add(new_relation)
    
    db.session.commit()
    return jsonify({"message": "Subaccount Updated"}), 200



@auth_bp.route('/deletesubaccount', methods=['DELETE', 'OPTIONS'])
@cross_origin()
def delete_subaccount():    
    try:
        headers = request.headers
        userid = headers.get('workspaceId')
        subaccountid = headers.get('subaccountid')
        
        # Validation
        if not subaccountid:
            return jsonify({'error': 'Subaccount ID is required'}), 400
        
        try:                       
            #Now,Subaccount_register table 
            subaccount = UserSubaccountRegister.query.filter_by(id=subaccountid).first()
            
            if not subaccount:
                db.session.rollback()
                return jsonify({'error': 'Subaccount not found'}), 404
            
            # subaccount_rel table data deleting
            UserSubaccountRelation.query.filter_by(user_subaccount_id=subaccountid).delete()
            
            db.session.delete(subaccount)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Subaccount deleted successfully',
                'subaccount_id': subaccountid
            }), 200
            
        except Exception as e:
            db.session.rollback()
            print(f"Database error: {str(e)}")
            raise e
            
    except Exception as e:
        print(f"Error deleting subaccount: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to delete subaccount'
        }), 500


@auth_bp.route('/getprofile', methods=['GET', 'OPTIONS'])
@cross_origin()
def profile_user():
    isagency = False
    headers = request.headers
    userid = headers.get('workspaceId')
    data = {}

    user = UserRegister.query.filter_by(workspace=userid).first()
    if user is None:
        user = AgencyRegister.query.filter_by(workspace=userid).first()
        isagency = True
    data['email'] = user.email
    data['phone'] = user.phone
    data['name'] = user.complete_name
    data['timezone'] = user.timezone
    data['company'] = user.company
    data['currency'] = user.currency
    data['plan_till'] = user.plan_till if isagency is False else None

    return jsonify(data), 200



@auth_bp.route('/updateprofile', methods=['PUT', 'OPTIONS'])
@cross_origin()
def profile_user_change():
    headers = request.headers
    userid = headers.get('workspaceId')
    data = json.loads(request.data)

    # Check if the user exists
    user = UserRegister.query.filter_by(workspace=userid).first()
    if user:
        try:
            match = data.get('timezone').split(" ")[0].replace('(GMT','').replace(')','') .split(':')
            if match:
                offset_hours = int(match[0])
                offset_minutes = int(match[1])
                total_offset = offset_hours + offset_minutes / 60
                user.timezone_value = total_offset
        except:
            pass
    else:
        user = AgencyRegister.query.filter_by(workspace=userid).first()

    user.phone = data.get('phone')
    user.complete_name = data.get('name')
    user.currency = data.get('currency')
    user.company = data.get('company')
    user.timezone = data.get('timezone')

    db.session.commit()
        
    return jsonify({"message":"Profile Updated"}), 200



@auth_bp.route('/createclient', methods=['POST', 'OPTIONS'])
@cross_origin()
def profile_client_create():
    headers = request.headers
    userid = headers.get('workspaceId')
    data = json.loads(request.data)
    email = data.get('email',None)
    islead = data.get('isLead', None)

    agency = UserRegister.query.filter_by(email=email).first() is not None
    if agency:       
        return jsonify(message='User already exist'), 409
      
    workspace = uuid4().hex
    productid = random.randint(100000000, 999999999)
    plantill = datetime.now() + timedelta(days=4)
    if not email:
        email = workspace + "@client.com"
    agency = AgencyRegister.query.filter_by(workspace=userid).first()
    subdomain = UserSubdomain.query.filter_by(status=False).first()
    subdomain.status = True
    user = UserRegister(complete_name=data['name'], email=email, phone=data.get('phone',None), workspace=workspace, productid=productid, account_type='individual', agencyid=agency.id, isactive=True, plan_till=plantill, timezone=data['timezone'], company=data['company'], currency=data['currency'], subdomain=subdomain.subdomain, isleadgen=islead)
    db.session.add(user)
    db.session.commit()
    
    user_onboarding = UserOnboarding(user_id=workspace,onboarding_status='not_started',created_at=datetime.now())
    db.session.add(user_onboarding)
    db.session.commit()
    

    return jsonify(message='Client Created', user_id=user.workspace), 201




@auth_bp.route('/getclient', methods=['GET', 'OPTIONS'])
@cross_origin()
def profile_client():
    headers = request.headers
    userid = headers.get('workspaceId',None)
    subaccounid = headers.get('subaccountid',None)
    admin_gmail = headers.get('adminid',None)
    client_data = []
    # import pdb; pdb.set_trace()
    if admin_gmail:
        admin = AdminUser.query.filter_by(email=admin_gmail).first()
        if admin is None:
            return jsonify(client_data), 200        
        all_clients = UserRegister.query.filter(UserRegister.isactive.is_(True)).order_by(desc(UserRegister.id)).all()
        
        for client in all_clients:
            client_data.append({
                'email': client.email,
                'phone': client.phone,
                'name': client.complete_name,
                'timezone': client.timezone,
                'company': client.company,
                'currency': client.currency,
                'workspace': client.workspace,
                'isleadgen': client.isleadgen
                })
        return jsonify(client_data), 200
    
    elif subaccounid:
        subaccount = UserSubaccountRegister.query.filter_by(id=subaccounid).first()
        if subaccount is None: 
            return jsonify(client_data), 200
        
        accessible_relations = UserSubaccountRelation.query.filter_by(user_subaccount_id=subaccounid).all()
        accessible_user_ids = [rel.user_register_id for rel in accessible_relations]
        clients = UserRegister.query.filter(UserRegister.id.in_(accessible_user_ids)).order_by(asc(UserRegister.id)).all()
        
        for user in clients:        
            # Store the data for each client in a nested dictionary
            client_data.append({
                'email': user.email,
                'phone': user.phone,
                'name': user.complete_name,
                'timezone': user.timezone,
                'company': user.company,
                'currency': user.currency,
                'workspace': user.workspace,
                'isleadgen': user.isleadgen
                })
            
        return jsonify(client_data), 200
        
    else:
        agency = AgencyRegister.query.filter_by(workspace=userid).first()
        clients = UserRegister.query.filter_by(agencyid = agency.id).order_by(asc(UserRegister.id)).all()
        for user in clients:
            # Store the data for each client in a nested dictionary
            client_data.append({
                'email': user.email,
                'phone': user.phone,
                'name': user.complete_name,
                'timezone': user.timezone,
                'company': user.company,
                'currency': user.currency,
                'workspace': user.workspace,
                'isleadgen': user.isleadgen
                })
        return jsonify(client_data), 200    
                


@auth_bp.route('/switchclient', methods=['GET', 'OPTIONS'])
@cross_origin()
def client_switch():
    headers = request.headers
    userid = headers.get('workspaceId')
    client_data = []
    
    # Step 3: Get JWT token from Authorization header
    auth_header = headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({"error": "Authorization token required"}), 401
    
    # Step 4: Extract and decode token
    token = auth_header.replace('Bearer ', '')
    try:
        decoded_token = decode_token(token)
        caller_email = decoded_token['sub']  # This is the email used in login
    except:
        return jsonify({"error": "Invalid token"}), 401
    
    # ============================================
    # NEW: Check if caller is ADMIN
    # ============================================
    admin = AdminUser.query.filter_by(email=caller_email).first()
    if admin:
        # Admin sees ALL clients (individual + agency clients)
        all_clients = UserRegister.query.filter(UserRegister.isactive.is_(True)).order_by(desc(UserRegister.id)).all()
        
        for client in all_clients:
            client_data.append({"name": client.complete_name,"workspace": client.workspace,"isleadgen": client.isleadgen})
        return jsonify(client_data), 200
    
    subaccount = UserSubaccountRegister.query.filter_by(email=caller_email).first()

    if subaccount is None: 
        # Check if the user exists
        user = UserRegister.query.filter_by(workspace=userid).first()  
        clients = UserRegister.query.filter_by(agencyid = user.agencyid).order_by(asc(UserRegister.id)).all()
        
        for client in clients:
            client_data.append({"name":client.complete_name, "workspace":client.workspace, "isleadgen": client.isleadgen})
        
        return jsonify(client_data), 200
     
    else:
        accessible_relations = UserSubaccountRelation.query.filter_by(user_subaccount_id=subaccount.id).all()
        accessible_user_ids = [rel.user_register_id for rel in accessible_relations]
        clients = UserRegister.query.filter(UserRegister.id.in_(accessible_user_ids)).order_by(asc(UserRegister.id)).all()
        
        for client in clients:
            client_data.append({"name":client.complete_name,"workspace":client.workspace,"isleadgen": client.isleadgen})
        return jsonify(client_data), 200
def generate_otp(length=4):
    """Generate a random OTP of given length."""
    import string
    digits = string.digits
    return ''.join(random.choice(digits) for _ in range(length))


def send_verification_change_email(to_email, otp, validity_minutes=30):
    subject = "OTP - Email Verification"
    body = f"""
    Dear User,

    The OTP to change your email is {otp}.
    In case you have not requested the OTP, please ignore this email. The OTP is valid for {validity_minutes} minutes only.

    Regards,
    Trackocity Team

    
    Note: This is a system generated message, please do not reply to it.
    """
    msg = Message(subject, recipients=[to_email], body=body)
    mail.send(msg)
    print(f"Email sent successfully to {to_email}")



def validate_otp(input_otp, stored_otp, stored_timestamp, validity_minutes=30):
    current_time = datetime.now()
    if input_otp != stored_otp:
        return False, "Invalid OTP."
    if current_time > stored_timestamp.replace(tzinfo=None) + timedelta(minutes=validity_minutes):
        return False, "OTP has expired."
    return True, "OTP is valid."



# Route to generate and send OTP
@auth_bp.route('/send_otp', methods=['POST'])
@cross_origin()
def send_otp():
    data = request.json
    to_email = data.get('email')
    headers = request.headers
    userid = headers.get('workspaceId')
    otp = generate_otp()
    timestamp = datetime.now()

    isexists = UserRegister.query.filter_by(email=to_email).first()
    agncyexists = AgencyRegister.query.filter_by(email=to_email).first()
    if isexists or agncyexists:
        jsonify({'message': 'Email Already Exist'}), 400

    changemail = EmailChange.query.filter_by(workspace=userid).first()
    if changemail:
        changemail.otp = otp
        changemail.created_at = timestamp
    else:
       emailchange = EmailChange(workspace=userid, otp=otp, created_at=timestamp)
       db.session.add(emailchange)
    db.session.commit()

    send_verification_change_email(to_email, otp)
    return jsonify({'message': 'OTP sent successfully'}), 200


# Route to validate OTP
@auth_bp.route('/validate_otp', methods=['PUT'])
@cross_origin()
def validate_otp_route():
    data = request.json
    input_otp = data.get('otp')
    email = data.get('email')
    headers = request.headers
    userid = headers.get('workspaceId')
    changemail = EmailChange.query.filter_by(workspace=userid).first()
    if changemail:
        stored_otp = changemail.otp
        stored_timestamp = changemail.created_at
        # Validate the OTP
        is_valid, message = validate_otp(input_otp, stored_otp, stored_timestamp)

        if is_valid:
            usr = UserRegister.query.filter_by(workspace=userid).first()
            usr.email = email
            message = message + ". Email is update"
            db.session.commit()
        return jsonify({'message': message, 'is_valid': is_valid}), 200