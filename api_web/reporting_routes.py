# reporting_routes

from ..db_model.sql_models import UserRegister
from ..connection import db
# from db_model.sql_models import UserRegister
# from connection import db

from flask import Blueprint, request, jsonify

from .schema import FB
# from api_web.schema import FB
from flask_cors import cross_origin
import json

report_bp = Blueprint('repoting', __name__)


@report_bp.route('/alluser', methods=['GET', 'OPTIONS'])
@cross_origin(origins='*', methods=['GET'], headers=['Content-Type'])
def get_all_user():
	page = request.args.get('page', default=1, type=int)
	per_page = request.args.get('per_page', default=3, type=int)

	users = UserRegister.query.paginate(
		page = page,
		per_page = per_page
	)

	result = FB().dump(users, many=True)

	return jsonify({
			"users":result,
		}), 200 


@report_bp.route('/fbtable', methods=['GET', 'OPTIONS'])
@cross_origin(origins='*', methods=['GET'], headers=['Content-Type'])
def get_reporttabledatafacebook():

	headers = request.headers
	body = request.args
	startdate = body.get('startdate')
	enddate = body.get('enddate')
	attribute = body.get('attribute')
	userid = headers.get('workspaceId')
	timezone = '5.5 hours'
	user = UserRegister.query.filter_by(workspace=userid).first()

	if attribute == 'first':
		sql_query = db.text("select * from table_facebookfirstattribute(:workspace, :productid, :startdate, :enddate, :timezone)")
	else:	
		sql_query = db.text("select * from table_facebooklastattribute(:workspace, :productid, :startdate, :enddate, :timezone)")

	result = db.session.execute(sql_query, {'workspace': userid, 'productid':user.productid, 'startdate':startdate, 'enddate':enddate, 'timezone':timezone})
	data = result.fetchall()

	fbdata = {}
	fbadsdata = {"impression":0, "clicks":0, "spend":0.0, "sales":0, "revenue":0.0}
	for row in data:
		campaign_id = row[0]
		ad_set_id = row[2]
		ad_id = row[4]

		if campaign_id not in fbdata:
			fbdata[campaign_id] = {
				"campaign_id": campaign_id,
				"campaign_name": row[1],
				"ad_sets": {},
				"impression": 0,
				"clicks": 0,
				"spend" : 0.0,
				"sales" : 0,
				"revenue" : 0.0
			}

		if ad_set_id not in fbdata[campaign_id]["ad_sets"]:
			fbdata[campaign_id]["ad_sets"][ad_set_id] = {
				"ad_set_id": ad_set_id,
				"ad_set_name": row[3],
				"ads": [],
				"impression": 0,
				"clicks": 0,
				"spend" : 0.0,
				"sales" : 0,
				"revenue" : 0.0
			}

		fbdata[campaign_id]["ad_sets"][ad_set_id]["ads"].append({
			"ad_id": ad_id,
			"ad_name": row[5],
			"impressions": row[6],
			"clicks": row[7],
			"spend": float(row[8]),
			"sales": row[9],
			"revenue": float(row[10])
		})

		fbadsdata["impression"] = fbadsdata["impression"] + row[6]
		fbadsdata["clicks"] = fbadsdata["clicks"] + row[7]
		fbadsdata["spend"] = fbadsdata["spend"] + float(row[8])
		fbadsdata["sales"] = fbadsdata["sales"] + row[9]
		fbadsdata["revenue"] = fbadsdata["revenue"] + float(row[10])
		
		fbdata[campaign_id]["impression"] = fbdata[campaign_id]["impression"] + row[6]
		fbdata[campaign_id]["clicks"] = fbdata[campaign_id]["clicks"] + row[7]
		fbdata[campaign_id]["spend"] = fbdata[campaign_id]["spend"] + float(row[8])
		fbdata[campaign_id]["sales"] = fbdata[campaign_id]["sales"] + row[9]
		fbdata[campaign_id]["revenue"] = fbdata[campaign_id]["revenue"] + float(row[10])

		fbdata[campaign_id]["ad_sets"][ad_set_id]["impression"] = fbdata[campaign_id]["ad_sets"][ad_set_id]["impression"] + row[6]
		fbdata[campaign_id]["ad_sets"][ad_set_id]["clicks"] = fbdata[campaign_id]["ad_sets"][ad_set_id]["clicks"] + row[7]
		fbdata[campaign_id]["ad_sets"][ad_set_id]["spend"] = fbdata[campaign_id]["ad_sets"][ad_set_id]["spend"] + float(row[8])
		fbdata[campaign_id]["ad_sets"][ad_set_id]["sales"] = fbdata[campaign_id]["ad_sets"][ad_set_id]["sales"] + row[9]
		fbdata[campaign_id]["ad_sets"][ad_set_id]["revenue"] = fbdata[campaign_id]["ad_sets"][ad_set_id]["revenue"] + float(row[10])


	# Convert the nested structure to a list of dates with campaigns
	campaign_list = list(fbdata.values())
	for date_entry in campaign_list:
		date_entry["ad_sets"] = list(date_entry["ad_sets"].values())

	fbadsdata["campaign"] = campaign_list
	# Convert to JSON
	# json_data = json.dumps(campaign_list)n
	json_data = fbadsdata


	return jsonify(json_data)



@report_bp.route('/ggtable', methods=['GET', 'OPTIONS'])
@cross_origin(origins='*', methods=['GET'], headers=['Content-Type'])
def get_reporttabledatagoogle():

	headers = request.headers
	body = request.args
	startdate = body.get('startdate')
	enddate = body.get('enddate')
	attribute = body.get('attribute')
	userid = headers.get('workspaceId')
	timezone = '5.5 hours'
	user = UserRegister.query.filter_by(workspace=userid).first()

	if attribute == 'first':
		sql_query = db.text("select * from table_googlefirstattribute(:workspace, :productid, :startdate, :enddate, :timezone)")
	else:	
		sql_query = db.text("select * from table_googlelastattribute(:workspace, :productid, :startdate, :enddate, :timezone)")

	result = db.session.execute(sql_query, {'workspace': userid, 'productid':user.productid, 'startdate':startdate, 'enddate':enddate, 'timezone':timezone})
	data = result.fetchall()

	ggdata = {}
	ggadsdata = {"impression":0, "clicks":0, "spend":0.0, "sales":0, "revenue":0.0}
	for row in data:
		campaign_id = row[0]
		ad_set_id = row[2]
		ad_id = row[4]

		if campaign_id not in ggdata:
			ggdata[campaign_id] = {
				"campaign_id": campaign_id,
				"campaign_name": row[1],
				"ad_sets": {},
				"impression": 0,
				"clicks": 0,
				"spend" : 0.0,
				"sales" : 0,
				"revenue" : 0.0
			}

		if ad_set_id not in ggdata[campaign_id]["ad_sets"]:
			ggdata[campaign_id]["ad_sets"][ad_set_id] = {
				"ad_set_id": ad_set_id,
				"ad_set_name": row[3],
				"ads": [],
				"impression": 0,
				"clicks": 0,
				"spend" : 0.0,
				"sales" : 0,
				"revenue" : 0.0
			}

		ggdata[campaign_id]["ad_sets"][ad_set_id]["ads"].append({
			"ad_id": ad_id,
			"ad_name": row[5],
			"impressions": row[6],
			"clicks": row[7],
			"spend": float(row[8]),
			"sales": row[9],
			"revenue": float(row[10])
		})

		ggadsdata["impression"] = ggadsdata["impression"] + row[6]
		ggadsdata["clicks"] = ggadsdata["clicks"] + row[7]
		ggadsdata["spend"] = ggadsdata["spend"] + float(row[8])
		ggadsdata["sales"] = ggadsdata["sales"] + row[9]
		ggadsdata["revenue"] = ggadsdata["revenue"] + float(row[10])
		
		ggdata[campaign_id]["impression"] = ggdata[campaign_id]["impression"] + row[6]
		ggdata[campaign_id]["clicks"] = ggdata[campaign_id]["clicks"] + row[7]
		ggdata[campaign_id]["spend"] = ggdata[campaign_id]["spend"] + float(row[8])
		ggdata[campaign_id]["sales"] = ggdata[campaign_id]["sales"] + row[9]
		ggdata[campaign_id]["revenue"] = ggdata[campaign_id]["revenue"] + float(row[10])

		ggdata[campaign_id]["ad_sets"][ad_set_id]["impression"] = ggdata[campaign_id]["ad_sets"][ad_set_id]["impression"] + row[6]
		ggdata[campaign_id]["ad_sets"][ad_set_id]["clicks"] = ggdata[campaign_id]["ad_sets"][ad_set_id]["clicks"] + row[7]
		ggdata[campaign_id]["ad_sets"][ad_set_id]["spend"] = ggdata[campaign_id]["ad_sets"][ad_set_id]["spend"] + float(row[8])
		ggdata[campaign_id]["ad_sets"][ad_set_id]["sales"] = ggdata[campaign_id]["ad_sets"][ad_set_id]["sales"] + row[9]
		ggdata[campaign_id]["ad_sets"][ad_set_id]["revenue"] = ggdata[campaign_id]["ad_sets"][ad_set_id]["revenue"] + float(row[10])


	# Convert the nested structure to a list of dates with campaigns
	campaign_list = list(ggdata.values())
	for date_entry in campaign_list:
		date_entry["ad_sets"] = list(date_entry["ad_sets"].values())

	ggadsdata["campaign"] = campaign_list
	# Convert to JSON
	# json_data = json.dumps(campaign_list)n
	json_data = ggadsdata


	return jsonify(json_data)



@report_bp.route('/graphsales', methods=['GET', 'OPTIONS'])
@cross_origin(origins='*', methods=['GET'], headers=['Content-Type'])
def get_reportgraphdata():

	headers = request.headers
	body = request.args
	startdate = body.get('startdate')
	enddate = body.get('enddate')
	userid = headers.get('workspaceId')
	timezone = '5.5 hours'
	user = UserRegister.query.filter_by(workspace=userid).first()

	sql_query = db.text("select * from report_graphsales(:workspace, :startdate, :enddate, :timezone)")

	result = db.session.execute(sql_query, {'workspace': userid, 'productid':user.productid, 'startdate':startdate, 'enddate':enddate, 'timezone':timezone})
	data = result.fetchall()

	sale_data = {}
	for row in data:
		key = row[0].strftime("%Y-%m-%d")
		sale_data[key] = [{"revenue":float(row[1]), "sales": int(row[2])}]

	return jsonify(sale_data)