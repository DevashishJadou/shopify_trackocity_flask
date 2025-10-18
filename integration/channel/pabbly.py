from flask import Blueprint, request, jsonify
import json, os
from datetime import datetime, timedelta, time
from flask_cors import cross_origin

from sqlalchemy import MetaData
import hashlib, random

from ...db_model.sql_models import UserRegister, order_table_dynamic, ordertable, ordertable_detail  
from .woocommerce import channel_bp
from ...connection import db
from ...dbrule import dup_order_rule
from sqlalchemy.sql import func
from sqlalchemy import text


ENCRYPTION_KEY = os.environ.get('_ENCYPT_KEY')

metadata = MetaData()

@channel_bp.route('/pabblyread', methods=['GET'])
@cross_origin()
def pabbly_sent_sign():
    header = request.headers
    workspace = header.get('workspaceId')
    signature = workspace + "trackocity"
    return jsonify({'key': hashlib.sha256(signature.encode('utf-8')).hexdigest()}), 200


@channel_bp.route('/pabblycredentials', methods=['POST'])
@cross_origin()
def pabbly_integration():
    header = request.headers
    _body = json.loads(request.get_data())
    workspace = header.get('workspaceId')

    tablename = 'order_'+workspace
    try:
        if not metadata.tables.get(tablename):
            pabbly_table = ordertable(tablename)
            ordertable_detail_table = ordertable_detail('order_detailed_'+workspace)
            try:
                pabbly_table.create(bind=db.engine)
                ordertable_detail_table.create(bind=db.engine)
            except:
                pass
    except Exception as e:
        print(f'Pabbly integration: {e.msg}')
        return jsonify({'error': 'Something went Wrong'}), 500

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


@channel_bp.route('/<workspace>/pabblyorderendpoint', methods=['POST'])
def pabbly_webhook(workspace):

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
  
    # Handle payment captured event
    first_name = data.get('first_name', None)
    last_name = data.get('last_name', None)
    order_status = data.get('order_status')
    amount = data.get('total')
    currency = data.get('currency')
    email = data.get('email')
    phone = str(data.get('phone'))
    payment_method = data.get('payment_method', 'Prepaid')
    order_date = data.get('order_date', datetime.now())  # Get order date or default to now
    event_time = parse_date(order_date)  # Parse the date
    islead = False
    if order_status == 'Lead':
        islead = True

    if phone is None or str(phone).strip().lower() in ('none', 'null', ''):
        phone = None

    if (email is None) or (str(email).strip().lower() in ('none', 'null', '', '@gmail.com')) or (workspace == '1dda54dda63a4737abafe52b538b6a33'):
        email = None
        
    if data.get('timezone') == 'true' or data.get('timezone') is True:
        timezone_offset = float(getattr(user, 'timezone_value', 0))
        event_time += timedelta(hours=timezone_offset)
    event_time = event_time.strftime("%Y-%m-%d %H:%M:%S")

    payment_default = str(random.randint(1, 99999999)) + '-' + str(random.randint(1, 99999999)) + '-' + str(random.randint(1, 99999999))
    if data.get('order_number') == '001':
        payment_id = payment_default
    else:
        payment_id = data.get('order_number', payment_default)
    
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
                'islead': islead
            }
            
            # Add encryption fields if supported
            # try:
            #     order_data.update({
            #         'email_encrypt': func.pgp_sym_encrypt(email, ENCRYPTION_KEY),
            #         'phone_encrypt': func.pgp_sym_encrypt(phone, ENCRYPTION_KEY),
            #         'email_secure': func.pgp_digest(email),
            #         'phone_secure': func.pgp_digest(phone)
            #     })
            # except Exception as enc_error:
            #     print(f"Encryption error (proceeding without): {enc_error}")
            
            # Create order with retry logic
            # order_make = create_order_with_retry(orderTable, order_data, max_retries=3)

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
                    'total': amount,  'order_status': order_status,  'islead': islead
                })
                db.session.commit()
                return jsonify({'status': 'success', 'order_id': payment_id}), 200

            except Exception as raw_e:
                db.session.rollback()
                print(f'Pabblydata Raw SQL insert also failed: {raw_e}')
            finally:
                db.session.close()
            print(f'Error pabblydata order: error:{str(e)} pabblydata:{data} payment_id:{payment_id}')
            return jsonify({'error': 'Failed to save order'}), 500
    else:
        return jsonify({'status': 'duplicate', 'message': 'Order already exists'}), 200