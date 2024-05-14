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
    data = json.loads(request.get_data())

    name = data.get('name')
    order_id = data.get('order_id')
    total = data.get('total')
    link = data.get('link')
    email = data.get('email')
    expireon = datetime.fromtimestamp(data.get('expireon'), tz=ZoneInfo("Asia/Kolkata"))

    payment = Payment(completename=name, order_id=order_id, total=total, link=link, email=email, status='pending', expireon=expireon)
    db.session.add(payment)
    db.session.commit()
    return jsonify({'status': 'success'}), 200


@trackocitypayment_bp.route('/payment_confirmation', methods=['POST'])
@cross_origin()
def razorpay_webhook():

    request_data = request.get_data()
  
    # Parse the JSON data from the request
    data = json.loads(request_data)

    # Process the webhook event based on the event type
    event_type = data.get('event')
    print(f'event_payment_link:{event_type}')
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