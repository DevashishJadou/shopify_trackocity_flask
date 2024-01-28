from flask import Flask

from .api_web.login_routes import auth_bp
from .external.routes import external_bp
from .client_auth_bridge.google.google_service_handler import google_bp
from .client_auth_bridge.facebook.facebook_service_handler import facebook_bp
from .integration.payment_gateway.razorpay import payment_bp
from .integration.channel.woocommerce import channel_bp
from .api_web.reporting_routes import report_bp
from .connection import create_app

app = create_app()

# Register blueprints

# app.register_blueprint(auth_bp, url_prefix='/auth')
# app.register_blueprint(external_bp, url_prefix='/external')
# app.register_blueprint(google_bp, url_prefix='/google')
# app.register_blueprint(facebook_bp, url_prefix='/facebook')
# app.register_blueprint(report_bp, url_prefix='/report')
# app.register_blueprint(payment_bp, url_prefix='/clientpayment')
# app.register_blueprint(channel_bp, url_prefix='/clientchannel')
