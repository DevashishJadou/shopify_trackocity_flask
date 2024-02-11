from flask import Blueprint, request, jsonify
import requests
import json, os
import hmac
import hashlib
from datetime import datetime


from .woocommerce import channel_bp
from ...db_model.sql_models import Shopify, order_table_dynamic, ordertable
from ...connection import db
# from integration.channel.woocommerce import channel_bp
# from db_model.sql_models import Shopify, order_table_dynamic, ordertable
# from connection import db

from sqlalchemy import MetaData

metadata = MetaData()

# channel_bp = Blueprint('clientchannel', __name__)

@channel_bp.route('/shopifyintegration', methods=['POST'])
def shopifyintegration():
	data = json.loads(request.get_data().decode("utf-8"))
	base_url = data['site_url']
	access_token = data['access_token']
	workspace = request.headers.get('workspace')

	user = Shopify.query.filter_by(workspace=workspace).first()
	if user:
		user.base_url = base_url
		user.access_token = access_token

		db.session.commit()
		return jsonify({'message': 'Inforamtion Updated Succesfully'}), 200

	else:
		user_make = Shopify(base_url=base_url, access_token=access_token, workspace=workspace)
		tablename = 'order_'+workspace
		if not metadata.tables.get(tablename):
			shopify_table = ordertable(tablename)
			shopify_table.create(bind=db.engine)
		db.session.add(user_make)
		db.session.commit()

	return jsonify({'status': 'success'}), 200




@channel_bp.route('/shopifyorders', methods=['POST'])
def shopify():

	# order = Shopify.query.filter_by(transcation_id=transcation_id).all()

	# Use the access token to make requests to the Shopify Admin API
	orders_endpoint = f'https://www.usemeworks.com/admin/api/2023-10/orders.json'
	access_token = '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'
	headers = {
		'Content-Type': 'application/json',
		'X-Shopify-Access-Token': access_token,
	}

	response = requests.get(orders_endpoint, headers=headers)

	if response.status_code == 200:
		orders_data = response.json()
		orders_data = orders_data['orders']
		
		tablename = 'order_hello2'
		# tablename = 'order_'+workspace
		
		orderTable = order_table_dynamic(tablename)
		orderTable.metadata = db.Model.metadata
		
		for data in orders_data:
			customer_ip = data['browser_ip']
			customer_user_agent = data['client_details']['user_agent']
			order_date = datetime.strptime(data['created_at'], "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%d %H:%M:%S")
			transcation_id = str(data['order_number'])
			total = float(data['total_price'])
			first_name = data['customer']['first_name']
			last_name = data['customer']['last_name']
			email = data['customer']['email']
			payment_method = str(data['payment_gateway_names'])

			order = orderTable.query.filter_by(transcation_id=transcation_id).filter_by(channel='shopify').first()
			if not order:
				order_make = orderTable(order_date=order_date, total=total, transcation_id=transcation_id, first_name=first_name, last_name=last_name, email=email, payment_method=payment_method, customer_ip=customer_ip, customer_user_agent=customer_user_agent, channel='shopify')
				db.session.add(order_make)

		db.session.commit()

		return jsonify({'status': 'success'}), 200
	else:
		print(f"Failed to retrieve orders. Status code: {response.status_code}, Response: {response.text}")
		return jsonify({'status': 'success'}), 400
