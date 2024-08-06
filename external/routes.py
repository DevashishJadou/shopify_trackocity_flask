# external/routes.py
from flask import Blueprint, jsonify, request
import hashlib

from ..db_model.mongo_models import Fingerprint, CustomerInfo, Error
from flask_cors import cross_origin

 
external_bp = Blueprint('external', __name__)

def map_hash(field):
    return hashlib.sha256(field.encode('utf-8')).hexdigest()

@external_bp.route('/gusid', methods=['POST'])
@cross_origin(origins='*', methods=['POST'], headers=['Content-Type'])
def user_session():
    try:
        # Get parameters from the request
        productid = request.json.get('productId', 'temp')
        creation_at = request.json.get('creationAt')
        usrid = request.json.get('gusId')
        fingerprint = request.json.get('fingerprint')
        localsession = request.json.get('clickId', None)
        session = request.headers.get('sessionId')
        body = request.json.get('body')

        #Api-key Validation
        securitykey = str(productid) if localsession is None else str(productid)+localsession
        apikey = request.args.get("apiKey")

        if apikey is None or apikey != map_hash(securitykey):
            return jsonify({'error': 'Authenication Failed'}), 401

        # Validate parameters
        if not productid or not session or not creation_at or not usrid or not localsession:
            return jsonify({'error': 'Missing parameters'}), 400

        new_product = Fingerprint(visitorid=usrid, fingerprint=fingerprint, session=session, productid=productid, creation_at=creation_at, localsession=localsession, body=body)
        new_product.save()

        return jsonify(200), 200
    except Exception as e:
        print(f'Error gusid external: {e.args}, session:{session}, product:{productid}')
        return jsonify(e.arg), 500


@external_bp.route('/info', methods=['POST'])
@cross_origin(origins='*', methods=['POST'], headers=['Content-Type'])
def user_info():
    try:
        # Get parameters from the request
        productid = request.json.get('productId', 'temp')
        creation_at = request.json.get('creationAt')
        body = request.json.get('jsonBody')
        localsession = request.json.get('clickId', None)
        session = request.headers.get('sessionId')

        try:
            x_forwarded_for = request.headers.get('X-Forwarded-For')
            client_ip = x_forwarded_for.split(',')[0].strip() if x_forwarded_for else request.remote_addr
            body['navigatordetails']['ipaddress'] = client_ip
        except:
            pass

        #Api-key Validation
        securitykey = str(productid) if localsession is None else str(productid)+localsession
        apikey = request.args.get("apiKey")

        if apikey is None or apikey != map_hash(securitykey):
            print(f'body: {body}')
            return jsonify({'error': 'Authenication Failed'}), 401

        # Validate parameters
        if not productid or not session or not creation_at or not body or not localsession:
            return jsonify({'error': 'Missing parameters'}), 400

        new_product = CustomerInfo(session=session, productid=productid, creation_at=creation_at, localsession=localsession, body=body)
        new_product.save()

        return jsonify(200), 200
    except Exception as e:
        print(f'Error in info: {e.args}, body:{body}, session:{session}, product:{productid}')
        return jsonify(e.arg), 500



@external_bp.route('/error', methods=['POST'])
@cross_origin(origins='*', methods=['POST'], headers=['Content-Type'])
def error():
    # Get parameters from the request
    productid = request.json.get('productId')
    errormsg = request.json.get('error')
    session = request.headers.get('sessionId')

    new_product = Error(session=session, productid=productid, error=error)
    new_product.save()

    return jsonify(200), 200
