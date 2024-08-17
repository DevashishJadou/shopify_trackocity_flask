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

	sql_query = db.text("select * from table_facebookcreative(:workspace, :productid, :startdate, :enddate, :sort)")

	result = db.session.execute(sql_query, {'workspace': userid, 'productid':user.productid, 'startdate':startdate, 'enddate':enddate, 'sort':'desc'})
	data = result.fetchall()

	crdata = {"creative": [], "clicks": 0, "impression": 0, "revenue": 0, "sales":0, "spend":0, "engagement":0, "roas":0, "cpa":0, "aov":0, "cpc":0, "cpm":0}
	for row in data:
		creativeid = row[0];       creativename = row[1];   adtype = row[2]
		thumbnail = row[3];        facebookfeed = row[4];   preview = row[5]
		spend = float(row[7]);  	orders = int(row[8]);   rev = float(row[9])
		impression = int(row[10]);  click = int(row[11]);	engagement = int(row[12])
		vv3s = int(row[13]); 	   p25 = int(row[14]);		p50 = int(row[15])
		p100 = int(row[16]);	   sec30 = int(row[17]);	thruplay = int(row[18])
		adcount = int(row[19]);    creation_at = row[6]

		if adtype == 'SHARE' and vv3s>0:
			adtype = 'VIDEO'

		roas = round(rev / max(spend,1), 2)
		cpa = round(spend / max(orders,1), 2)
		aov = round(rev / max(orders,1), 2)
		cpc = round(spend / max(click, 1))
		cpm = round(spend*1000/ max(impression,1)) 
		ctr = round(click / max(impression, 1),2)
		hookrate = round(vv3s / max(engagement, 1),2)
		holdrate = round(thruplay / max(vv3s, 1),2)
		engage_rate = round(engagement*100 / max(impression, 1),2)
		completion_rate = round(p100 / max(vv3s, 1),2)
		cr = round(orders*100 / max(click, 1),2)

		creative_data = {
        "creativeid": creativeid, "creativename": creativename, "adtype": adtype,
        "thumbnail": thumbnail, "facebookfeed": facebookfeed, "preview": preview,
        "spend": spend, "orders": orders, "revenue": rev, "impression": impression,
        "click": click, "engagement": engagement, "vv3s": vv3s, "p25": p25,
        "p50": p50, "p100": p100, "sec30": sec30, "thruplay": thruplay, "adcount": adcount,
        "roas": roas, "cpa": cpa, "aov": aov, "cpc": cpc, "cpm": cpm, "ctr": ctr,
		"hookrate": hookrate, "holdrate": holdrate, "engage_rate":engage_rate, 
		"completion_rate":completion_rate, "cr":cr, "creation_at":creation_at
    }

		crdata["creative"].append(creative_data)
		crdata["clicks"] += click
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
	crdata["cpc"] = round(crdata["spend"] / max(crdata["clicks"], 1),2)
	crdata["cpm"] = round(crdata["spend"]*1000 / max(crdata["impression"], 1),2)
	crdata["ctr"] = round(crdata["clicks"]*100 / max(crdata["impression"], 1),2)
	crdata["cr"] = round(crdata["sales"]*100 / max(crdata["clicks"], 1),2)

	return jsonify(crdata), 200


