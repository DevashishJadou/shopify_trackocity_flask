from flask import Blueprint, request, jsonify
import json, os
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta
from flask_cors import cross_origin

from .db_model.sql_models import Payment, UserRegister
from .connection import db


trackocitypayment_bp = Blueprint('trackocitypayment', __name__)

@trackocitypayment_bp.route('/payment_link', methods=['POST'])
def razorpay_params():
    try:
        data = json.loads(request.get_data())
        name = data.get('name')
        order_id = data.get('order_id')
        total = data.get('total')
        link = data.get('link')
        email = data.get('email')
        workspace = data.get('workspace')
        # expireon = datetime.fromtimestamp(data.get('expireon'), tz=ZoneInfo("Asia/Kolkata"))

        isexist = Payment.query.filter(workspace=workspace, total=total).first()
        if isexist:
            return jsonify({'status': 'success'}), 200
        else:
            payment = Payment(completename=name, order_id=order_id, total=total, link=link, email=email, status='pending', workspace=workspace)
            db.session.add(payment)
            db.session.commit()
    except Exception as e:
        print(f'error payment link:{e.args}')
    return jsonify({'status': 'success'}), 200


@trackocitypayment_bp.route('/payment_confirmation_razorpay', methods=['POST'])
@cross_origin()
def razorpay_subscription_recd():

    request_data = request.get_data()
  
    # Parse the JSON data from the request
    data = json.loads(request_data)

    # Process the webhook event based on the event type
    event_type = data.get('event')
    if event_type in ('order.paid', 'payment.captured', 'subscription.completed'):
        # Handle payment captured event
        payload = data.get('payload').get('payment').get('entity')
        payment_id = payload.get('id')
        order_id = payload.get('order_id')
        amount = payload.get('amount')/100.0
        currency = payload.get('currency')
        email = payload.get('email')
        
        user = UserRegister.query.filter_by(email=email).first()
        
        if user:
            user.isactive = True
            plan_till = user.plan_till
            user.plan_till = max(datetime.now(), plan_till) + timedelta(days=30)

            order_obj = Payment.query.filter_by(order_id=order_id).first()
            if order_obj:
                order_obj.transaction_id = payment_id
                order_obj.currency = currency
                order_obj.status = 'complete'
            else:
                order_make = Payment(transaction_id=payment_id, email=email, total=amount, currency=currency, status='complete')
                db.session.add(order_make)
        
        db.session.commit()


    return jsonify({'status': 'success'}), 200




@trackocitypayment_bp.route('/payment_confirmation_cashfree', methods=['POST'])
@cross_origin()
def cashfree_subscription_recd():

    request_data = request.get_data()
  
    # Parse the JSON data from the request
    data = json.loads(request_data)

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

    try:
        
        event_time = datetime.strptime(event_time, '%Y-%m-%dT%H:%M:%S%z')
        try:
            event_time = datetime.strptime(event_time, '%Y-%m-%d %H:%M:%S%')
        except:
            print(f'cashfree event_time:{event_time}')
    except:
        print(f'cashfree event_time:{event_time}')


    order_obj = Payment.query.filter_by(order_id=order_info).first()
    if order_obj:
        order_obj.transaction_id = payment_id
        order_obj.currency = currency
        order_obj.status = 'complete'
    else:
        order_make = Payment(transaction_id=payment_id, email=email, total=amount, currency=currency, status='complete')
        db.session.add(order_make)