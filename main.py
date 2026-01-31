# run.py

from flask import Flask,jsonify,request,redirect

from .api_web.login_routes import auth_bp
from .api_web.setting_route import setting_bp
from .external.routes import external_bp
from .client_auth_bridge.google.google_service_handler import google_bp
from .client_auth_bridge.facebook.facebook_service_handler import facebook_bp
from .client_auth_bridge.linkedin.linkedinads_service_handler import linkedinads_bp
from .integration.payment_gateway.razorpay import payment_bp
from .integration.payment_gateway.instamojo import payment_bp
from .integration.payment_gateway.cashfree import payment_bp
from .integration.payment_gateway.paypal import payment_bp
from .integration.payment_gateway.stripe import payment_bp
from .integration.channel.gohighlevel import channel_bp
from .integration.channel.woocommerce import channel_bp
from .integration.channel.tagmango import channel_bp
from .integration.channel.shopify import channel_bp
from .integration.channel.pabbly import channel_bp
from .integration.channel.zoho import channel_bp
from .api_web.reporting_routes import report_bp
from .api_web.creative_routes import creative_bp
from .api_web.behaviour_routes import behaviour_bp
from .api_web.dashboard_routes import dashboard_bp
from .api_web.integration_routes import intgration_cd
from .api_web.product_routes import product_bp
from .chat_bot.mongo_bot import chatbot_cd
from .chat_bot.sql_bot import chatbot_cd
from .payment import trackocitypayment_bp
from .connection import create_app, jwt, db
from .db_model.sql_models import UserRegister,UserSubaccountRegister,Payment
from datetime import datetime, timedelta
import psutil


from flask_cors import CORS, cross_origin
from flask_jwt_extended import verify_jwt_in_request, jwt_required, create_access_token
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
import time, json , requests

import tracemalloc

# os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
# Set-ExecutionPolicy Unrestricted -Scope Process


app = create_app()

# CORS(app, resources={r"/*": {"origins": "*"}})
CORS(app)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(setting_bp, url_prefix='/setting')
app.register_blueprint(intgration_cd, url_prefix='/integration')
app.register_blueprint(external_bp, url_prefix='/external')
app.register_blueprint(google_bp, url_prefix='/google')
app.register_blueprint(facebook_bp, url_prefix='/facebook')
app.register_blueprint(linkedinads_bp, url_prefix='/linkedinads')
app.register_blueprint(report_bp, url_prefix='/reporting')
app.register_blueprint(creative_bp, url_prefix='/creative')
app.register_blueprint(behaviour_bp, url_prefix='/behaviour')
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
app.register_blueprint(payment_bp, url_prefix='/clientpayment')
app.register_blueprint(channel_bp, url_prefix='/clientchannel')
app.register_blueprint(chatbot_cd, url_prefix='/chatbot')
app.register_blueprint(trackocitypayment_bp, url_prefix='/trackocitypayment')
app.register_blueprint(product_bp, url_prefix='/product')

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


@app.route('/api/orders', methods=['GET', 'OPTIONS'])
@cross_origin(origins='*', methods=['GET', 'OPTIONS'], headers=['Content-Type'])
def get_orders():
    api_key = request.args.get('api_key')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    user = UserRegister.query.filter_by(workspace=api_key).first()
    if not user or user.isactive is False:
        return jsonify({"message":"Non Authorized"}), 400
    
    ordertable = f"order_{api_key}"
    sql_query = db.text(f"""SELECT id, order_date, transcation_id , total, first_name, email, phone  FROM {ordertable} WHERE order_date >= :start_timestamp AND order_date <= :end_timestamp""")
    result = db.session.execute(sql_query, {'start_timestamp':start_date, 'end_timestamp':end_date})
    order_data = result.fetchall()
    # Return structured data instead of array
    orders = [
        {
            'id': order.id,
            'order_date': order.order_date.isoformat() if order.order_date else None,
            'transaction_id': order.transcation_id,
            'total': float(order.total) if order.total else 0,
            'customer': {
                'first_name': order.first_name,
                'email': order.email,
                'phone': order.phone
            }
        }
        for order in order_data
    ]
    
    return jsonify({
        'success': True,
        'count': len(orders),
        'orders': orders
    }), 200



@app.route('/googlesheetuser', methods=['GET', 'OPTIONS'])
@cross_origin(origins='*', methods=['GET', 'OPTIONS'], headers=['Content-Type'])
def googlesheet_user():
    api_key = request.args.get('api_key')
    if api_key != 'hisd8gi385ho0dfn49js80943tggbo934t90ge':
        return jsonify({"message":"Non Authorized"}), 400

    user = UserRegister.query.order_by(UserRegister.id.desc()).all()
    header = ['id','complete_name','email','phone','created_at','plan_till','product_type',' tag']
    data = []
    data.append(header)
    for usr in user:
        row = [usr.id, usr.complete_name, usr.email, usr.phone, usr.created_at, usr.plan_till, usr.product_type, usr.tag]
        data.append(row)
    return jsonify(data), 200



@app.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
@cross_origin()
def refresh():
    headers = request.headers
    userid = headers.get('workspaceId', None)
    new_access_token = create_access_token(identity=userid, expires_delta=timedelta(minutes=3))
    return jsonify({"tokens": {
                "access":new_access_token}}), 200

@app.before_request
def before_request():
    headers = request.headers
    userid = headers.get('workspaceId', None)
    subaccountid = headers.get('subaccountid',None)
    if request.endpoint not in ('refresh', 'googlesheetuser','googlesheet_user', 'api/orders'):
        if userid:
            verify_jwt_in_request()
            user = UserRegister.query.filter_by(workspace=userid).first()
            subaccount = UserSubaccountRegister.query.filter_by(id=subaccountid).first() 
            if user:
                user.last_activity = datetime.now()
                if datetime.now() > user.plan_till or user.isactive is False:
                    # response = payment_order_creation(user.complete_name, userid, user.plan_till, user.email, user.phone, user.currency)
                    user.isactive = False
                    return jsonify({"message": "Subscription Expired"}), 406
                # if datetime.now() + timedelta(days=3) > user.plan_till and user.isactive:
                #     payment_order_creation(user.complete_name, userid, user.plan_till, user.email, user.phone, user.currency)
                db.session.commit()
            
            if subaccount:
                    subaccount.last_activity = datetime.now()
                    if user:
                        if datetime.now() > user.plan_till or user.isactive is False:
                            user.isactive = False
                            return jsonify({"message": "Subscription Expired"}), 406                                               
                    db.session.commit()


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


def payment_order_creation(name, workspace, plan_till, email, phone='1212121212', currency='INR', product='standard'):
    payment = Payment.query.filter(workspace==workspace).first()
    if payment:
        return payment.link
    url = "https://connect.pabbly.com/workflow/sendwebhookdata/IjU3NjUwNTY1MDYzMDA0MzQ1MjZmNTUzZDUxMzYi_pc"
    payload = json.dumps({'status': 'pending',
    'currency': currency if currency else 'INR',
    'name': name,
    'email': email,
    'phone': phone if phone else '1212121212',
    'product': product,
    'startat':max(datetime.now()+timedelta(days=1), plan_till).timestamp(), 
    'workspace':workspace,
    'total': '7078.82'})

    headers = {
    'Content-Type': 'application/json'
    }
    requests.request("POST", url, headers=headers, data=payload)
    time.sleep(5)
    payment = Payment.query.filter(workspace==workspace).first()
    if payment:
        return payment.link
    
@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()


tracemalloc.start()
@app.route("/memory-stats")
def detailed_memory_stats():
    snapshot = tracemalloc.take_snapshot()
     # Group by filename to identify problem modules
    top_stats = snapshot.statistics('filename')
    sqlalchemy_stats = [stat for stat in top_stats if 'sqlalchemy' in stat.traceback.filename]
    
    result = [f"SQLAlchemy memory usage: {sum(s.size for s in sqlalchemy_stats) / 1024 / 1024:.1f} MB"]
    
    # Show line-level details for SQLAlchemy
    line_stats = snapshot.statistics('lineno')
    for stat in line_stats[:5]:
        if 'sqlalchemy' in stat.traceback.filename:
            result.append(f"{stat.traceback.filename}:{stat.traceback.lineno}: {stat.size / 1024 / 1024:.1f} MB ({stat.count} objects)")
    
    return "<br>".join(result)


@app.route("/cpu-stats")
def spike_detector():
    process = psutil.Process()
    cpu = process.cpu_percent(interval=1)
    memory_mb = process.memory_info().rss / 1024 / 1024
    
    if cpu > 50 or memory_mb > 1500:  # Spike thresholds
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        return f"SPIKE DETECTED {timestamp}: CPU={cpu:.1f}% RAM={memory_mb:.1f}MB"
    
    return f"Normal: CPU={cpu:.1f}% RAM={memory_mb:.1f}MB"


if __name__ == '__main__':
    app.run(debug=False)
