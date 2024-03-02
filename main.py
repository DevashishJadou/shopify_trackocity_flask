# run.py

from flask import Flask,jsonify,request,redirect

from .api_web.login_routes import auth_bp
from .external.routes import external_bp
from .client_auth_bridge.google.google_service_handler import google_bp
from .client_auth_bridge.facebook.facebook_service_handler import facebook_bp
from .integration.payment_gateway.razorpay import payment_bp
from .integration.channel.woocommerce import channel_bp
from .integration.channel.shopify import channel_bp
from .api_web.reporting_routes import report_bp
from .connection import create_app, jwt
from flask_cors import CORS
from .db_model.sql_models import UserRegister
from datetime import datetime
import os

# os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
# Set-ExecutionPolicy Unrestricted -Scope Process

# from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity, jwt_expired_token_loader


app = create_app()

CORS(app, resources={r"/*": {"origins": "*"}})

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(external_bp, url_prefix='/external')
app.register_blueprint(google_bp, url_prefix='/google')
app.register_blueprint(facebook_bp, url_prefix='/facebook')
app.register_blueprint(report_bp, url_prefix='/report')
app.register_blueprint(payment_bp, url_prefix='/clientpayment')
app.register_blueprint(channel_bp, url_prefix='/clientchannel')

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

@app.before_request
def before_request():
    headers = request.headers
    userid = headers.get('workspaceId', None)
    if userid:
        user = UserRegister.query.filter_by(workspace=userid).first()
        if datetime.now() > user.plan_till or user.active is False:
            user.isactive = False
            return redirect("https://trackocity.io")

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

if __name__ == '__main__':
    app.run(debug=True)
