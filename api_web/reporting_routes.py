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
				"ad_sets": {}
			}

		if ad_set_id not in fbdata[date]["campaigns"][campaign_id]["ad_sets"]:
			fbdata[date]["campaigns"][campaign_id]["ad_sets"][ad_set_id] = {
				"ad_set_id": ad_set_id,
				"ad_set_name": row[4],
				"ads": []
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

	# Convert the nested structure to a list of dates with campaigns
	date_list = list(fbdata.values())
	for date_entry in date_list:
		date_entry["campaigns"] = list(date_entry["campaigns"].values())
		for campaign in date_entry["campaigns"]:
			campaign["ad_sets"] = list(campaign["ad_sets"].values())

	# Convert to JSON
	json_data = json.dumps(date_list, indent=4)


	# Transform the result into the desired JSON format
	# data_json = {}
	# for row in data:
	# 	import pdb
	# 	pdb.set_trace()
	# 	dated = row[0]
	# 	if dated not in data_json:
	# 		campaign = row[1]
	# 		data_json[dated] = {
	# 			'campaign': campaign,
	# 			'adset': []
	# 		}
	# 	if campaign in data_json[dated]:
	# 		adset = row[2]           
	# 		data_json[dated][campaign] = {
	# 			'adset': adset,
	# 			'ad': [],					
	# 		}
	# 	if adset not in data_json[dated][campaign]:
	# 		ad = row[3]           
	# 		data_json[dated][campaign][adset] = {
	# 			'ad': ad,					
	# 		}
	# 	if ad in data_json[dated][campaign][adset][ad]:
	# 		data_json[dated][campaign][adset][ad] = {
	# 			'impression': row[4],
	# 			'clicks': row[5],
	# 			'order': row[6],
	# 			'total': row[7]
	# 		}


	return jsonify(json_data)
