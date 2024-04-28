# external/routes.py
from flask import Blueprint, jsonify, request
import hashlib

from ..db_model.mongo_models import Fingerprint, CustomerInfo, Error
# from db_model.mongo_models import Fingerprint, CustomerInfo, Error, CustomerInfoext

from flask_cors import cross_origin

 
external_bp = Blueprint('external', __name__)

def map_hash(field):
    return hashlib.sha256(field.encode('utf-8')).hexdigest()

@external_bp.route('/gusid', methods=['OPTIONS', 'POST'])
@cross_origin(origins='*', methods=['OPTIONS', 'POST'], headers=['Content-Type'])
def user_session():
    # Get parameters from the request
    productid = request.json.get('productId')
    creation_at = request.json.get('creationAt')
    usrid = request.json.get('gusId')
    localsession = request.json.get('clickId')
    session = request.headers.get('sessionId')

    #Api-key Validation
    securitykey = str(productid)+localsession
    apikey = request.args.get("apiKey")

    if apikey is None or apikey != map_hash(securitykey):
        return jsonify({'error': 'Authenication Failed'}), 401

    # Validate parameters
    if not productid or not session or not creation_at or not usrid or not localsession:
        return jsonify({'error': 'Missing parameters'}), 400

    new_product = Fingerprint(visitorid=usrid, session=session, productid=productid, creation_at=creation_at, localsession=localsession)
    new_product.save()

    print(new_product)

    return jsonify(200), 200


@external_bp.route('/info', methods=['OPTIONS', 'POST'])
@cross_origin(origins='*', methods=['OPTIONS', 'POST'], headers=['Content-Type'])
def user_info():
    # Get parameters from the request
    productid = request.json.get('productId')
    creation_at = request.json.get('creationAt')
    body = request.json.get('jsonBody')
    localsession = request.json.get('clickId')
    session = request.headers.get('sessionId')

    #Api-key Validation
    securitykey = str(productid)+localsession
    apikey = request.args.get("apiKey")

    if apikey is None or apikey != map_hash(securitykey):
        return jsonify({'error': 'Authenication Failed'}), 401

    # Validate parameters
    if not productid or not session or not creation_at or not body or not localsession:
        return jsonify({'error': 'Missing parameters'}), 400

    new_product = CustomerInfo(session=session, productid=productid, creation_at=creation_at, localsession=localsession, body=body)
    new_product.save()

    return jsonify(200), 200



@external_bp.route('/error', methods=['OPTIONS', 'POST'])
@cross_origin(origins='*', methods=['OPTIONS', 'POST'], headers=['Content-Type'])
def error():
    # Get parameters from the request
    productid = request.json.get('productId')
    errormsg = request.json.get('error')
    session = request.headers.get('sessionId')

    print(f'productid:{productid}, error:{errormsg} ,session:{session}')

    new_product = Error(session=session, productid=productid, error=error)
    new_product.save()

    return jsonify(200), 200
