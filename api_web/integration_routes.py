# integration pg

from ..db_model.sql_models import *
from ..connection import db
from sqlalchemy import MetaData


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



@intgration_cd.route('/linkedin', methods=['GET', 'OPTIONS'])
@cross_origin(origins='*', methods=['GET', 'OPTIONS'], headers=['Content-Type'])
def integration_linkedin():
    headers = request.headers
    workspace = headers.get('workspaceId')

    user = ClientLinkedinCredentials.query.filter_by(workspace=workspace).all()
    if user:
        accounts = []
        for acc in user:
            value = {'id':acc.id, 'accountname':acc.account_name, 'accountid':acc.account}
            accounts.append(value)
        return jsonify({"accounts":accounts}), 200
    else:
        return jsonify({"message":"no account found"}), 400
    

@intgration_cd.route('/linkedin/deleteaccount', methods=['PUT', 'OPTIONS'])
@cross_origin(origins='*', methods=['PUT', 'OPTIONS'], headers=['Content-Type'])
def integration_linkedin_account_delete():
    headers = request.headers
    workspace = headers.get('workspaceId')
    body = request.args
    id = body.get('id')
    row_to_delete = ClientLinkedinCredentials.query.filter_by(id=id, workspace=workspace).first()
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
    output = {}
    integation = {}
    integation['adplatform'] = {}
    integation['payment'] = {}
    integation['store'] = {}
    adplatform = 0
    paymentplatform = 0
    storeplatform = 0

    onboarding = UserOnboarding.query.filter_by(user_id=workspace).first()
    output['tour_started'] = onboarding.tour_started
    output['tour_completed'] = onboarding.tour_completed
    output['current_tour_step'] = onboarding.current_tour_step
    output['tour_dismissed'] = onboarding.tour_dismissed
    

    fb = ClientFacebookredentials.query.filter_by(workspace=workspace).first()
    integation['adplatform']['facebook'] = True if fb else False
    adplatform +=1 if fb else 0

    gg = ClientGoogleCredentials.query.filter_by(workspace=workspace).first()
    integation['adplatform']['google'] = True if gg else False
    adplatform +=1 if gg else 0

    linkedin = ClientLinkedinCredentials.query.filter_by(workspace=workspace).first()
    integation['adplatform']['linkedin'] = True if linkedin else False
    adplatform +=1 if linkedin else 0

    onboarding.connected_adplatform = adplatform



    
    shopify = Shopify.query.filter_by(workspace=workspace).first()
    integation['store']['shopify'] = True if shopify else False
    storeplatform +=1 if shopify else 0

    woocommerce = WooCommerce.query.filter_by(workspace=workspace).first()
    integation['store']['woocommerce'] = True if woocommerce else False
    storeplatform +=1 if woocommerce else 0
    
    razorpay = RazorpayConfiguration.query.filter_by(workspace=workspace).first()
    integation['payment']['razorpay'] = True if razorpay else False
    storeplatform +=1 if razorpay else 0

    onboarding.connected_checkout = storeplatform


    plaform_cashfree = 'cashfree'
    cashfree = PlatformConfiguration.query.filter_by(workspace = workspace).filter_by(platform=plaform_cashfree).first()
    integation['payment']['cashfree'] = True if cashfree else False
    paymentplatform +=1 if cashfree else 0

    plaform_stripe= 'stripe'
    stripe = PlatformConfiguration.query.filter_by(workspace = workspace).filter_by(platform=plaform_stripe).first()
    integation['payment']['stripe'] = True if stripe else False
    paymentplatform +=1 if stripe else 0

    plaform_paypal= 'paypal'
    paypal = PlatformConfiguration.query.filter_by(workspace = workspace).filter_by(platform=plaform_paypal).first()
    integation['payment']['paypal'] = True if paypal else False
    paymentplatform +=1 if paypal else 0

    plaform_pabbly= 'pabbly'
    pabbly = PlatformConfiguration.query.filter_by(workspace = workspace).filter_by(platform=plaform_pabbly).first()
    integation['payment']['pabbly'] = True if pabbly else False
    paymentplatform +=1 if pabbly else 0

    onboarding.connected_payment = paymentplatform

    output['connected_adplatform'] = adplatform
    output['connected_payment'] = paymentplatform
    output['connected_checkout'] = storeplatform

    output['total_connected_platform'] = adplatform + paymentplatform + storeplatform

    output['integration'] = integation


    return jsonify(output), 200
