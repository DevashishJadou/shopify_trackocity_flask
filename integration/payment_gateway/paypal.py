from flask import Blueprint, request, jsonify
# from integration.payment_gateway.razorpay import payment_bp
from payment_gateway.razorpay import payment_bp

_token = 'ECvJ_yBNz_UfMmCvWEbT_2ZWXdzbFFQZ-1Y5K2NGgeHn'

headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer '+_token,
}


@payment_bp.route('/paypalwebhookcreate', methods=['POST'])
def webhook_create():
    data = '{ "url": "https://example.com/example_webhook", "event_types": [ { "name": "PAYMENT.AUTHORIZATION.CREATED" }, { "name": "PAYMENT.AUTHORIZATION.VOIDED" } ] }'

    # response = requests.post('https://api-m.sandbox.paypal.com/v1/notifications/webhooks', headers=headers, data=data)


@payment_bp.route('/paypalwebhook', methods=['POST'])
def webhook_endpoint():
    pass
    