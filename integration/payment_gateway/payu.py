from flask import request, jsonify
import json, os
from datetime import datetime, timedelta
from flask_cors import cross_origin

from sqlalchemy import MetaData

from ...db_model.sql_models import UserRegister, PlatformConfiguration, order_table_dynamic, ordertable, ordertable_detail_dynamic
from ...connection import db
from .razorpay import payment_bp
from sqlalchemy.sql import func


ENCRYPTION_KEY = os.environ.get('_ENCYPT_KEY')

metadata = MetaData()

@payment_bp.route('/payucredentials', methods=['POST'])
@cross_origin()
def checkout_params():
    header = request.headers
    _body = json.loads(request.get_data())
    workspace = header.get('workspaceId')
    platform = _body.get('platform')
    platform = 'payu'


    user = PlatformConfiguration.query.filter_by(workspace=workspace).filter_by(platform=platform).first()
    if user:
        return 200

    else:
        payu_register = PlatformConfiguration(workspace=workspace, platform=platform, active=True)
        db.session.add(payu_register)
        tablename = 'order_'+workspace
        try:
            if not metadata.tables.get(tablename):
                razorpay_table = ordertable(tablename)
                try:
                    razorpay_table.create(bind=db.engine)
                except:
                    pass
        except Exception as e:
            print(f'Payu: {e.msg}')
            return jsonify({'error': 'Something went Wrong'}), 500
    db.session.commit()

    return jsonify({'message': 'success'}), 200


@payment_bp.route('/<workspace>/payuwebhook', methods=['POST'])
def checkout_webhook(workspace):

    request_data = request.get_json() 
    print(f'payu webhook data: {request_data}')
    account = PlatformConfiguration.query.filter_by(workspace=workspace).filter_by(platform='payu').first()
    user = UserRegister.query.filter_by(workspace=workspace).first()
    if not account or not account.active:
        return jsonify({'status': 'Unauthorized'}), 403

    request_data = request.get_json()  # Load JSON data from the request

    # Extract relevant information from request data
    event_time = request_data.get('addedon')

    payment_id = str(request_data.get('cf_payment_id'))
    amount = request_data.get('amount')
    currency = request_data.get('currency', 'INR')
    email = request_data.get('email')
    phone = request_data.get('phone')
    payment_method = request_data.get('mode')
    first_name = request_data.get('firstname')
    last_name = request_data.get('lastname')
    email_encrypt = func.pgp_sym_encrypt(email, ENCRYPTION_KEY)
    phone_encrypt = func.pgp_sym_encrypt(phone, ENCRYPTION_KEY)
    email_secure = func.pgp_digest(email)
    phone_secure = func.pgp_digest(phone)

    # Convert event_time to correct timezone
    try:
        
        event_time = datetime.strptime(event_time, '%Y-%m-%dT%H:%M:%S%z') + timedelta(hours=float(user.timezone_value)) 
        try:
            event_time = datetime.strptime(event_time, '%Y-%m-%d %H:%M:%S%') + timedelta(hours=float(user.timezone_value)) 
        except:
            print(f'payu event_time:{event_time}')
    except:
        print(f'payu event_time:{event_time}')

    tablename = 'order_' + workspace
    orderTable = order_table_dynamic(tablename)
    orderTable.metadata = db.Model.metadata

    tablename_detail = 'order_detail_'+workspace
    orderTableDetail = ordertable_detail_dynamic(tablename_detail)
    orderTableDetail.metadata = db.Model.metadata

    
    if user.isleadgen:
        order_obj = orderTable.query.filter_by(email=email).first()
        if not order_obj:
            order_obj = orderTable.query.filter_by(phone=phone).first()
        if order_obj:
            order_obj.transcation_id = payment_id
            order_obj.total = amount
            order_obj.currency = currency
            order_obj.email = email
            order_obj.phone = phone
            order_obj.converted_date = event_time
            order_obj.email_encrypt = func.pgp_sym_encrypt(email, ENCRYPTION_KEY)
            order_obj.phone_encrypt = func.pgp_sym_encrypt(phone, ENCRYPTION_KEY)
            order_obj.email_secure = func.pgp_digest(email)
            order_obj.phone_secure = func.pgp_digest(phone)
        else:
            order_obj = orderTable.query.filter_by(transcation_id=payment_id).first()
            if order_obj is None:
                order_make = orderTable(order_date=event_time, transcation_id=payment_id, email=email, phone=phone, email_encrypt=email_encrypt, phone_encrypt=phone_encrypt, email_secure=email_secure, phone_secure=phone_secure, payment_method='Prepaid', total=amount, currency=currency)
                db.session.add(order_make)
    else:
        order_obj = orderTable.query.filter_by(transcation_id=payment_id).first()
        if order_obj is None:
            order_make = orderTable(
                order_date=event_time,
                transcation_id=payment_id,
                first_name = first_name,
                last_name = last_name,
                email=email,
                phone=phone,
                email_encrypt=email_encrypt,
                phone_encrypt=phone_encrypt,
                email_secure=email_secure,
                phone_secure=phone_secure,
                payment_method=payment_method,
                total=amount,
                currency=currency
            )
            db.session.add(order_make)
    db.session.commit()

    return jsonify({'status': 'success'}), 200
