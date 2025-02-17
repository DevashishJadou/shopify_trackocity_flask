
from flask import request, jsonify
import json, os, random
from datetime import datetime, timedelta
from flask_cors import cross_origin
from .woocommerce import channel_bp

from ...db_model.sql_models import UserRegister, PlatformConfiguration, order_table_dynamic, ordertable
from ...connection import db
from sqlalchemy import MetaData


metadata = MetaData()

@channel_bp.route('/gohighlevelcredentials', methods=['POST'])
@cross_origin(origins='*', methods=['POST'])
def gohiglevel_params():
    header = request.headers
    _body = json.loads(request.get_data())
    workspace = header.get('workspaceId')
    platform = _body.get('platform')

    user = PlatformConfiguration.query.filter_by(workspace=workspace).filter_by(platform=platform).first()
    if user:
        return jsonify({'message': 'success'}), 200
    else:
        gohiglevel_register = PlatformConfiguration(workspace=workspace, platform=platform, active=True)
        db.session.add(gohiglevel_register)
        tablename = 'order_'+workspace
        try:
            if not metadata.tables.get(tablename):
                gohiglevel_table = ordertable(tablename)
                try:
                    gohiglevel_table.create(bind=db.engine)
                except:
                    pass
        except Exception as e:
            print(f'gohiglevel: {e.msg}')
            return jsonify({'error': 'Something went Wrong'}), 500
    db.session.commit()

    return jsonify({'message': 'success'}), 200



@channel_bp.route('/<workspace>/gohiglevelwebhook', methods=['POST'])
@cross_origin()
def gohiglevel_webhook(workspace):
    
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
    print(f'gohiglevel Payload {workspace}:{event}')

    # Handle the event
    payment_id = event.get('id', '001')
    currency = event.get('order',{}).get('currency_code', None)
    amount = event.get('amount',0)/100.0
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
    email = event.get('email', event.get('user', {}).get('email'))
    phone = event.get('phone', event.get('user', {}).get('phone'))
    first_name = event.get('first_name', event.get('user', {}).get('firstName'))
    last_name = event.get('last_name', event.get('user', {}).get('firstName'))
    event_time = datetime.strptime(event.get('date_created'), "%Y-%m-%dT%H:%M:%S.%fZ") + timedelta(hours=float(user.timezone_value))
    order_obj = orderTable.query.filter_by(transcation_id=payment_id).first()
    if payment_id == '001':
        payment_id = str(random.randint(1, 9999999))
    if order_obj is None:
        order_make = orderTable(order_date=event_time, transcation_id=payment_id, first_name=first_name, email=email, phone=phone, last_name=last_name, payment_method='Prepaid', total=amount, currency=currency)
        db.session.add(order_make)
    db.session.commit()


    return jsonify(success=True)