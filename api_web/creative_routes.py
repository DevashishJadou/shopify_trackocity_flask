from ..db_model.sql_models import UserRegister
from ..connection import db

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin


creative_bp = Blueprint('creative', __name__)

@creative_bp.route('/creativetabledata/facebook', methods=['GET', 'OPTIONS'])
@cross_origin(origins='*', methods=['GET'], headers=['Content-Type'])
def get_creativetabledatafacebook():

	headers = request.headers
	body = request.args
	startdate = body.get('startdate')
	enddate = body.get('enddate')
	userid = headers.get('workspaceId')
	campaign = body.get('campaign')

	if campaign == 'Null' or campaign is None:
		campaign = None
	else:
		campaign = campaign.lower()
	adset = body.get('adset')
	if adset == 'Null' or adset is None:
		adset = None
	else:
		adset = adset.lower()
	ad = body.get('ad')
	if ad == 'Null' or ad is None:
		ad = None
	else:
		ad = ad.lower()
	
	user = UserRegister.query.filter_by(workspace=userid).first()

	sql_query = db.text("select * from creative_table(:workspace, :productid, :startdate, :enddate, :sort, :campaign, :adset, :ad)")

	result = db.session.execute(sql_query, {'workspace': userid, 'productid':user.productid, 'startdate':startdate, 'enddate':enddate, 'sort':'desc', 'campaign':campaign, 'adset':adset, 'ad':ad})
	data = result.fetchall()

	crdata = {"creative": [], "click": 0, "impression": 0, "revenue":0, "spend":0, "sales":0, "leads":0, "engagement":0, "roas":0, "cpa":0, "aov":0, "cpc":0, "cpm":0, "cpl":0}
	for row in data:
		creativeid = row[0];       thumbnail_id = row[1]; creativename = row[2]
		status = row[3]	;	       adtype = row[4];         thumbnail = row[5]
		facebookfeed = row[6];     	preview = row[7];      creation_at = row[8]     
		spend = float(row[9]);  	orders = int(row[10]);   rev = float(row[11])
		impression = int(row[12]);  click = int(row[13]);	engagement = int(row[14])
		vv3s = int(row[15]); 	   p25 = int(row[16]);		p50 = int(row[17])
		p100 = int(row[18]);	   sec30 = int(row[19]);	thruplay = int(row[20])
		videolength = round(float(row[21]),2);    adcount = int(row[22]); 
		lead = int(row[23]);  

		if adtype == 'SHARE' and vv3s>0:
			adtype = 'VIDEO'

		roas = 0 if spend == 0 else round(rev / max(spend,1), 2)
		cpa = 0 if orders == 0 else round(spend / max(orders,1), 2)
		aov =  round(rev / max(orders,1), 2)
		cpc = 0 if click == 0 else round(spend / max(click, 1))
		cpm = round(spend*1000/ max(impression,1)) 
		ctr = round(click*100 / max(impression, 1),2)
		hookrate = round(vv3s*100 / max(impression, 1),2)
		holdrate = 0 if vv3s == 0 else round(thruplay*100 / max(vv3s, 1),2)
		engage_rate = round(engagement*100 / max(impression, 1),2)
		completion_rate = 0 if vv3s == 0 else round(p100 / max(vv3s, 1),2)
		cr = 0 if click == 0 else  round(orders*100 / max(click, 1),2)
		cpnv = 0 if engagement == 0 else  round(spend / max(engagement, 1),2)
		cpl = 0 if lead == 0 else round(spend / max(lead, 1),2)

		creative_data = {
        "creativeid": creativeid, "thumbnail_id": thumbnail_id, "creativename": creativename, 
		"status": status, "adtype": adtype,
        "thumbnail": thumbnail, "facebookfeed": facebookfeed, "preview": preview,
        "spend": spend, "sales": orders, "leads":lead, "revenue": rev, "impression": impression,
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
		crdata["leads"] += lead
	crdata["revenue"] = round(crdata["revenue"])
	crdata["spend"] = round(crdata["spend"])
	crdata["roas"] = 0 if crdata["spend"] == 0 else round(crdata["revenue"] / max(crdata["spend"], 1), 2)
	crdata["cpa"] = 0 if crdata["sales"] == 0 else round(crdata["spend"] / max(crdata["sales"], 1))
	crdata["aov"] = round(crdata["revenue"] / max(crdata["sales"], 1))
	crdata["cpc"] = 0 if crdata["click"] == 0 else round(crdata["spend"] / max(crdata["click"], 1),2)
	crdata["cpl"] = 0 if crdata["leads"] == 0 else round(crdata["spend"] / max(crdata["leads"], 1))
	crdata["cpm"] = round(crdata["spend"]*1000 / max(crdata["impression"], 1),2)
	crdata["ctr"] = round(crdata["click"]*100 / max(crdata["impression"], 1),2)
	crdata["cr"] = 0 if crdata["click"] == 0 else round(crdata["sales"]*100 / max(crdata["click"], 1),2)
	crdata["cpnv"] = 0 if crdata["engagement"] == 0 else round(crdata["spend"] / max(crdata["engagement"], 1),2)

	return jsonify(crdata), 200



@creative_bp.route('/adtable/facebook', methods=['GET', 'OPTIONS'])
@cross_origin(origins='*', methods=['GET'], headers=['Content-Type'])
def get_reporttabledatafacebook():

	headers = request.headers
	body = request.args
	startdate = body.get('startdate')
	enddate = body.get('enddate')
	userid = headers.get('workspaceId')
	creativeid = body.get('creativeId')
	# campaign = body.get('campaign', None)
	# adset = body.get('adset', None)
	# ad = body.get('ad', None)
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



@creative_bp.route('/creativetabledata/youtube', methods=['GET', 'OPTIONS'])
@cross_origin(origins='*', methods=['GET'], headers=['Content-Type'])
def get_creativetabledatayoutube():

	headers = request.headers
	body = request.args
	startdate = body.get('startdate')
	enddate = body.get('enddate')
	userid = headers.get('workspaceId')

	sql_query = db.text("""select workspace, creative_id, creative_name, sum(impression) impression, sum(spend) spend,
					sum(purchase) purchase, sum(purchase_value) purchase_value, sum(engagement) engagement, sum(video_views) video_views,
					sum(video_p25_watched_actions) video_p25_watched_actions, sum(video_p50_watched_actions) video_p50_watched_actions,
					sum(video_p75_watched_actions) video_p75_watched_actions, sum(video_p100_watched_actions) video_p100_watched_actions,
					video_length, ad_type, thumbnail_url, preview  
					from googlecreative
					where workspace = :workspace and dated >= :startdate and dated <= :enddate
					group by 1,2,3,14,15,16,17
					 """)

	result = db.session.execute(sql_query, {'workspace': userid, 'startdate':startdate, 'enddate':enddate})
	data = result.fetchall()

	crdata = {"creative": [], "click": 0, "impression": 0, "sales":0, "spend":0, "engagement":0, "cpc":0, "cpm":0, "cpa":0}
	for row in data:
		creativeid = row[1];         creativename = row[2];        impression = int(row[3])
		spend = float(row[4]);	     sales = float(row[6]);          engagement = row[7]
		video_views = row[8];     	 p25 = row[9];                p50 = row[10]       
		p75 = row[11];               p100 = row[12];               videolength = row[13]
		adtype = row[14];          thumbnail_id = row[15];      preview = row[16]
		click = row[5];            



		cpc = 0 if click == 0 else round(spend / max(click, 1))
		cpm = round(spend*1000/ max(impression,1)) 
		ctr = round(click*100 / max(impression, 1),2)
		cpa = round(float(spend) / max(float(sales), 1),2)
		engage_rate = round(engagement*100 / max(impression, 1),2)
		cpnv = 0 if engagement == 0 else  round(spend / max(engagement, 1),2)
		hookrate = 0 if impression == 0 else round(video_views / impression * 100, 2)
		holdrate = 0 if video_views ==0 else  round(p25* 100/video_views ,2)
		completion_rate = 0 if video_views ==0 else round(p100* 10000/video_views ,2)

		creative_data = {
        "creativeid": creativeid, "thumbnail_id": thumbnail_id, "creativename": creativename, 
		"adtype": "VIDEO", "sales":sales,
        "thumbnail": thumbnail_id, "preview": preview,
        "spend": spend, "impression": impression,
        "click": click, "engagement": engagement, "video_views": video_views, "p25": p25,
        "p50": p50, "p75":p75, "p100": p100,  "videolength":videolength,
		"cpc": cpc, "cpm": cpm, "ctr": ctr, "cpa":cpa,
		"hookrate": hookrate, "holdrate": holdrate, "engage_rate":engage_rate, "cpnv": cpnv,
		"completion_rate":completion_rate
    }

		crdata["creative"].append(creative_data)
		crdata["click"] += click
		crdata["impression"] += impression
		crdata["spend"] += spend
		crdata["sales"] += sales
		crdata["engagement"] += engagement
	crdata["spend"] = round(crdata["spend"])
	crdata["cpc"] = 0 if crdata["click"] == 0 else round(crdata["spend"] / max(crdata["click"], 1),2)
	crdata["cpm"] = round(crdata["spend"]*1000 / max(crdata["impression"], 1),2)
	crdata["ctr"] = round(crdata["click"]*100 / max(crdata["impression"], 1),2)
	crdata["cpnv"] = 0 if crdata["engagement"] == 0 else round(crdata["spend"] / max(crdata["engagement"], 1),2)

	return jsonify(crdata), 200
