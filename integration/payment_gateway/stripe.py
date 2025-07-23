
from flask import request, jsonify
import json, os
from datetime import datetime, timedelta
from flask_cors import cross_origin
from .razorpay import payment_bp

from ...db_model.sql_models import UserRegister, PlatformConfiguration, order_table_dynamic, ordertable, ordertable_detail
from ...connection import db
from sqlalchemy import MetaData
from sqlalchemy import text


metadata = MetaData()

@payment_bp.route('/stripecredentials', methods=['POST'])
@cross_origin(origins='*', methods=['POST'])
def stripe_params():
    header = request.headers
    _body = json.loads(request.get_data())
    workspace = header.get('workspaceId')
    platform = _body.get('platform')

    user = PlatformConfiguration.query.filter_by(workspace=workspace).filter_by(platform=platform).first()
    if user:
        return jsonify({'message': 'success'}), 200
    else:
        stripe_register = PlatformConfiguration(workspace=workspace, platform=platform, active=True)
        db.session.add(stripe_register)
        tablename = 'order_'+workspace
        order_detail_tablename = 'order_detailed_'+workspace
        try:
            if not metadata.tables.get(tablename):
                stripe_table = ordertable(tablename)
                order_detail_table = ordertable_detail(order_detail_tablename)
                try:
                    stripe_table.create(bind=db.engine)
                    order_detail_table.create(bind=db.engine)
                except:
                    pass
        except Exception as e:
            print(f'Stripe: {e.msg}')
            return jsonify({'error': 'Something went Wrong'}), 500
    db.session.commit()

    return jsonify({'message': 'success'}), 200



@payment_bp.route('/<workspace>/stripewebhook', methods=['POST'])
@cross_origin()
def strip_webhook(workspace):
    
    account = PlatformConfiguration.query.filter_by(workspace=workspace).filter_by(platform='stripe').first()
    user = UserRegister.query.filter_by(workspace=workspace).first()
    if not user.isactive or not account.active:
        jsonify({'status': 'Unauthorized'}), 403
    
    if not user.isactive:
        jsonify({'status': 'Unauthorized'}), 403

    tablename = 'order_'+workspace
    orderTable = order_table_dynamic(tablename)
    orderTable.metadata = db.Model.metadata

    # The library needs to be configured with your account's secret key.
    event = None
    payload = request.data
    event = json.loads(payload.decode('utf-8'))
    print(f'Stripe Payload {workspace}:{event}')

    # Handle the event
    if event['type'] == 'charge.succeeded':
        print(f'Stripe event {workspace}:{event}')
        charge = event['data']['object']
        payment_id = charge.get('id')
        currency = charge.get('currency')
        amount = charge.get('amount')/100.0
        if currency.lower() == 'usd':
            if user.currency == 'INR':
                amount = amount * 86
                currency = 'INR'
            if user.currency == 'GBP':
                amount = amount * 0.8
                currency = 'GBP'
        if currency.lower() == 'gbp':
            if user.currency == 'INR':
                amount = amount * 103
                currency = 'INR'
            if user.currency == 'USD':
                amount = amount * 1.24
                currency = 'USD'
        if charge.get('metadata', {}).get('email') is not None or charge.get('metadata', {}).get('email') != 'None':
            email = charge.get('metadata', {}).get('email')
        else:
            email = charge.get('receipt_email')
        phone = charge.get('receipt_number')
        first_name = charge.get('billing_details', {}).get('name')
        event_time = datetime.fromtimestamp(charge.get('created')) + timedelta(hours=float(user.timezone_value))
        order_obj = orderTable.query.filter_by(transcation_id=payment_id).first()
        if order_obj is None:
            order_make = orderTable(order_date=event_time, transcation_id=payment_id, first_name=first_name, email=email, phone=phone, payment_method='Prepaid', total=amount, currency=currency)
            db.session.add(order_make)
        db.session.commit()
    else:
        print('Unhandled event type {}'.format(event['type']))

    return jsonify(success=True)