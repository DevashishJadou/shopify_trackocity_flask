# integration pg

from ..db_model.sql_models import *
from ..connection import db

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin


intgration_cd = Blueprint('integration', __name__)

@intgration_cd.route('/code', methods=['GET', 'OPTIONS'])
@cross_origin(origins='*', methods=['GET', 'POST', 'OPTIONS'], headers=['Content-Type'])
def code_productid():
    headers = request.headers
    workspace = headers.get('workspaceId')

    user = UserRegister.query.filter_by(workspace=workspace).first()
    subdomain = user.subdomain if user.subdomain is not None else 'delivery'

    if user:
        return jsonify({"productid":user.productid, "subdomain":subdomain}), 200
    else:
        return jsonify({"message":"Workspace don't found"}), 400


@intgration_cd.route('/facebook', methods=['GET', 'OPTIONS'])
@cross_origin(origins='*', methods=['GET', 'OPTIONS'], headers=['Content-Type'])
def integration_facebbok():
    headers = request.headers
    workspace = headers.get('workspaceId')

    user = ClientFacebookredentials.query.filter_by(workspace=workspace).all()

    if user:
        accounts = []
        for acc in user:
            value = {'id':acc.id, 'accountname':acc.account_name, 'accountid':acc.account}
            accounts.append(value)
        return jsonify({"accounts":accounts}), 200
    else:
        return jsonify({"message":"no account found"}), 400
    

@intgration_cd.route('/facebook/deleteaccount', methods=['PUT', 'OPTIONS'])
@cross_origin(origins='*', methods=['PUT', 'OPTIONS'], headers=['Content-Type'])
def integration_facebbok_account_delete():
    headers = request.headers
    workspace = headers.get('workspaceId')
    body = request.args
    id = body.get('id')
    row_to_delete = ClientFacebookredentials.query.filter_by(id=id, workspace=workspace).first()
    if row_to_delete:
        # If the row exists, delete it
        db.session.delete(row_to_delete)
        db.session.commit()  # Commit the transaction to delete the row
        return jsonify({"message": "Account successfully deleted"}), 200
    else:
        # Return an appropriate message if the row doesn't exist
        return jsonify({"message": "No account found"}), 404
    

@intgration_cd.route('/google', methods=['GET', 'OPTIONS'])
@cross_origin(origins='*', methods=['GET', 'OPTIONS'], headers=['Content-Type'])
def integration_google():
    headers = request.headers
    workspace = headers.get('workspaceId')

    user = ClientGoogleCredentials.query.filter_by(workspace=workspace).all()

    if user:
        accounts = []
        for acc in user:
            value = {'id':acc.id, 'accountname':acc.account_name, 'accountid':acc.account}
            accounts.append(value)
        return jsonify({"accounts":accounts}), 200
    else:
        return jsonify({"message":"no account found"}), 400
    

@intgration_cd.route('/google/deleteaccount', methods=['PUT', 'OPTIONS'])
@cross_origin(origins='*', methods=['PUT', 'OPTIONS'], headers=['Content-Type'])
def integration_google_account_delete():
    headers = request.headers
    workspace = headers.get('workspaceId')
    body = request.args
    id = body.get('id')
    row_to_delete = ClientGoogleCredentials.query.filter_by(id=id, workspace=workspace).first()

    if row_to_delete:
        # If the row exists, delete it
        db.session.delete(row_to_delete)
        db.session.commit()  # Commit the transaction to delete the row
        return jsonify({"message": "Account successfully deleted"}), 200
    else:
        # Return an appropriate message if the row doesn't exist
        return jsonify({"message": "No account found"}), 404


@intgration_cd.route('/integration', methods=['GET', 'OPTIONS'])
@cross_origin(origins='*', methods=['GET', 'OPTIONS'], headers=['Content-Type'])
def integrationed_plaform():
    headers = request.headers
    workspace = headers.get('workspaceId')
    integation = {}

    shopify = Shopify.query.filter_by(workspace=workspace).first()
    integation['shopify'] = True if shopify else False

    razorpay = RazorpayConfiguration.query.filter_by(workspace=workspace).first()
    integation['razorpay'] = True if razorpay else False

    woocommerce = WooCommerce.query.filter_by(workspace=workspace).first()
    integation['woocommerce'] = True if woocommerce else False

    return jsonify(integation), 200