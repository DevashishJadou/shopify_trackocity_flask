from ..db_model.sql_models import ProductTable, UTMSource, UserRegister, CustomizeColumn
from ..connection import db

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import json
from sqlalchemy import text

import requests


setting_bp = Blueprint('setting', __name__)



@setting_bp.route('/taxrate/getrate', methods=['GET', 'OPTIONS'])
@cross_origin(origins='*', methods=['GET'], headers=['Content-Type'])
def get_taxrate():

	headers = request.headers
	userid = headers.get('workspaceId')
	tax = UserRegister.query.filter_by(workspace=userid).first()
	return jsonify({"taxrate": tax.tax_rate*100, "tax_on": tax.tax_on}), 200


@setting_bp.route('/taxrate/updaterate', methods=['POST', 'OPTIONS'])
@cross_origin(origins='*', methods=['POST'], headers=['Content-Type'])
def update_taxrate():

	headers = request.headers
	userid = headers.get('workspaceId')
	data = json.loads(request.data)
	tax = UserRegister.query.filter_by(workspace=userid).first()
	tax.tax_rate = round(data.get('taxrate')/100,3)
	tax.tax_on = data.get('tax_on')
	db.session.commit()
	return jsonify(message="Updated Successfully"), 200

	

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
	sale_price = data.get('sale_price')
	product = ProductTable.query.filter_by(workspaceid=userid, sale_price=sale_price).first()
	if product:
		if product.id != id:       
			return jsonify(message='Each sale price must be unique and can be assigned to only one product'), 409
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
def put_delete_product():
    headers = request.headers
    workspace = headers.get('workspaceId')
    body = json.loads(request.data)
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
	



@setting_bp.route('/utm_source/get_utmsource', methods=['GET', 'OPTIONS'])
@cross_origin(origins='*', methods=['GET'], headers=['Content-Type'])
def get_utmsource_data():

	headers = request.headers
	userid = headers.get('workspaceId')
	utm_sources = UTMSource.query.filter_by(workspace=userid).all()
	
	utm_source_data = []
	for utm_source in utm_sources:        
        # Store the data for each client in a nested dictionary
		utm_source_data.append({
			'id': utm_source.id,
			'displayname': utm_source.displayname,
			'utm_field': utm_source.utm_field,
			'value': utm_source.value,
			'utm_subfield': utm_source.utm_sub_field
		})

	return jsonify(utm_source_data), 200


@setting_bp.route('/utm_source/create_utmsource', methods=['POST', 'OPTIONS'])
@cross_origin(origins='*', methods=['POST'], headers=['Content-Type'])
def post_create_utmsource():

	headers = request.headers
	userid = headers.get('workspaceId')
	data = json.loads(request.data)
	utm_source = UTMSource.query.filter_by(workspace=userid, utm_field=data.get('utm_field'), value=data.get('value'), utm_sub_field=data.get('utm_subfield')).first()
	if utm_source:       
		return jsonify(message='The combination alread exists'), 409
	utm_source = UTMSource(workspace=userid, utm_field=data.get('utm_field'), value=data.get('value'), utm_sub_field=data.get('utm_subfield'), displayname=data.get('displayname'))
	
	db.session.add(utm_source)
	db.session.commit()

	return jsonify(message='Product Added', id=utm_source.id), 201



@setting_bp.route('/utm_source/update_utmsource', methods=['PUT', 'OPTIONS'])
@cross_origin(origins='*', methods=['PUT'], headers=['Content-Type'])
def put_update_utmsource():

	headers = request.headers
	userid = headers.get('workspaceId')
	data = json.loads(request.data)
	id = data.get('id')
	utm_source = UTMSource.query.filter_by(workspace=userid, id=id).first()
	if not utm_source:       
		return jsonify(message='Something went wrong. Try after sometime'), 409
	utm_source.utm_field = data.get('utm_field')
	utm_source.value = data.get('value')
	utm_source.utm_sub_field = data.get('utm_subfield')
	utm_source.displayname = data.get('displayname')
	
	db.session.commit()

	return jsonify(message='Product Updated'), 201


@setting_bp.route('/utm_source/delete_utmsource', methods=['PUT', 'OPTIONS'])
@cross_origin(origins='*', methods=['PUT', 'OPTIONS'], headers=['Content-Type'])
def put_delete_utmsource():
    headers = request.headers
    workspace = headers.get('workspaceId')
    body = json.loads(request.data)
    id = body.get('id')
    row_to_delete = UTMSource.query.filter_by(id=id, workspace=workspace).first()

    if row_to_delete:
        # If the row exists, delete it
        db.session.delete(row_to_delete)
        db.session.commit()  # Commit the transaction to delete the row
        return jsonify({"message": "Source Removed Successfully"}), 200
    else:
        # Return an appropriate message if the row doesn't exist
        return jsonify({"message": "No Such Product found"}), 404



@setting_bp.route('/resource_useage', methods=['GET', 'OPTIONS'])
@cross_origin(origins='*', methods=['GET', 'OPTIONS'], headers=['Content-Type', 'Authorization'])
def page_limit_get():
    headers = request.headers
    workspace = headers.get('workspaceId')
    sql_query = text("""
				select sum(value)*100.0 / page_limit
				from mongo_metric mm 
				left join (
					SELECT workspace, complete_name, product_type::int*1000 page_limit,
						CASE 
							WHEN EXTRACT(DAY FROM ur.plan_till) >= EXTRACT(DAY FROM NOW()) 
							THEN DATE_TRUNC('month', NOW()) - INTERVAL '1 month' + INTERVAL '1 day' * (EXTRACT(DAY FROM ur.plan_till) - 1)
							ELSE DATE_TRUNC('month', NOW()) + INTERVAL '1 day' * (EXTRACT(DAY FROM ur.plan_till) - 1)
						END AS adjusted_plan_till
					FROM 
						user_register ur
					WHERE 
						isactive = true
					) as u on u.workspace = mm.workspace 
				where metric = 'page_view' and mm.dated >= u.adjusted_plan_till
				and mm.workspace = :workspace
				group by page_limit
					 """)
    result = db.session.execute(sql_query, {'workspace': workspace})
    xx =  result.fetchall()
    page_view_usage = xx[0][0] if xx else 0

    user = UserRegister.query.filter_by(workspace=workspace).first()
    plan = user.plan
    is_logout = user.is_logout

    return jsonify({"data": page_view_usage, "plan": plan, "is_logout": is_logout}), 200
    #return jsonify({"data":page_view_usage, "plan":plan}), 200
    # return jsonify({"data":page_view_usage}), 200



@setting_bp.route('/update_logout_status', methods=['PUT', 'OPTIONS'])
@cross_origin(origins='*', methods=['PUT', 'OPTIONS'], headers=['Content-Type', 'Authorization'])
def update_logout_status():
    headers = request.headers
    workspace = headers.get('workspaceId')  # Get user workspace ID
    agencyid = headers.get('agencyid')
    data = json.loads(request.data)         # Get request body
    new_status = data.get('is_logout')      # Get new value for is_logout
    
    # if agencyid is null
    if not agencyid:
        user = UserRegister.query.filter_by(workspace=workspace).first()
        
        if not user:
            return jsonify({"message": "User not found"}), 404
        
    
        user.is_logout = new_status  # Update value in database
        db.session.commit()          # Save changes

    # if agency id is not null
    else:
        users = UserRegister.query.filter_by(agencyid=agencyid).all()
        
        for user in users:
            user.is_logout = new_status
        db.session.commit()    
            
    if new_status:
        print(f'User {workspace} has been logged out.')
    else:
        print(f'User {workspace} has been logged in.')    
    return jsonify({"message": "Logout status updated successfully"}), 200
    


@setting_bp.route('/reporting/get_customize_column', methods=['GET', 'OPTIONS'])
@cross_origin(origins='*', methods=['GET', 'OPTIONS'], headers=['Content-Type', 'Authorization'])
def reporting_get_customize_column():
	headers = request.headers
	workspace = headers.get('workspaceId')
	params = request.args
	view = params.get('view_name', None)
	report = params.get('report', 'reporting')

	if not view:
		sql_query0 = db.text("SELECT distinct(view_name) FROM customize_column WHERE workspaceid = :workspace AND report = :report and latest_view is True")
		result = db.session.execute(sql_query0, {'workspace': workspace, 'report':report})
		data = result.fetchall()
		view = data[0][0]

	sql_query = db.text("SELECT report, workspaceid, field, seq FROM customize_column WHERE is_custom_column IS False AND workspaceid = :workspace AND report = :report AND view_name = :view")
	result = db.session.execute(sql_query, {'workspace': workspace, 'report':report, 'view':view})
	data = result.fetchall()
	columns = ["report", "workspace", "field", "seq"]
	results = [dict(zip(columns, row)) for row in data]

	sql_query2 = db.text("SELECT report, workspaceid, field, seq, custom_formula, is_custom_column, name, is_custom_used, custom_id FROM customize_column WHERE is_custom_column IS TRUE AND workspaceid = :workspace AND report = :report AND view_name = :view")
	result2 = db.session.execute(sql_query2, {'workspace': workspace, 'report':report, 'view':view})
	data2 = result2.fetchall()
	columns2 = ["report", "workspace", "field", "seq", "customFormula", "isCustomColumn", "name", "isAdded", "id"]
	results2 = [dict(zip(columns2, row)) for row in data2]
	results.extend(results2)

	sql_query3 = db.text("SELECT distinct(view_name) FROM customize_column WHERE workspaceid = :workspace AND report = :report")
	result3 = db.session.execute(sql_query3, {'workspace': workspace, 'report':report})
	data3 = result3.fetchall()
	result3 = [row[0] for row in data3]

	results = {'data': results, 'views': result3, 'current_view':view}
	return jsonify(results),200



@setting_bp.route('/reporting/update_customize_column', methods=['POST', 'OPTIONS'])
@cross_origin(origins='*', methods=['POST', 'OPTIONS'], headers=['Content-Type', 'Authorization'])
def reporting_update_customize_column():
	headers = request.headers
	workspace = headers.get('workspaceId')
	param = request.args
	body = json.loads(request.data)
	report = param.get('report')
	view = param.get('view_name', 'myview')
	deleteview = param.get('deleteview', False)
	
	CustomizeColumn.query.filter_by(workspaceid=workspace, view_name=view).delete()

	if deleteview:
		db.session.commit()
		return jsonify({"message":"Deleted"}), 200

	for row in body:
		field = row.get('field')
		seq = row.get('seq')
		name = row.get('name', None)
		is_custom_column = row.get('isCustomColumn', None)
		custom_formula = row.get('customFormula', None)
		is_custom_used = row.get('isAdded', None)
		custom_id = row.get('id', None)

		sql_query = db.text("UPDATE customize_column SET latest_view = false WHERE workspaceid = :workspace AND report = :report")
		db.session.execute(sql_query, {'workspace': workspace, 'report':report})
		ff = CustomizeColumn(workspaceid=workspace, report=report, field=field, seq=seq, custom_formula=custom_formula, is_custom_column=is_custom_column, name=name, is_custom_used=is_custom_used, custom_id=custom_id, view_name=view, latest_view=True)
		db.session.add(ff)
	db.session.commit()
	
	return jsonify({"message":"Updated"}), 201




@setting_bp.route('/frontenderror', methods=['POST', 'OPTIONS'])
@cross_origin(origins='*', methods=['POST', 'OPTIONS'], headers=['Content-Type', 'Authorization'])
def error_to_slack():
	headers = request.headers
	workspace = headers.get('workspaceId')
	param = request.args
	param = json.loads(request.data)

	SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/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"
	payload = {
				"text": f"🚨 *{workspace}* : *{param.get('type', 'Unknown Error')} Error Report*",
				"attachments": [
					{
						"fields": [
						{
							"title": "API Endpoint",
							"value": param.get('endpoint', 'N/A'),
							"short": False
						},
						{
							"title": "Error Message",
							"value": param.get('message', 'N/A'),
							"short": False
						},
						{
							"title": "Error stack",
							"value": param.get('stack', 'N/A'),
							"short": False
						},
						{
							"title": "Time",
							"value": param.get('time', 'N/A'),
							"short": False
						}
					]
					}
					]
				}

	response = requests.post(SLACK_WEBHOOK_URL, json=payload)

	if response.status_code == 200:
		return jsonify({'status': 'success', 'message': 'Sent to Slack'}), 200
	else:
		return jsonify({'status': 'error', 'message': 'Failed to send to Slack'}), 500