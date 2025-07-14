from flask import Blueprint, request, jsonify
import json, os, requests
import time
from datetime import datetime, timedelta
from flask_cors import cross_origin
from sqlalchemy import desc

from .db_model.sql_models import Payment, UserRegister
from .connection import db


trackocitypayment_bp = Blueprint('trackocitypayment', __name__)


baseUrl = "https://sandbox.cashfree.com/"

@trackocitypayment_bp.route('/payment_link', methods=['POST'])
@cross_origin(origins='*', methods=['POST', 'OPTIONS'], headers=['Content-Type', 'Authorization'])
def create_subscription():
    try:
        headers = request.headers
        userid = headers.get('workspaceId')
        req_data = request.get_json()
        print("Request body:", json.dumps(req_data, indent=2))

        # Build the request body
        request_body = {
            **req_data,
            # Uncomment and adjust if needed:
            # "subscription_meta": {
            #     **(req_data.get("subscription_meta") or {}),
            #     "return_url": req_data.get("subscription_meta", {}).get("return_url", "https://yourdomain.com/return"),
            #     "notify_url": "https://yourdomain.com/api/webhook",
            # },
        }

        headers = {
            "Content-Type": "application/json",
            "x-api-version": "2023-08-01",
            "x-client-id": os.environ.get('_CASHFREE_CLIENT_ID'),
            "x-client-secret": os.environ.get('_CASHFREE_CLIENT_SECRET'),
        }

        response = requests.post(
            f"{baseUrl}pg/subscriptions",
            headers=headers,
            json=request_body
        )

        try:
            result = response.json()
        except ValueError:
            result = {"error": "Invalid JSON response from Cashfree"}

        print("Full Cashfree response:", json.dumps(result, indent=2))

        if result.get("subs_payment_modes") == []:
            print("Warning: No payment modes available in response")

        if not response.ok:
            print("Cashfree API Error:", result)
            return jsonify(result), response.status_code

        # Additional validation
        if not result.get("subscription_session_id"):
            raise Exception("No session ID received")

        customer_detail = result.get('customer_details', {})
        name = customer_detail.get('customer_name', 'Unknown')
        email = customer_detail.get('customer_email')
        subscription_id = result.get('subscription_id')
        transaction_id = result.get('cf_subscription_id')

        time.sleep(5)  # Wait for the subscription to be created
        payurl = f"{baseUrl}api/v2/subscriptions/{transaction_id}"
        payresponse = requests.get(payurl, headers=headers)
        payresult = payresponse.json()
        print(f"payresult:{payresult}")

        link = payresult.get('subscription').get('authLink')

        row = Payment(workspace = userid, completename = name, email = email, order_id = subscription_id, transaction_id = transaction_id, link=link, status = 'pending')
        db.session.add(row)
        db.session.commit()
        print("Subscription created successfully:", result)
        return jsonify(link), 200

    except Exception as err:
        print("Server Error:", err)
        return jsonify({"error": "Subscription creation failed", "details": str(err)}), 500




@trackocitypayment_bp.route('/cancel_subscription', methods=['POST'])
@cross_origin(origins='*', methods=['POST', 'OPTIONS'], headers=['Content-Type', 'Authorization'])
def cancel_subscription():
    try:
        headers = request.headers
        userid = headers.get('workspaceId')
        data = Payment.query.filter_by(workspace=userid).order_by(desc(Payment.id)).first()
        subscription_id = data.order_id if data else None

        if not subscription_id:
            return jsonify({"error": "Subscription ID is required"}), 400

        url = f"{baseUrl}pg/subscriptions/{subscription_id}/manage"
        
        headers = {
            "Content-Type": "application/json",
            "x-api-version": "2023-08-01",
            "x-client-id": os.environ.get('_CASHFREE_CLIENT_ID'),
            "x-client-secret": os.environ.get('_CASHFREE_CLIENT_SECRET')
        }
        
        payload = {
            "subscription_id": subscription_id,
            "action": "CANCEL"
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        try:
            result = response.json()
        except ValueError:
            # Cashfree sometimes returns plain text errors; handle gracefully
            result = {"error": "Invalid response from Cashfree", "response_text": response.text}

        if not response.ok:
            return jsonify(result), response.status_code
        
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": "Subscription cancellation failed", "details": str(e)}), 500
    



@trackocitypayment_bp.route('/get_subscription', methods=['GET'])
@cross_origin(origins='*', methods=['GET', 'OPTIONS'], headers=['Content-Type', 'Authorization'])
def get_subscription():

    # headers = request.headers
    # userid = headers.get('subref')
    # data = Payment.query.filter_by(workspace=userid).order_by(desc(Payment.id)).first()
    # subscription_id = data.order_id if data else None

    # if not subscription_id:
    #     return jsonify({"error": "Subscription ID is required"}), 400

    url = f"https://sandbox.cashfree.com/api/v2/subscriptions/1142709"
    
    headers = {
        "Content-Type": "application/json",
        "x-api-version": "2023-08-01",
        "x-client-id": os.environ.get('_CASHFREE_CLIENT_ID'),
        "x-client-secret": os.environ.get('_CASHFREE_CLIENT_SECRET')
    }
    
    # payload = {
    #     "subscription_id": subscription_id,
    #     "action": "CANCEL"
    # }
    
    response = requests.get(url, headers=headers)

    import pdb; pdb.set_trace()