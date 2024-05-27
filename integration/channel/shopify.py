from flask import request, jsonify
import requests
import json, os
from datetime import datetime
from flask_cors import cross_origin


from .woocommerce import channel_bp
from ...db_model.sql_models import Shopify, order_table_dynamic, ordertable
from ...connection import db
from ...dbrule import dup_order_rule


from sqlalchemy import MetaData

metadata = MetaData()

# channel_bp = Blueprint('clientchannel', __name__)

@channel_bp.route('/shopifyintegration', methods=['POST'])
@cross_origin()
def shopifyintegration():
	data = json.loads(request.get_data().decode("utf-8"))
	base_url = data['site_url']
	access_token = data['access_token']
	workspace = request.headers.get('workspaceId')

	user = Shopify.query.filter_by(workspace=workspace).first()
	if user:
		user.base_url = base_url
		user.access_token = access_token

		db.session.commit()
		return jsonify({'message': 'Inforamtion Updated Succesfully'}), 200

	else:
		user_make = Shopify(base_url=base_url, access_key=access_token, workspace=workspace, active=True)
		tablename = 'order_'+workspace
		try:
			if not metadata.tables.get(tablename):
				shopify_table = ordertable(tablename)
				try:
					shopify_table.create(bind=db.engine)
					db.session.add(user_make)
					dup_order_rule(tablename)
				except:
					pass
			db.session.commit()
		except Exception as e:
			print(f'Shopify client secret: {e.msg}')
			return jsonify({'error': 'Something went Wrong'}), 500

	return jsonify({'message': 'success'}), 200




@channel_bp.route('/shopifyorders', methods=['POST'])
def shopify():
	header =  request.headers
	userid = header.get("workSpaceId")
	orders = Shopify.query.filter_by(workspace=userid).filter_by(active=True).all()

	
	for order in orders:
		# Use the access token to make requests to the Shopify Admin API
		# orders_endpoint = f'https://www.usemeworks.com/admin/api/2023-10/orders.json'
		# access_token = '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'
		orders_endpoint = order.base_url
		access_token = order.access_key
		headers = {
			'Content-Type': 'application/json',
			'X-Shopify-Access-Token': access_token,
		}

		response = requests.get(orders_endpoint, headers=headers)

		if response.status_code == 200:
			orders_data = response.json()
			orders_data = orders_data['orders']
			
			tablename = 'order_'+userid
			
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

				order = orderTable.query.filter_by(transcation_id=transcation_id).first()
				if not order:
					order_make = orderTable(order_date=order_date, total=total, transcation_id=transcation_id, first_name=first_name, last_name=last_name, email=email, payment_method=payment_method, customer_ip=customer_ip, customer_user_agent=customer_user_agent)
					db.session.add(order_make)

			db.session.commit()

		else:
			print(f"Failed to retrieve orders. Status code: {response.status_code}, Response: {response.text}")
			return jsonify({'status': 'success'}), 400
	return jsonify({'status': 'success'}), 200
