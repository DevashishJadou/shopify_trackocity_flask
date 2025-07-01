from flask import Blueprint, request, jsonify
import json, os
from datetime import datetime, timedelta
from flask_cors import cross_origin

from sqlalchemy import MetaData
import hashlib, random

from ...db_model.sql_models import UserRegister, order_table_dynamic, ordertable
from .woocommerce import channel_bp
from ...connection import db
from ...dbrule import dup_order_rule
from sqlalchemy.sql import func
from sqlalchemy import text


ENCRYPTION_KEY = os.environ.get('_ENCYPT_KEY')

metadata = MetaData()

@channel_bp.route('/pabblyread', methods=['GET'])
@cross_origin()
def pabbly_sent_sign():
    header = request.headers
    workspace = header.get('workspaceId')
    signature = workspace + "trackocity"
    return jsonify({'key': hashlib.sha256(signature.encode('utf-8')).hexdigest()}), 200


@channel_bp.route('/pabblycredentials', methods=['POST'])
@cross_origin()
def pabbly_integration():
    header = request.headers
    _body = json.loads(request.get_data())
    workspace = header.get('workspaceId')

    tablename = 'order_'+workspace
    try:
        if not metadata.tables.get(tablename):
            pabbly_table = ordertable(tablename)
            try:
                pabbly_table.create(bind=db.engine)
            except:
                pass
    except Exception as e:
        print(f'Pabbly integration: {e.msg}')
        return jsonify({'error': 'Something went Wrong'}), 500
    
    sql_query = db.text("select * from partition_product_create (:workspace)")
    db.session.execute(sql_query, {'workspace':workspace})
    
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    sql_query = db.text("select * from partition_monthly_create(:workspace, :year, :month)")
    db.session.execute(sql_query, {'workspace':workspace, 'year': current_year, 'month': current_month})
    db.session.commit()

    return jsonify({'message': 'success'}), 200


from datetime import datetime

def parse_date(date_str):
    if isinstance(date_str, datetime):
        return date_str
    
    try:
        # First attempt to parse the date normally
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        pass

    try:
        # Normalize spaces around colons and try again
        normalized_date_str = date_str.replace(" : ", ":").replace(": ", ":").replace(" :", ":")
        return datetime.strptime(normalized_date_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        pass

    try:
        # Handle ISO 8601 format with milliseconds and 'Z' suffix
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        pass

    try:
        # Handle ISO 8601 format without milliseconds
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as e:
        print(f"Error parsing date: {date_str} - {e}")
        return None


@channel_bp.route('/<workspace>/pabblyorderendpoint', methods=['POST'])
def pabbly_webhook(workspace):
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
        return jsonify({'status': 'Unauthorized'}), 403

    signature = request.headers.get('Authorization')
    key = workspace + "trackocity"
    verify = signature == hashlib.sha256(key.encode('utf-8')).hexdigest()

    if not verify:
        return jsonify({'error': 'Invalid Authorization'}), 400
    
        
    tablename = 'order_'+workspace
    orderTable = order_table_dynamic(tablename)
    orderTable.metadata = db.Model.metadata

    data = request.get_json()
  
    # Handle payment captured event
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    order_status = data.get('order_status')
    amount = data.get('total')
    currency = data.get('currency')
    email = data.get('email')
    phone = str(data.get('phone'))
    payment_method = data.get('payment_method')
    order_date = data.get('order_date', datetime.now())  # Get order date or default to now
    event_time = parse_date(order_date)  # Parse the date
    islead = False
    if order_status == 'Lead':
        islead = True
    if data.get('timezone') == 'true' or data.get('timezone') is True:  # Apply timezone offset if required
        timezone_offset = float(getattr(user, 'timezone_value', 0))  # Ensure safe access
        event_time += timedelta(hours=timezone_offset)
    event_time = event_time.strftime("%Y-%m-%d %H:%M:%S")

    if data.get('order_number') == '001':
        payment_id = str(random.randint(1, 999999999))
    else:
        payment_id = data.get('order_number', str(random.randint(1, 999999999)))
    
    order_obj = orderTable.query.filter_by(transcation_id=payment_id).first()
    if order_obj is None:
        try:
            email_encrypt = func.pgp_sym_encrypt(email, ENCRYPTION_KEY)
            phone_encrypt = func.pgp_sym_encrypt(phone, ENCRYPTION_KEY)
            email_secure = func.pgp_digest(email)
            phone_secure = func.pgp_digest(phone)
            order_make = orderTable(order_date=event_time, transcation_id=payment_id, first_name=first_name, last_name=last_name, email=email, phone=phone, email_encrypt=email_encrypt, phone_encrypt=phone_encrypt, email_secure=email_secure, phone_secure=phone_secure, payment_method=payment_method, total=amount, order_status=order_status, islead=islead)
            db.session.add(order_make)
            db.session.commit()
        except:
            db.session.rollback()
            print(f'Error pabblydata order: pabblydata:{data}')
            return jsonify({'error': 'Failed to save order'}), 500

    


    return jsonify({'status': 'success'}), 200
