from ..db_model.sql_models import UserRegister, order_table_dynamic, ClientFacebookredentials, ClientGoogleCredentials, MongoMetric
from ..db_model.mongo_models import CustomerInfo
from ..connection import db

from flask import Blueprint, request, jsonify
from .schema import FB
from flask_cors import cross_origin
import json

from datetime import datetime, timedelta
from collections import defaultdict

creative_bp = Blueprint('creative', __name__)


@creative_bp.route('/creativetabledata', methods=['GET', 'OPTIONS'])
@cross_origin(origins='*', methods=['GET'], headers=['Content-Type'])
def get_dashboardgraphdata():

	headers = request.headers
	body = request.args
	startdate = body.get('startdate')
	enddate = body.get('enddate')
	userid = headers.get('workspaceId')
	user = UserRegister.query.filter_by(workspace=userid).first()

	sql_query = db.text("select * from creative_table(:workspace, :productid, :startdate, :enddate, :sort)")

	result = db.session.execute(sql_query, {'workspace': userid, 'productid':user.productid, 'startdate':startdate, 'enddate':enddate, 'sort':'desc'})
	data = result.fetchall()

	crdata = {"creative": [], "click": 0, "impression": 0, "revenue": 0, "sales":0, "spend":0, "engagement":0, "roas":0, "cpa":0, "aov":0, "cpc":0, "cpm":0}
	for row in data:
		creativeid = row[0];       thumbnail_id = row[1]; creativename = row[2]
		status = row[3]	;	       adtype = row[4];         thumbnail = row[5]
		facebookfeed = row[6];     	preview = row[7];      creation_at = row[8]     
		spend = float(row[9]);  	orders = int(row[10]);   rev = float(row[11])
		impression = int(row[12]);  click = int(row[13]);	engagement = int(row[14])
		vv3s = int(row[15]); 	   p25 = int(row[16]);		p50 = int(row[17])
		p100 = int(row[18]);	   sec30 = int(row[19]);	thruplay = int(row[20])
		videolength = float(row[21]);    adcount = int(row[22]);    

		if adtype == 'SHARE' and vv3s>0:
			adtype = 'VIDEO'

		roas = round(rev / max(spend,1), 2)
		cpa = round(spend / max(orders,1), 2)
		aov = round(rev / max(orders,1), 2)
		cpc = round(spend / max(click, 1))
		cpm = round(spend*1000/ max(impression,1)) 
		ctr = round(click*100 / max(impression, 1),2)
		hookrate = round(vv3s*100 / max(engagement, 1),2)
		holdrate = round(thruplay*100 / max(vv3s, 1),2)
		engage_rate = round(engagement*100 / max(impression, 1),2)
		completion_rate = round(p100 / max(vv3s, 1),2)
		cr = round(orders*100 / max(click, 1),2)
		cpnv = round(spend / max(engagement, 1),2)

		creative_data = {
        "creativeid": creativeid, "thumbnail_id": thumbnail_id, "creativename": creativename, 
		"status": status, "adtype": adtype,
        "thumbnail": thumbnail, "facebookfeed": facebookfeed, "preview": preview,
        "spend": spend, "sales": orders, "revenue": rev, "impression": impression,
        "click": click, "engagement": engagement, "vv3s": vv3s, "p25": p25,
        "p50": p50, "p100": p100, "sec30": sec30, "thruplay": thruplay, "videolength":videolength,
		"adcount": adcount, "roas": roas, "cpa": cpa, "aov": aov, "cpc": cpc, "cpm": cpm, "ctr": ctr,
		"hookrate": hookrate, "holdrate": holdrate, "engage_rate":engage_rate, "cpnv": cpnv,
		"completion_rate":completion_rate, "cr":cr, "creation_at":creation_at
    }

		crdata["creative"].append(creative_data)
		crdata["click"] += click
		crdata["impression"] += impression
		crdata["revenue"] += rev
		crdata["sales"] += orders
		crdata["spend"] += spend
		crdata["engagement"] += engagement
	crdata["revenue"] = round(crdata["revenue"])
	crdata["spend"] = round(crdata["spend"])
	crdata["roas"] = round(crdata["revenue"] / max(crdata["spend"], 1), 2)
	crdata["cpa"] = round(crdata["spend"] / max(crdata["sales"], 1))
	crdata["aov"] = round(crdata["revenue"] / max(crdata["sales"], 1))
	crdata["cpc"] = round(crdata["spend"] / max(crdata["click"], 1),2)
	crdata["cpm"] = round(crdata["spend"]*1000 / max(crdata["impression"], 1),2)
	crdata["ctr"] = round(crdata["click"]*100 / max(crdata["impression"], 1),2)
	crdata["cr"] = round(crdata["sales"]*100 / max(crdata["click"], 1),2)
	crdata["cpnv"] = round(crdata["spend"] / max(crdata["engagement"], 1),2)

	return jsonify(crdata), 200



@creative_bp.route('/adtable', methods=['GET', 'OPTIONS'])
@cross_origin(origins='*', methods=['GET'], headers=['Content-Type'])
def get_reporttabledatafacebook():

	headers = request.headers
	body = request.args
	startdate = body.get('startdate')
	enddate = body.get('enddate')
	userid = headers.get('workspaceId')
	creativeid = body.get('creativeId')
	user = UserRegister.query.filter_by(workspace=userid).first()

	if user:
		sort = 'DESC'
		sql_query = db.text("select * from creative_facebookads(:workspace, :productid, :creativeid, :startdate, :enddate, :sort)")
		result = db.session.execute(sql_query, {'workspace': userid, 'productid':user.productid, 'creativeid':creativeid, 'startdate':startdate, 'enddate':enddate, 'sort':sort})
		data = result.fetchall()

		fbdata = {"ads":[]}
		fbadsdata = {"impression":0, "click":0, "spend":0.0, "sales":0, "revenue":0.0, "cancelorder":0, "cancelrev":0.0}
		for row in data:
			ad_id = row[0]

			fbdata["ads"].append({
				"ad_id": ad_id,
				"ad_name": row[1],
				"impression": row[2],
				"click": row[3],
				"spend": float(row[4]),
				"sales": int(row[5]),
				"revenue": float(row[6]),
				"cancelorder": int(row[7]),
				"cancelrev": float(row[8])
			})

			fbadsdata["impression"] = fbadsdata["impression"] + row[2]
			fbadsdata["click"] = fbadsdata["click"] + row[3]
			fbadsdata["spend"] = fbadsdata["spend"] + float(row[4])
			fbadsdata["sales"] = fbadsdata["sales"] + int(row[5])
			fbadsdata["revenue"] = fbadsdata["revenue"] + float(row[6])
			fbadsdata["cancelorder"] = fbadsdata["cancelorder"] + int(row[7])
			fbadsdata["cancelrev"] = fbadsdata["cancelrev"] + float(row[8])

		fbadsdata["ads"] = fbdata["ads"]

		# Convert to JSON
		json_data = fbadsdata


		return jsonify(json_data)
	else:
		return jsonify({"msg":"No Data Found"}), 404
