from flask import Blueprint, request, jsonify
import json, os
from datetime import datetime, timedelta
from flask_cors import cross_origin

from sqlalchemy import MetaData
import hashlib, random, time

from ...db_model.sql_models import UserRegister, order_table_dynamic, ordertable, ordertable_detail ,PlatformConfiguration
from .woocommerce import channel_bp
from ...connection import db
from ...dbrule import dup_order_rule
from sqlalchemy.sql import func
from sqlalchemy import text

# tagmango_bp = Blueprint('tagmango', __name__)

ENCRYPTION_KEY = os.environ.get('_ENCYPT_KEY')

metadata = MetaData()


@channel_bp.route('/tagmangoread',methods=['GET'])
@cross_origin()
def tagmango_sent_sign():
    header = request.headers
    workspace = header.get('workspaceId')
    signature = workspace + "trackocity"
    return jsonify({'key': hashlib.sha256(signature.encode('utf-8')).hexdigest()}), 200



@channel_bp.route('/tagmangocredentials', methods=['POST'])
@cross_origin()
def tagmango_integration():
    header = request.headers
    _body = json.loads(request.get_data())
    workspace = header.get('workspaceId')

    tablename = 'order_'+workspace
    try:
        if not metadata.tables.get(tablename):
            tagmango_table = ordertable(tablename)
            ordertable_detail_table = ordertable_detail('order_detailed_'+workspace)
            try:
                tagmango_table.create(bind=db.engine)
                ordertable_detail_table.create(bind=db.engine)
            except:
                pass
    except Exception as e:
        print(f'Tagmango integration: {e.msg}')
        return jsonify({'error': 'Something went Wrong'}), 500
    
    tagmango_register = PlatformConfiguration(workspace=workspace, platform='tagmango', active=True)
    db.session.add(tagmango_register)
    db.session.commit()

    return jsonify({'message': 'success'}), 200



from datetime import datetime

def parse_date(date_str):
    if isinstance(date_str, datetime):
        return date_str
    
    try:
        # First attempt to parse the date normally
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        pass

    try:
        # Normalize spaces around colons and try again
        normalized_date_str = date_str.replace(" : ", ":").replace(": ", ":").replace(" :", ":")
        return datetime.strptime(normalized_date_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        pass

    try:
        # Handle ISO 8601 format with milliseconds and 'Z' suffix
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        pass

    try:
        # Handle ISO 8601 format without milliseconds
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as e:
        print(f"Error parsing date: {date_str} - {e}")
        return None




@channel_bp.route('/<workspace>/tagmangoorderendpoint', methods=['POST'])
def tagmango_webhook(workspace):
    """
    Status Types
    The webhook will be triggered with different status values:

    - initiated - When a subscriber starts the payment process
    - completed - When the payment is successfully processed and confirmed
    - failed - When the payment attempt fails or is declined
    
    Webhook payload structure:
    {
        "subscriberId": "634fc35ddaf58580e2418c40",
        "name": "Subscriber Name",
        "email": "someone@example.com",
        "phone": 1234567890,
        "country": "IN",
        "dialCode": "+91",
        "orderId": "634fc35ddaf58580e2418c40",
        "orderTime": "2025-02-03T12:36:18.831Z",
        "amount": 100,
        "gst": 0,
        "discount": 20,
        "coupon": "CODE",
        "amountPayable": 90,
        "mangoName": "Your mango",
        "status": "completed",
        "recurringType": "monthly",
        "currency": "INR"
    }
    """
    user = UserRegister.query.filter_by(workspace=workspace).first()
    if not user.isactive:
        return jsonify({'status': 'Unauthorized'}), 403

    signature = request.headers.get('Authorization')
    key = workspace + "trackocity"
    verify = signature == hashlib.sha256(key.encode('utf-8')).hexdigest()

    if not verify:
        return jsonify({'error': 'Invalid Authorization'}), 400
    
    tablename = 'order_'+workspace
    orderTable = order_table_dynamic(tablename)
    orderTable.metadata = db.Model.metadata

    data = request.get_json()
    
    #Extract Name
    name = data.get('name','')
    
    #Split into first_name and last_name
    name_parts = name.split(' ',1) if name else ['','']
    first_name = name_parts[0] if len(name_parts) > 0 else None
    last_name = name_parts[1] if len(name_parts) > 1 else None
    
    
  
    # Handle payment captured event
    email = data.get('email')
    phone = str(data.get('phone'))
    order_status = data.get('status')
    amount = data.get('amount')
    currency = data.get('currency')
    payment_method = data.get('payment_method', "Prepaid")
    order_date = data.get('orderTime', datetime.now())
    event_time = parse_date(order_date)
    islead = False
    
    
    #timezone    
    timezone_value = getattr(user, 'timezone_value', 0) or 0
    timezone_offset = float(timezone_value)
    event_time += timedelta(hours=timezone_offset)
    event_time = event_time.strftime("%Y-%m-%d %H:%M:%S")

    payment_id = data.get('orderId') if data.get('orderId') else str(random.randint(1, 99999999)) + '-' + str(random.randint(1, 99999999)) + '-' + str(random.randint(1, 99999999))
    
    # Check if order already exists
    # order_obj = orderTable.query.filter_by(transcation_id=payment_id).first()
    order_obj = None
    if order_obj is None:
        try:
            # Prepare order data
            order_data = {
                'order_date': event_time,
                'transcation_id': payment_id,
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'phone': phone,
                'payment_method': payment_method,
                'total': amount,
                'order_status': order_status,
                'islead': islead,
                'currency':"INR"
            }

            try:
                order_make = orderTable(**order_data)
                db.session.add(order_make)
                db.session.flush()  # Force ID generation and check for issues
                
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                raise e
            finally:
                db.session.close()
            
            return jsonify({'status': 'success', 'order_id': getattr(order_make, 'id', payment_id)}), 200
            
        except Exception as e:
            db.session.rollback()

            try:
                payment_id = data.get('orderId') if data.get('orderId') else str(random.randint(1, 99999999)) + '-' + str(random.randint(1, 99999999)) + '-' + str(random.randint(1, 99999999))

                # Fallback to raw SQL INSERT
                raw_sql = text("""
                    INSERT INTO {} (
                        order_date, transcation_id, first_name, last_name, email, phone, 
                        payment_method, total, order_status, islead, created_at, updated_at
                    ) VALUES (
                        :order_date, :transcation_id, :first_name, :last_name, :email, :phone, 
                        :payment_method, :total, :order_status, :islead, now(), now()
                    )
                    ON CONFLICT (transcation_id) DO NOTHING
                """.format(tablename))  # tablename already defined as 'order_'+workspace
                
                # Execute raw insert with params safely
                db.session.execute(raw_sql, {
                    'order_date': event_time,  'transcation_id': payment_id, 'first_name': first_name,
                    'last_name': last_name,  'email': email,  'phone': phone,  'payment_method': payment_method,
                    'total': amount,  'order_status': order_status,  'islead': islead,'currency':"INR"
                })
                db.session.commit()
                return jsonify({'status': 'success', 'order_id': payment_id}), 200

            except Exception as raw_e:
                db.session.rollback()
                print(f'tagmangodata Raw SQL insert also failed: {raw_e}')
            finally:
                db.session.close()
            print(f'Error tagmangodata order: error:{str(e)} tagmangodata:{data} payment_id:{payment_id}')
            return jsonify({'error': 'Failed to save order'}), 500
    else:
        return jsonify({'status': 'duplicate', 'message': 'Order already exists'}), 200

