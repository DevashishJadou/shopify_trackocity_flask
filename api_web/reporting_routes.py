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
	userid = headers.get('workspaceId')
	user = UserRegister.query.filter_by(workspace=userid).first()

	sql_query = db.text("select * from table_lastattribute(:workspace, :productid)")

	result = db.session.execute(sql_query, {'workspace': userid, 'productid':user.productid})
	data = result.fetchall()

	fbdata = {}
	for row in data:
		date = row[0].strftime("%Y-%m-%d")
		campaign_id = row[1]
		ad_set_id = row[3]
		ad_id = row[5]

		if date not in fbdata:
			fbdata[date] = {"date": date, "campaigns": {}}

		if campaign_id not in fbdata[date]["campaigns"]:
			fbdata[date]["campaigns"][campaign_id] = {
				"campaign_id": campaign_id,
				"campaign_name": row[2],
				"ad_sets": {},
				"impression": 0,
				"clicks": 0,
				"spend" : 0.0,
				"order" : 0,
				"total" : 0.0
			}

		if ad_set_id not in fbdata[date]["campaigns"][campaign_id]["ad_sets"]:
			fbdata[date]["campaigns"][campaign_id]["ad_sets"][ad_set_id] = {
				"ad_set_id": ad_set_id,
				"ad_set_name": row[4],
				"ads": [],
				"impression": 0,
				"clicks": 0,
				"spend" : 0.0,
				"order" : 0,
				"total" : 0.0
			}

		fbdata[date]["campaigns"][campaign_id]["ad_sets"][ad_set_id]["ads"].append({
			"ad_id": ad_id,
			"ad_name": row[6],
			"impressions": row[7],
			"clicks": row[8],
			"spend": float(row[9]),
			"order": row[10],
			"total": float(row[11])
		})
		
		fbdata[date]["campaigns"][campaign_id]["impression"] = fbdata[date]["campaigns"][campaign_id]["impression"] + row[7]
		fbdata[date]["campaigns"][campaign_id]["clicks"] = fbdata[date]["campaigns"][campaign_id]["clicks"] + row[8]
		fbdata[date]["campaigns"][campaign_id]["spend"] = fbdata[date]["campaigns"][campaign_id]["spend"] + float(row[9])
		fbdata[date]["campaigns"][campaign_id]["order"] = fbdata[date]["campaigns"][campaign_id]["order"] + row[10]
		fbdata[date]["campaigns"][campaign_id]["total"] = fbdata[date]["campaigns"][campaign_id]["total"] + float(row[11])

		fbdata[date]["campaigns"][campaign_id]["ad_sets"][ad_set_id]["impression"] = fbdata[date]["campaigns"][campaign_id]["ad_sets"][ad_set_id]["impression"] + row[7]
		fbdata[date]["campaigns"][campaign_id]["ad_sets"][ad_set_id]["clicks"] = fbdata[date]["campaigns"][campaign_id]["ad_sets"][ad_set_id]["clicks"] + row[8]
		fbdata[date]["campaigns"][campaign_id]["ad_sets"][ad_set_id]["spend"] = fbdata[date]["campaigns"][campaign_id]["ad_sets"][ad_set_id]["spend"] + float(row[9])
		fbdata[date]["campaigns"][campaign_id]["ad_sets"][ad_set_id]["order"] = fbdata[date]["campaigns"][campaign_id]["ad_sets"][ad_set_id]["order"] + row[10]
		fbdata[date]["campaigns"][campaign_id]["ad_sets"][ad_set_id]["total"] = fbdata[date]["campaigns"][campaign_id]["ad_sets"][ad_set_id]["total"] + float(row[11])


	# Convert the nested structure to a list of dates with campaigns
	date_list = fbdata
	for date_entry in date_list:
		date_list[date_entry]["campaigns"] = list(date_list[date_entry]["campaigns"].values())
		for campaign in date_list[date_entry]["campaigns"]:
			campaign["ad_sets"] = list(campaign["ad_sets"].values())

	# Convert to JSON
	json_data = json.dumps(date_list)


	return jsonify(json_data)
