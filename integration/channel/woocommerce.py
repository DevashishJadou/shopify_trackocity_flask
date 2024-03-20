from flask import Blueprint, request, jsonify
import json, os
from flask_cors import cross_origin

from ...db_model.sql_models import WooCommerce, order_table_dynamic, ordertable
from ...connection import db
from ...dbrule import dup_order_rule
# from db_model.sql_models import WooCommerce, order_table_dynamic, ordertable
# from connection import db

from sqlalchemy import MetaData, Table


metadata = MetaData()

channel_bp = Blueprint('clientchannel', __name__)

@channel_bp.route('/woocommerceintegration', methods=['POST'])
@cross_origin()
def woocommerceintegration():
    header = request.headers
    _body = json.loads(request.get_data())
    workspace = header.get('workspaceId')
    _woocommerce_client_secret = _body['woocommerce_client_secret']
    
    user = WooCommerce.query.filter_by(workspace=workspace).first()
    if user:
        user.woocommerce_client_secret = _woocommerce_client_secret
        db.session.commit()
        return jsonify({'message': 'Inforamtion Updated Succesfully'}), 200
    
    else:
        razorpay_register = WooCommerce(workspace=workspace, client_secret=_woocommerce_client_secret)
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
            db.session.commit()
        except Exception as e:
            print(f'Woocommerce client secret: {e.msg}')
            return jsonify({'error': 'Something went Wrong'}), 500
    return jsonify({'message': 'success'}), 200


@channel_bp.route('/<workspace>/woocommercewebhook', methods=['POST'])
def woocommercewebook(workspace):
	# b'{"id":5935,"parent_id":0,"status":"pending","currency":"INR","version":"8.4.0","prices_include_tax":false,
	# "date_created":"2023-12-18T18:12:14","date_modified":"2023-12-18T18:12:14","discount_total":"0.00",
	# "discount_tax":"0.00","shipping_total":"0.00","shipping_tax":"0.00","cart_tax":"0.00","total":"399.00",
	# "total_tax":"0.00","customer_id":1,"order_key":"wc_order_rEmFNWCqTWOKf",
	# "billing":{"first_name":"Ankur","last_name":"Gupta","company":"","address_1":"","address_2":"",
	# 	"city":"","state":"","postcode":"","country":"","email":"ankurguptajp@gmail.com","phone":""},
	# "shipping":{"first_name":"","last_name":"","company":"","address_1":"","address_2":"","city":"","state":"",
	# 	"postcode":"","country":"","phone":""},
	# "payment_method":"razorpay","payment_method_title":"Credit Card\\/Debit Card\\/NetBanking","transaction_id":"",
	# "customer_ip_address":"49.36.236.186",
	# "customer_user_agent":"Mozilla\\/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit\\/537.36 (KHTML, like Gecko) Chrome\\/120.0.0.0 Safari\\/537.36 Edg\\/120.0.0.0",
	# "created_via":"checkout","customer_note":"","date_completed":null,"date_paid":null,
	# "cart_hash":"636ee354ca9ff0cda98284b977a6242a","number":"5935",
	# "meta_data":[{"id":43635,"key":"_vp_words_count","value":"14"},
	# {"id":43663,"key":"is_vat_exempt","value":"no"},{"id":43664,"key":"ce4wp_checkout_consent","value":"0"},
	# {"id":43665,"key":"_wcf_flow_id","value":"5867"},{"id":43666,"key":"_wcf_checkout_id","value":"5869"},
	# {"id":43667,"key":"_wpfunnels_checkout_id","value":"5869"},
	# {"id":43668,"key":"is_magic_checkout_order","value":"no"}],
	# "line_items":[{"id":75,"name":"IROF","product_id":5863,"variation_id":0,"quantity":1,"tax_class":"",
	# 	"subtotal":"399.00","subtotal_tax":"0.00","total":"399.00","total_tax":"0.00","taxes":[],"meta_data":[],
	# 	"sku":"","price":399,
	# 	"image":{"id":"5902","src":"https:\\/\\/sannidhyabaweja.com\\/wp-content\\/uploads\\/2023\\/12\\/web-2.webp"},"parent_name":null}],
	# 	"tax_lines":[],"shipping_lines":[],"fee_lines":[],"coupon_lines":[],"refunds":[],
	# 	"payment_url":"https:\\/\\/sannidhyabaweja.com\\/checkout\\/order-pay\\/5935\\/?pay_for_order=true&key=wc_order_rEmFNWCqTWOKf",
	# 	"is_editable":true,"needs_payment":true,"needs_processing":true,"date_created_gmt":"2023-12-18T12:42:14",
	# 	"date_modified_gmt":"2023-12-18T12:42:14","date_completed_gmt":null,"date_paid_gmt":null,
	# 	"currency_symbol":"\\u20b9","_links":{"self":[{"href":"https:\\/\\/sannidhyabaweja.com\\/wp-json\\/wc\\/v3\\/orders\\/5935"}],
	# 	"collection":[{"href":"https:\\/\\/sannidhyabaweja.com\\/wp-json\\/wc\\/v3\\/orders"}],
	# 	"customer":[{"href":"https:\\/\\/sannidhyabaweja.com\\/wp-json\\/wc\\/v3\\/customers\\/1"}]}}
	
	user = WooCommerce.query.filter_by(workspace=workspace).first()
	if not user.isactive:
		return jsonify({'error': 'Unathorized'}), 403

	request_data = request.get_data().decode("utf-8")
	request_data = json.loads(request_data)
	signature = request.headers.get('X-Wc-Webhook-Signature')

	tablename ='order_'+workspace
	orderTable = order_table_dynamic(tablename)
	orderTable.metadata = db.Model.metadata

	order_date = request_data['date_created']
	total = request_data['total']
	transcation_id = request_data['order_key']
	first_name = request_data['billing']['first_name']
	last_name = request_data['billing']['last_name']
	email = request_data['billing']['email']
	payment_method = request_data['payment_method']
	customer_ip = request_data['customer_ip_address']
	customer_user_agent = request_data['customer_user_agent']

	order = orderTable.query.filter_by(transcation_id=transcation_id).filter_by(channel='woocommerce').first()
	if order:
		order.total = total
		order.payment_method = payment_method
		return jsonify(message='Order updated'), 200
	
	order_make = orderTable(order_date=order_date, total=total, transcation_id=transcation_id, first_name=first_name, last_name=last_name, email=email, payment_method=payment_method, customer_ip=customer_ip, customer_user_agent=customer_user_agent, channel='woocommerce')
	db.session.add(order_make)
	db.session.commit()

	return jsonify({'status': 'success'}), 200