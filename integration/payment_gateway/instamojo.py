from flask import request, jsonify
import json, os
from datetime import datetime, timedelta
from flask_cors import cross_origin

from sqlalchemy import MetaData

# from db_model.sql_models import RazorpayConfiguration, order_table_dynamic, ordertable
# from connection import db
from ...db_model.sql_models import UserRegister, InstaMojoConfiguration, order_table_dynamic, ordertable
from ...connection import db
from ...dbrule import dup_order_rule
from integration.payment_gateway.razorpay import payment_bp

from instamojo_wrapper import Instamojo
from datetime import datetime


metadata = MetaData()

@payment_bp.route('/razorpaycredentials', methods=['POST'])
@cross_origin()
def instamojo_params():
    header = request.headers
    _body = json.loads(request.get_data())
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
