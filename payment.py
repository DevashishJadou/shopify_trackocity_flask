from flask import Blueprint, request, jsonify
import json, os
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

    payment = Payment(name=name, order_id=order_id, total=total, link=link, email=email, status='pending')
    db.session.add(payment)
    db.session.commit()


@trackocitypayment_bp.route('/payment_confirmation', methods=['POST'])
@cross_origin()
def razorpay_webhook():

    request_data = request.get_data()
  
    # Parse the JSON data from the request
    data = json.loads(request_data)

    # Process the webhook event based on the event type
    event_type = data.get('event')
    if event_type in ('order.paid', 'payment.captured', 'subscription.completed','refund.processed'):
        # Handle payment captured event
        payload = data.get('payload').get('payment').get('entity')
        payment_id = payload.get('id')
        order_id = payload.get('order_id')
        amount = payload.get('amount')/100.0
        currency = payload.get('currency')
        email = payload.get('email')
        
        user = UserRegister.query.filter_by(email=data['email']).first() is not None
        
        if user:
          user.isactive = True
          user.plan_till = datetime.now() + timedelta(days=30)

          order_obj = Payment.query.filter_by(order_id=order_id).first()
          if order_obj:
              order_obj.transaction_id = payment_id
              order_obj.status = 'complete'
          else:
              order_make = Payment(transcation_id=payment_id, email=email, total=amount, status='complete')
              db.session.add(order_make)
        
        db.session.commit()


    return jsonify({'status': 'success'}), 200