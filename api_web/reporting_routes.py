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
def get_data():

	headers = request.headers
	body = json.loads(request.data)
	startdate = body.get('startdate')
	enddate = body.get('enddate')
	userid = headers.get('workspaceId')
	user = UserRegister.query.filter_by(workspace=userid).first()

	sql_query = db.text("select * from table_lastattribute(:workspace, :productid, :startdate, :enddate)")

	result = db.session.execute(sql_query, {'workspace': userid, 'productid':user.productid, 'startdate':startdate, 'enddate':enddate})
	data = result.fetchall()

	fbdata = {}
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
	campaign_list = fbdata
	for date_entry in campaign_list:
		campaign_list[date_entry]['campaign_id'] = campaign_list[date_entry]["campaign_id"]
		campaign_list[date_entry]['campaign_name'] = campaign_list[date_entry]["campaign_name"]
		campaign_list[date_entry]["ad_sets"] = list(campaign_list[date_entry]["ad_sets"].values())


	# Convert to JSON
	# json_data = json.dumps(campaign_list)
	json_data = campaign_list


	return jsonify(json_data)
