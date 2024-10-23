from ..db_model.sql_models import ProductTable
from ..connection import db

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import json


setting_bp = Blueprint('setting', __name__)


@setting_bp.route('/product/getproduct', methods=['GET', 'OPTIONS'])
@cross_origin(origins='*', methods=['GET'], headers=['Content-Type'])
def get_productdata():

	headers = request.headers
	userid = headers.get('workspaceId')
	products = ProductTable.query.filter_by(workspaceid=userid).all()
	
	product_data = []
	for product in products:        
        # Store the data for each client in a nested dictionary
		product_data.append({
			'id': product.id,
			'product_name': product.product_name,
			'cost_price': product.cost_price,
			'sale_price': product.sale_price
		})

	return jsonify(product_data), 200


@setting_bp.route('/product/createproduct', methods=['POST', 'OPTIONS'])
@cross_origin(origins='*', methods=['POST'], headers=['Content-Type'])
def post_createproduct():

	headers = request.headers
	userid = headers.get('workspaceId')
	data = json.loads(request.data)
	sale_price = data.get('sale_price')
	product = ProductTable.query.filter_by(workspaceid=userid, sale_price=sale_price).first()
	if product:       
		return jsonify(message='Each sale price must be unique and can be assigned to only one product'), 409
	product = ProductTable(workspaceid=userid, product_name=data.get('product_name'), cost_price=data.get('cost_price'), sale_price=data.get('sale_price'))
	
	db.session.add(product)
	db.session.commit()

	return jsonify(message='Product Added', id=product.id), 201



@setting_bp.route('/product/updateproduct', methods=['PUT', 'OPTIONS'])
@cross_origin(origins='*', methods=['PUT'], headers=['Content-Type'])
def put_updateproduct():

	headers = request.headers
	userid = headers.get('workspaceId')
	data = json.loads(request.data)
	id = data.get('id')
	product = ProductTable.query.filter_by(workspaceid=userid, id=id).first()
	if not product:       
		return jsonify(message='Something went wrong. Try after sometime'), 409
	product.product_name = data.get('product_name')
	product.cost_price = data.get('cost_price')
	product.sale_price = data.get('sale_price')
	
	db.session.commit()

	return jsonify(message='Product Updated'), 201


@setting_bp.route('/product/deleteproduct', methods=['PUT', 'OPTIONS'])
@cross_origin(origins='*', methods=['PUT', 'OPTIONS'], headers=['Content-Type'])
def integration_google_account_delete():
    headers = request.headers
    workspace = headers.get('workspaceId')
    body = request.args
    id = body.get('id')
    row_to_delete = ProductTable.query.filter_by(id=id, workspaceid=workspace).first()

    if row_to_delete:
        # If the row exists, delete it
        db.session.delete(row_to_delete)
        db.session.commit()  # Commit the transaction to delete the row
        return jsonify({"message": "Product Removed Successfully"}), 200
    else:
        # Return an appropriate message if the row doesn't exist
        return jsonify({"message": "No Such Product found"}), 404