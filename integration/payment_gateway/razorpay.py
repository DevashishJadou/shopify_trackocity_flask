from flask import Blueprint, request, jsonify
import json, os
from datetime import datetime, timedelta
from flask_cors import cross_origin

import razorpay
from sqlalchemy import MetaData
from sqlalchemy import text

# from db_model.sql_models import RazorpayConfiguration, order_table_dynamic, ordertable
# from connection import db
from ...db_model.sql_models import UserRegister, RazorpayConfiguration, order_table_dynamic, ordertable, ordertable_detail
from ...connection import db
from ...dbrule import dup_order_rule

from sqlalchemy.sql import func

metadata = MetaData()
payment_bp = Blueprint('clientpayment', __name__)
ENCRYPTION_KEY = os.environ.get('_ENCYPT_KEY')

@payment_bp.route('/razorpaycredentials', methods=['POST'])
@cross_origin()
def razorpay_params():
    header = request.headers
    _body = json.loads(request.get_data())
    workspace = header.get('workspaceId')
    _razorpay_api_secret = 'tmp'
    _razorpay_api_key = 'tmp'
    _razorpay_client_secret = 'tmp'

    user = RazorpayConfiguration.query.filter_by(workspace=workspace).first()
    if user:
        user.razorpay_api_secret = _razorpay_api_secret
        user.razorpay_api_key = _razorpay_api_key
        user.razorpay_client_secret = _razorpay_client_secret
        db.session.commit()
        return jsonify({'message': 'Already Connected'}), 200

    else:
        razorpay_register = RazorpayConfiguration(workspace=workspace, razorpay_api_secret=_razorpay_api_secret, razorpay_api_key=_razorpay_api_key, razorpay_client_secret=_razorpay_client_secret, active=True)
        db.session.add(razorpay_register)
        tablename = 'order_'+workspace
        ordetail_tablename = 'order_detailed_'+workspace
        try:
            if not metadata.tables.get(tablename):
                razorpay_table = ordertable(tablename)
                order_detail_table = ordertable_detail(ordetail_tablename)
                try:
                    razorpay_table.create(bind=db.engine)
                    order_detail_table.create(bind=db.engine)
                except:
                    pass
        except Exception as e:
            print(f'Razorpay Connect: {e.msg}')
            return jsonify({'error': 'Something went Wrong'}), 500
    db.session.commit()

    return jsonify({'message': 'success'}), 200


@payment_bp.route('/<workspace>/razorpaywebhook', methods=['POST'])
def razorpay_webhook(workspace):
    # {"entity":"event","account_id":"acc_IXN05ypMrY0Yrn","event":"order.paid","contains":["payment","order"],
    # "payload":{"payment":{"entity":{"id":"pay_N8cPI5YAONeJKz","entity":"payment","amount":39900,"currency":"INR",
    # "base_amount":39900,"status":"captured","order_id":"order_N8cP7QVPZ4J9so","invoice_id":null,
    # "international":false,"method":"upi","amount_refunded":0,"amount_transferred":0,"refund_status":null,
    # "captured":true,"description":"IROF","card_id":null,"bank":null,"wallet":null,"vpa":"9554708419@paytm",
    # "email":"redsha95@gmail.com","contact":"+919554708419",
    # "notes":{"order_signature":"55cefa46e2b7622026471e1393130056447cf9f4eb19b0b86811bbec21ddf026",
    # "sio_order_item_id":5659823},"fee":942,"tax":144,"error_code":null,"error_description":null,"error_source":null,
    # "error_step":null,"error_reason":null,"acquirer_data":{"rrn":"333923598646"},"created_at":1701769369,
    # "provider":null,"upi":{"payer_account_type":"bank_account","vpa":"9554708419@paytm"}}},
    # "order":{"entity":{"id":"order_N8cP7QVPZ4J9so","entity":"order","amount":39900,"amount_paid":39900,
    # "amount_due":0,"currency":"INR","receipt":"5659823","offer_id":"offer_N4HDpTNUQeMoGe",
    # "offers":["offer_N4HDpTNUQeMoGe"],"status":"paid","attempts":1,
    # "notes":{"order_signature":"55cefa46e2b7622026471e1393130056447cf9f4eb19b0b86811bbec21ddf026",
    # "sio_order_item_id":5659823},"created_at":1701769359}}},"created_at":1701769395}

    
    user = UserRegister.query.filter_by(workspace=workspace).first()
    if not user.isactive:
        jsonify({'status': 'Unauthorized'}), 403

    signature = request.headers.get('X-Razorpay-Signature')
    razorpay_client = RazorpayConfiguration.query.filter_by(workspace=workspace).first()

    webhook_secret = razorpay_client.razorpay_api_secret
    webhook_key = razorpay_client.razorpay_api_key
    client_secret = razorpay_client.razorpay_client_secret

    request_data = request.get_data()
    client = razorpay.Client(auth=(webhook_key, webhook_secret))
    # verify = client.utility.verify_webhook_signature(request_data.decode("utf-8"), signature, client_secret)


    # if not verify:
    #     return jsonify({'error': 'Invalid signature'}), 400
    
    tablename = 'order_'+workspace
    orderTable = order_table_dynamic(tablename)
    orderTable.metadata = db.Model.metadata


    # Parse the JSON data from the request
    data = json.loads(request_data)

    # Process the webhook event based on the event type
    event_type = data.get('event')

    if user.isleadgen:
        payload = data.get('payload').get('payment').get('entity')
        if razorpay_client.active and event_type in ('order.paid', 'payment.captured', 'subscription.charged'):
            order_obj = orderTable.query.filter_by(email=payload.get('email')).first()
            payment_id = payload.get('id')
            total = payload.get('amount')/100.0
            currency = payload.get('currency')
            email = payload.get('email')
            phone = payload.get('contact')
            event_time = datetime.fromtimestamp(data.get('created_at')) + timedelta(hours=float(user.timezone_value))
            if not order_obj:
                order_obj = orderTable.query.filter_by(phone=payload.get('contact')).first()
            if order_obj:
                order_obj.transcation_id = payment_id
                order_obj.total = total
                order_obj.currency = currency
                order_obj.email = email
                order_obj.phone = phone
                order_obj.email_encrypt = func.pgp_sym_encrypt(email, ENCRYPTION_KEY)
                order_obj.phone_encrypt = func.pgp_sym_encrypt(phone, ENCRYPTION_KEY)
                order_obj.email_secure = func.pgp_digest(email)
                order_obj.phone_secure = func.pgp_digest(phone)
                order_obj.converted_date = event_time
            else:
                order_obj = orderTable.query.filter_by(transcation_id=payment_id).first()
                email_encrypt = func.pgp_sym_encrypt(email, ENCRYPTION_KEY)
                phone_encrypt = func.pgp_sym_encrypt(phone, ENCRYPTION_KEY)
                email_secure = func.pgp_digest(email)
                phone_secure = func.pgp_digest(phone)
                if order_obj is None:
                    order_make = orderTable(order_date=event_time, transcation_id=payment_id, email=email, phone=phone, email_encrypt=email_encrypt, phone_encrypt=phone_encrypt, email_secure=email_secure, phone_secure=phone_secure, payment_method='Prepaid', total=amount, currency=currency)
                    db.session.add(order_make)
            db.session.commit()

    elif razorpay_client.active and event_type in ('order.paid', 'payment.captured', 'subscription.charged'):
        try:
            # Handle payment captured event
            payload = data.get('payload').get('payment').get('entity')
            payment_id = payload.get('id')
            amount = payload.get('amount')/100.0
            currency = payload.get('currency')
            email = payload.get('email')
            phone = payload.get('contact')
            event_time = datetime.fromtimestamp(data.get('created_at')) + timedelta(hours=float(user.timezone_value))
            
            order_obj = orderTable.query.filter_by(transcation_id=payment_id).first()
            if order_obj is None:
                email_encrypt = func.pgp_sym_encrypt(email, ENCRYPTION_KEY)
                phone_encrypt = func.pgp_sym_encrypt(phone, ENCRYPTION_KEY)
                email_secure = func.pgp_digest(email)
                phone_secure = func.pgp_digest(phone)
                order_make = orderTable(order_date=event_time, transcation_id=payment_id, email=email, phone=phone, email_encrypt=email_encrypt, phone_encrypt=phone_encrypt, email_secure=email_secure, phone_secure=phone_secure, payment_method='Prepaid', total=amount, currency=currency)
                db.session.add(order_make)
            db.session.commit()
            return jsonify({'status': 'success'}), 200
        except Exception as e:
            print(f'Error razorpay webhook:{e.args}')
            return jsonify({'status': 'success'}), 200
    
    if razorpay_client.active and event_type in ('refund.processed'):
        try:
            order_obj = orderTable.query.filter_by(transcation_id=payment_id).first()
            if order_obj:
                order_obj.order_status = 'cancelled'
            else:
                email_encrypt = func.pgp_sym_encrypt(email, ENCRYPTION_KEY)
                phone_encrypt = func.pgp_sym_encrypt(phone, ENCRYPTION_KEY)
                email_secure = func.pgp_digest(email)
                phone_secure = func.pgp_digest(phone)
                order_make = orderTable(order_date=event_time, transcation_id=payment_id, email=email, phone=phone, email_encrypt=email_encrypt, phone_encrypt=phone_encrypt, email_secure=email_secure, phone_secure=phone_secure, payment_method='Prepaid', total=amount, currency=currency, order_status='cancelled')
                db.session.add(order_make)
            db.session.commit()
            return jsonify({'status': 'success'}), 200
        except Exception as e:
            print(f'Error razorpay webhook:{e.args}')
            return jsonify({'status': 'success'}), 400


    return jsonify({'status': 'success'}), 200
