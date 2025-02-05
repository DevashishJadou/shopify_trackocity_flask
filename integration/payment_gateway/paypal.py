from flask import request, jsonify
import json, os
from datetime import datetime, timedelta
from flask_cors import cross_origin
from .razorpay import payment_bp

from ...db_model.sql_models import UserRegister, PlatformConfiguration, order_table_dynamic, ordertable
from ...connection import db
from sqlalchemy import MetaData


metadata = MetaData()

@payment_bp.route('/paypalcredentials', methods=['POST'])
@cross_origin(origins='*', methods=['POST'])
def paypal_params():
    header = request.headers
    _body = json.loads(request.get_data())
    workspace = header.get('workspaceId')
    platform = _body.get('platform')


    user = PlatformConfiguration.query.filter_by(workspace=workspace).filter_by(platform=platform).first()
    if user:
        return jsonify({'message': 'success'}), 200
    else:
        paypal_register = PlatformConfiguration(workspace=workspace, platform=platform, active=True)
        db.session.add(paypal_register)
        tablename = 'order_'+workspace
        try:
            if not metadata.tables.get(tablename):
                paypal_table = ordertable(tablename)
                try:
                    paypal_table.create(bind=db.engine)
                except:
                    pass
        except Exception as e:
            print(f'Stripe: {e.msg}')
            return jsonify({'error': 'Something went Wrong'}), 500
    db.session.commit()

    return jsonify({'message': 'success'}), 200


@payment_bp.route('/<workspace>/paypalwebhook', methods=['POST'])
def paypal_webhook_endpoint(workspace):
    user = UserRegister.query.filter_by(workspace=workspace).first()
    if not user.isactive:
        jsonify({'status': 'Unauthorized'}), 403

    tablename = 'order_'+workspace
    orderTable = order_table_dynamic(tablename)
    orderTable.metadata = db.Model.metadata

    # The library needs to be configured with your account's secret key.
    event = None
    payload = request.data

    event = json.loads(payload.decode('utf-8'))
    print(f'Paypal Payload {workspace}:{event}')
    # Handle the event
    if event['event_type'] in ('CHECKOUT.ORDER.COMPLETED'):
        print(f'Paypal event {workspace}:{event}')
        resource = event['resource']
        charge = resource['purchase_units'][0]
        payment_id = event.get('id')
        amount = charge.get('amount').get('value')
        currency = charge.get('amount').get('currency_code')
        if currency.lower() == 'usd':
            if user.currency == 'INR':
                amount = amount * 86
            if user.currency == 'GBP':
                amount = amount * 0.8
        if currency.lower() == 'gbp':
            if user.currency == 'INR':
                amount = amount * 103
            if user.currency == 'USD':
                amount = amount * 1.24
        email = resource.get('payer').get('email_address')
        first_name = resource.get('payer').get('name').get('given_name')
        last_name = resource.get('payer').get('name').get('surname')
        phone = None
        event_time = datetime.strptime(resource.get('create_time'), "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=float(user.timezone_value))
        order_obj = orderTable.query.filter_by(transcation_id=payment_id).first()
        if order_obj is None:
            order_make = orderTable(order_date=event_time, transcation_id=payment_id, email=email, phone=phone, payment_method='Prepaid', total=amount, currency=currency, first_name= first_name, last_name = last_name)
            db.session.add(order_make)
        db.session.commit()
    else:
        print('Unhandled event type {}'.format(event['type']))

    return jsonify(success=True)

    