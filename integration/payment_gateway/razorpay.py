from flask import Blueprint, request, jsonify
import json, os

import razorpay
from sqlalchemy import MetaData

# from db_model.sql_models import RazorpayConfiguration, order_table_dynamic, ordertable
# from connection import db
from ...db_model.sql_models import RazorpayConfiguration, order_table_dynamic, ordertable
from ...connection import db

metadata = MetaData()
payment_bp = Blueprint('clientpayment', __name__)

@payment_bp.route('/razorpaycredentials', methods=['POST'])
def razorpay_params():
    _body = request.get_data()
    workspace = _body['workspace']
    _razorpay_api_secret = _body['razorpay_api_secret']
    _razorpay_api_key = _body['razorpay_api_key']
    _razorpay_client_secret = _body['_razorpay_client_secret']

    user = RazorpayConfiguration.query.filter_by(workspace=workspace).first()
    if user:
        user.razorpay_api_secret = _razorpay_api_secret
        user.razorpay_api_key = _razorpay_api_key
        db.session.commit()
        return jsonify({'message': 'Inforamtion Updated Succesfully'}), 200

    else:
        razorpay_register = RazorpayConfiguration(workspace=workspace, razorpay_api_secret=_razorpay_api_secret, razorpay_api_key=_razorpay_api_key, razorpay_client_secret=_razorpay_client_secret)
        tablename = 'order_'+workspace
        if not metadata.tables.get(tablename):
            razorpay_table = ordertable(tablename)
            razorpay_table.create(bind=db.engine)
        db.session.add(razorpay_register)
    db.session.commit()


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


    signature = request.headers.get('X-Razorpay-Signature')

    razorpay_client = RazorpayConfiguration.query.filter_by(workspace=workspace).first()

    webhook_secret = razorpay_client.razorpay_api_secret
    webhook_key = razorpay_client.razorpay_api_key
    client_secret = razorpay_client.razorpay_client_secret

    request_data = request.get_data()
    client = razorpay.Client(auth=(webhook_key, webhook_secret))
    verify = client.utility.verify_webhook_signature(request_data.decode("utf-8"), signature, client_secret)
    print(f"Verify:{verify}")


    if not verify:
        return jsonify({'error': 'Invalid signature'}), 400
    
    tablename = 'order_'+workspace
    orderTable = order_table_dynamic(tablename)
    orderTable.metadata = db.Model.metadata

    # Parse the JSON data from the request
    data = json.loads(request_data)
    print(f"Razorpay payload: {data}")

    # Process the webhook event based on the event type
    event_type = data.get('event')
    if event_type in ('order.paid', 'payment.captured'):
        # Handle payment captured event
        payload = data.get('payload').get('payment').get('entity')
        payment_id = payload.get('id')
        amount = payload.get('amount')
        currency = payload.get('currency')
        email = payload.get('email')
        event_time = data.get('created_at')
        
        order_make = orderTable(order_date=event_time, transcation_id=payment_id, email=email, payment_method='Prepaid', total=amount)

        db.session.add(order_make)
        db.session.commit()


    return jsonify({'status': 'success'}), 200
