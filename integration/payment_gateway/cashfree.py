from flask import request, jsonify
import json, os
from datetime import datetime, timedelta
from flask_cors import cross_origin

import razorpay
from sqlalchemy import MetaData

from ...db_model.sql_models import UserRegister, PlatformConfiguration, order_table_dynamic, ordertable
from ...connection import db
from .razorpay import payment_bp

metadata = MetaData()

@payment_bp.route('/cashfreecredentials', methods=['POST'])
@cross_origin()
def checkout_params():
    header = request.headers
    _body = json.loads(request.get_data())
    workspace = header.get('workspaceId')
    platform = _body.get('platform')
    platform = 'cashfree'


    user = PlatformConfiguration.query.filter_by(workspace=workspace).filter_by(platform=platform).first()
    if user:
        return 200

    else:
        razorpay_register = PlatformConfiguration(workspace=workspace, platform=platform, active=True)
        db.session.add(razorpay_register)
        tablename = 'order_'+workspace
        try:
            if not metadata.tables.get(tablename):
                razorpay_table = ordertable(tablename)
                try:
                    razorpay_table.create(bind=db.engine)
                except:
                    pass
        except Exception as e:
            print(f'Cashfree: {e.msg}')
            return jsonify({'error': 'Something went Wrong'}), 500
    db.session.commit()

    return jsonify({'message': 'success'}), 200


@payment_bp.route('/<workspace>/cashfreewebhook', methods=['POST'])
def checkout_webhook(workspace):
    #  {  
    #         "data": {  
    #             "order": {  
    #                 "order_id": "order_OFR_2",  
    #                 "order_amount": 2,  
    #                 "order_currency": "INR",  
    #                 "order_tags": null  
    #             },  
    #             "payment": {  
    #                 "cf_payment_id": 1453002795,  
    #                 "payment_status": "SUCCESS",  
    #                 "payment_amount": 1,  
    #                 "payment_currency": "INR",  
    #                 "payment_message": "00::Transaction success",  
    #                 "payment_time": "2022-12-15T12:20:29+05:30",  
    #                 "bank_reference": "234928698581",  
    #                 "auth_id": null,  
    #                 "payment_method": {  
    #                     "upi": {  
    #                         "channel": null,  
    #                         "upi_id": "9611199227@paytm"  
    #                     }  
    #                 },  
    #                 "payment_group": "upi"  
    #             },  
    #             "customer_details": {  
    #                 "customer_name": null,  
    #                 "customer_id": "7112AAA812234",  
    #                 "customer_email": "[miglaniyogesh7@gmail.com](<>)",  
    #                 "customer_phone": "9908734801"  
    #             },  
    #             "payment_gateway_details": {
    #                 "gateway_name": "CASHFREE",
    #                 "gateway_order_id": "1634766330",
    #                 "gateway_payment_id": "1504280029",
    #                 "gateway_settlement": "CASHFREE",
    #                 "gateway_status_code": null
    #             },
    #             "payment_offers": [  
    #                 {  
    #                     "offer_id": "0f05e1d0-fbf8-4c9c-a1f0-814c7b2abdba",  
    #                     "offer_type": "DISCOUNT",  
    #                     "offer_meta": {  
    #                         "offer_title": "50% off on UPI",  
    #                         "offer_description": "50% off for testing",  
    #                         "offer_code": "UPI50",  
    #                         "offer_start_time": "2022-11-09T06:23:25.972Z",  
    #                         "offer_end_time": "2023-02-27T18:30:00Z"  
    #                     },  
    #                     "offer_redemption": {  
    #                         "redemption_status": "SUCCESS",  
    #                         "discount_amount": 1,  
    #                         "cashback_amount": 0  
    #                     }  
    #                 }  
    #             ]  
    #         },  
    #         "event_time": "2023-01-03T11:16:10+05:30",  
    #         "type": "PAYMENT_SUCCESS_WEBHOOK"  
    #     }

    user = UserRegister.query.filter_by(workspace=workspace).first()
    if not user.isactive:
        return jsonify({'status': 'Unauthorized'}), 403

    request_data = request.get_json()  # Load JSON data from the request

    # Extract relevant information from request data
    payment_info = request_data.get('data', {}).get('payment', {})
    customer_info = request_data.get('data', {}).get('customer_details', {})
    order_info = request_data.get('data', {}).get('order', {})
    event_time = request_data.get('event_time')

    payment_id = str(payment_info.get('cf_payment_id'))
    try:
        amount = payment_info.get('payment_amount')
    except:
        amount = payment_info.get('payment_amount')
    currency = payment_info.get('payment_currency')
    email = customer_info.get('customer_email')
    phone = customer_info.get('customer_phone')
    payment_method = payment_info.get('payment_group')

    # Convert event_time to correct timezone
    try:
        
        event_time = datetime.strptime(event_time, '%Y-%m-%dT%H:%M:%S%z') + timedelta(hours=float(user.timezone_value)) 
        try:
            event_time = datetime.strptime(event_time, '%Y-%m-%d %H:%M:%S%') + timedelta(hours=float(user.timezone_value)) 
        except:
            print(f'cashfree event_time:{event_time}')
    except:
        print(f'cashfree event_time:{event_time}')

    tablename = 'order_' + workspace
    orderTable = order_table_dynamic(tablename)
    orderTable.metadata = db.Model.metadata

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
        else:
            order_obj = orderTable.query.filter_by(transcation_id=payment_id).first()
            if order_obj is None:
                order_make = orderTable(order_date=event_time, transcation_id=payment_id, email=email, phone=phone, payment_method='Prepaid', total=amount, currency=currency)
                db.session.add(order_make)
    else:
        order_obj = orderTable.query.filter_by(transcation_id=payment_id).first()
        if order_obj is None:
            order_make = orderTable(
                order_date=event_time,
                transcation_id=payment_id,
                email=email,
                phone=phone,
                payment_method=payment_method,
                total=amount,
                currency=currency
            )
            db.session.add(order_make)
    db.session.commit()

    return jsonify({'status': 'success'}), 200
