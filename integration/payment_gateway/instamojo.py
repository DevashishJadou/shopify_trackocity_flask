from flask import request, jsonify
from datetime import datetime, timedelta
from flask_cors import cross_origin

from sqlalchemy import MetaData

# from db_model.sql_models import RazorpayConfiguration, order_table_dynamic, ordertable
# from connection import db
from ...db_model.sql_models import UserRegister, InstaMojoConfiguration, order_table_dynamic, ordertable
from ...connection import db
from ...dbrule import dup_order_rule
from .razorpay import payment_bp

from datetime import datetime


metadata = MetaData()

@payment_bp.route('/instamojocredentials', methods=['POST'])
@cross_origin()
def instamojo_params():
    header = request.headers
    _body = request.form.to_dict()
    print(f'body:{_body}')
    workspace = header.get('workspaceId')
    _api_auth = _body['intamojo_api_auth']
    _api_key = _body['intamojo_api_key']

    user = InstaMojoConfiguration.query.filter_by(workspace=workspace).first()
    if user:
        user.api_key = _api_key
        user.api_auth = _api_auth
        db.session.commit()
        return jsonify({'message': 'Inforamtion Updated Succesfully'}), 200

    else:
        razorpay_register = InstaMojoConfiguration(workspace=workspace, api_key=_api_key, api_auth=_api_auth, active=True)
        tablename = 'order_'+workspace
        try:
            if not metadata.tables.get(tablename):
                razorpay_table = ordertable(tablename)
                try:
                    razorpay_table.create(bind=db.engine)
                    db.session.add(razorpay_register)
                    dup_order_rule(tablename)
                except:
                    pass
        except Exception as e:
            print(f'InstaMojo: {e.msg}')
            return jsonify({'error': 'Something went Wrong'}), 500
    db.session.commit()

    return jsonify({'message': 'success'}), 200


@payment_bp.route('/<workspace>/instamojowebhook', methods=['POST'])
def instamojo_webhook(workspace):
    user = UserRegister.query.filter_by(workspace=workspace).first()
    if not user.isactive:
        jsonify({'status': 'Unauthorized'}), 403
    
    data = request.form.to_dict()
    print(f'instamojo:{data}')
    mac_provided = data.pop('mac', None)
    
    if not mac_provided:
        return jsonify({'status': 'error', 'message': 'MAC not provided'}), 400
    
    tablename = 'order_'+workspace
    orderTable = order_table_dynamic(tablename)
    orderTable.metadata = db.Model.metadata

    amount = data.get('amount')
    buyer = data.get('buyer')
    buyer_name = data.get('buyer_name')
    buyer_phone = data.get('buyer_phone')
    currency = data.get('currency')
    fees = data.get('fees')
    longurl = data.get('longurl')
    payment_id = data.get('payment_id')
    payment_request_id = data.get('payment_request_id')
    purpose = data.get('purpose')
    shorturl = data.get('shorturl')
    status = data.get('status')


    # Process the webhook event based on the event type
    if status == 'Credit':
        # Handle payment captured event
        event_time = datetime.fromtimestamp(datetime.now()) #+ timedelta(hours=float(user.timezone_value))
        
        order_obj = orderTable.query.filter_by(transcation_id=payment_id).first()
        if order_obj is None:
            order_make = orderTable(order_date=event_time, transcation_id=payment_id, first_name=buyer_name, email=buyer, phone=buyer_phone, payment_method='Prepaid', total=amount, currency=currency)

            db.session.add(order_make)
            db.session.commit()


    return jsonify({'status': 'success'}), 200
