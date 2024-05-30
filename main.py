# run.py

from flask import Flask,jsonify,request,redirect

from .api_web.login_routes import auth_bp
from .external.routes import external_bp
from .client_auth_bridge.google.google_service_handler import google_bp
from .client_auth_bridge.facebook.facebook_service_handler import facebook_bp
from .integration.payment_gateway.razorpay import payment_bp
from .integration.channel.woocommerce import channel_bp
from .integration.channel.shopify import channel_bp
from .integration.channel.pabbly import channel_bp
from .api_web.reporting_routes import report_bp
from .api_web.integration_routes import intgration_cd
from .payment import trackocitypayment_bp
from .connection import create_app, jwt
from .db_model.sql_models import UserRegister, Payment
from datetime import datetime, timedelta, time

from flask_cors import CORS, cross_origin
from flask_cors import CORS
from flask_jwt_extended import verify_jwt_in_request, jwt_required, create_access_token
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
import os, json , requests

# os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
# Set-ExecutionPolicy Unrestricted -Scope Process


app = create_app()

# CORS(app, resources={r"/*": {"origins": "*"}})
CORS(app)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(intgration_cd, url_prefix='/integration')
app.register_blueprint(external_bp, url_prefix='/external')
app.register_blueprint(google_bp, url_prefix='/google')
app.register_blueprint(facebook_bp, url_prefix='/facebook')
app.register_blueprint(report_bp, url_prefix='/reporting')
app.register_blueprint(payment_bp, url_prefix='/clientpayment')
app.register_blueprint(channel_bp, url_prefix='/clientchannel')
app.register_blueprint(trackocitypayment_bp, url_prefix='/trackocitypayment')

# health-check
@app.route('/health')
def health_check():
    return jsonify({'status': 'health-fine'}), 200


# jwt error handler
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_data):
    return jsonify({"message": "Token has expired", "error": "token_expired"}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({"message": "Signature Verification Failed", "error": "invalid_token"}), 401


@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({"message": "Request doesn't contain valid token", "error": "authorization_header"}), 401


@app.errorhandler(ExpiredSignatureError)
@app.errorhandler(InvalidTokenError)
def handle_invalid_token_error(error):
    return jsonify({'message': 'Invalid JWT Token or Token has expired'}), 401


@app.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
@cross_origin()
def refresh():
    headers = request.headers
    userid = headers.get('workspaceId', None)
    new_access_token = create_access_token(identity=userid, expires_delta=timedelta(hours=6))
    return jsonify({"tokens": {
                "access":new_access_token}}), 200

@app.before_request
def before_request():
    headers = request.headers
    userid = headers.get('workspaceId', None)
    if request.endpoint != 'refresh':
        if userid:
            verify_jwt_in_request()
            user = UserRegister.query.filter_by(workspace=userid).first()
            if datetime.now() > user.plan_till or user.isactive is False:
                response = payment_order_creation(user.complete_name, user.email, user.phone, user.currency)
                user.isactive = False
                return jsonify({"payment_link":response,"message": "Subscription Expired"}), 403
            if datetime.now() + timedelta(days=3) > user.plan_till and user.isactive:
                payment_order_creation(user.complete_name, user.email, user.phone, user.currency)

@app.after_request
def after_request(response):
    if 'Access-Control-Allow-Origin' not in response.headers:
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Credentials', True)
    return response


@app.errorhandler(403)  # CORS-related errors often have HTTP status code 403
def handle_cors_error(e):
    return jsonify(error="CORS error: {}".format(e.description)), 403


def payment_order_creation(name, email, phone='1212121212', currency='INR', product='standard'):
    payment = Payment.query.filter(Payment.expireon>datetime.now(),Payment.email==email).first()
    if payment:
        return payment.link
    url = "https://connect.pabbly.com/workflow/sendwebhookdata/IjU3NjUwNTZhMDYzNTA0MzQ1MjZhNTUzYzUxMzYi_pc"
    payload = json.dumps({'status': 'pending',
    'currency': currency if currency else 'INR',
    'name': name,
    'email': email,
    'phone': phone if phone else '1212121212',
    'product': product,
    'total': '4128.82'})

    headers = {
    'Content-Type': 'application/json'
    }
    requests.request("POST", url, headers=headers, data=payload)
    time.sleep(5)
    payment = Payment.query.filter(Payment.expireon>datetime.now(),Payment.email==email).first()
    if payment:
        return payment.link


if __name__ == '__main__':
    app.run()
