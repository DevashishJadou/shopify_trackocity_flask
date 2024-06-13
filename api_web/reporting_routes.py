# reporting_routes

from ..db_model.sql_models import UserRegister, order_table_dynamic, ClientFacebookredentials, ClientGoogleCredentials
from ..db_model.mongo_models import CustomerInfo
from ..connection import db, db_mongo

from flask import Blueprint, request, jsonify
from .schema import FB
from flask_cors import cross_origin
import json

from datetime import datetime, timedelta

report_bp = Blueprint('reporting', __name__)


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
	user = UserRegister.query.filter_by(workspace=userid).first()

	if user:
		sort = 'ASC' if attribute == 'first' else 'DESC'
		sql_query = db.text("select * from table_facebookattribute(:workspace, :productid, :startdate, :enddate, :sort)")
		result = db.session.execute(sql_query, {'workspace': userid, 'productid':user.productid, 'startdate':startdate, 'enddate':enddate, 'sort':sort})
		data = result.fetchall()

		fbdata = {}
		fbadsdata = {"impression":0, "clicks":0, "spend":0.0, "sales":0, "revenue":0.0, "cancelorder":0, "cancelrev":0.0}
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
					"revenue" : 0.0,
					"cancelorder": 0,
					"cancelrev": 0.0
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
					"revenue" : 0.0,
					"cancelorder": 0,
					"cancelrev": 0.0
				}

			fbdata[campaign_id]["ad_sets"][ad_set_id]["ads"].append({
				"ad_id": ad_id,
				"ad_name": row[5],
				"impressions": row[6],
				"clicks": row[7],
				"spend": float(row[8]),
				"sales": int(row[9]),
				"revenue": float(row[10]),
				"cancelorder": int(row[11]),
				"cancelrev": float(row[12])
			})

			fbadsdata["impression"] = fbadsdata["impression"] + row[6]
			fbadsdata["clicks"] = fbadsdata["clicks"] + row[7]
			fbadsdata["spend"] = fbadsdata["spend"] + float(row[8])
			fbadsdata["sales"] = fbadsdata["sales"] + int(row[9])
			fbadsdata["revenue"] = fbadsdata["revenue"] + float(row[10])
			fbadsdata["cancelorder"] = fbadsdata["cancelorder"] + int(row[11])
			fbadsdata["cancelrev"] = fbadsdata["cancelrev"] + float(row[12])
			
			fbdata[campaign_id]["impression"] = fbdata[campaign_id]["impression"] + row[6]
			fbdata[campaign_id]["clicks"] = fbdata[campaign_id]["clicks"] + row[7]
			fbdata[campaign_id]["spend"] = fbdata[campaign_id]["spend"] + float(row[8])
			fbdata[campaign_id]["sales"] = fbdata[campaign_id]["sales"] + int(row[9])
			fbdata[campaign_id]["revenue"] = fbdata[campaign_id]["revenue"] + float(row[10])
			fbdata[campaign_id]["cancelorder"] = fbdata[campaign_id]["cancelorder"] + int(row[11])
			fbdata[campaign_id]["cancelrev"] = fbdata[campaign_id]["cancelrev"] + float(row[12])

			fbdata[campaign_id]["ad_sets"][ad_set_id]["impression"] = fbdata[campaign_id]["ad_sets"][ad_set_id]["impression"] + row[6]
			fbdata[campaign_id]["ad_sets"][ad_set_id]["clicks"] = fbdata[campaign_id]["ad_sets"][ad_set_id]["clicks"] + row[7]
			fbdata[campaign_id]["ad_sets"][ad_set_id]["spend"] = fbdata[campaign_id]["ad_sets"][ad_set_id]["spend"] + float(row[8])
			fbdata[campaign_id]["ad_sets"][ad_set_id]["sales"] = fbdata[campaign_id]["ad_sets"][ad_set_id]["sales"] + int(row[9])
			fbdata[campaign_id]["ad_sets"][ad_set_id]["revenue"] = fbdata[campaign_id]["ad_sets"][ad_set_id]["revenue"] + float(row[10])
			fbdata[campaign_id]["ad_sets"][ad_set_id]["cancelorder"] = fbdata[campaign_id]["ad_sets"][ad_set_id]["cancelorder"] + int(row[10])
			fbdata[campaign_id]["ad_sets"][ad_set_id]["cancelrev"] = fbdata[campaign_id]["ad_sets"][ad_set_id]["cancelrev"] + float(row[12])


		# Convert the nested structure to a list of dates with campaigns
		campaign_list = list(fbdata.values())
		for date_entry in campaign_list:
			date_entry["ad_sets"] = list(date_entry["ad_sets"].values())

		fbadsdata["campaign"] = campaign_list
		# Convert to JSON
		# json_data = json.dumps(campaign_list)n
		json_data = fbadsdata


		return jsonify(json_data)
	else:
		return jsonify({"msg":"No Data Found"}), 404



@report_bp.route('/ggtable', methods=['GET', 'OPTIONS'])
@cross_origin(origins='*', methods=['GET'], headers=['Content-Type'])
def get_reporttabledatagoogle():

	headers = request.headers
	body = request.args
	startdate = body.get('startdate')
	enddate = body.get('enddate')
	attribute = body.get('attribute')
	userid = headers.get('workspaceId')
	
	user = UserRegister.query.filter_by(workspace=userid).first()

	if user:
		sort = 'ASC' if attribute == 'first' else 'DESC'
		sql_query = db.text("select * from table_googleattribute(:workspace, :productid, :startdate, :enddate, :sort)")
		result = db.session.execute(sql_query, {'workspace': userid, 'productid':user.productid, 'startdate':startdate, 'enddate':enddate, 'sort':sort})
		data = result.fetchall()

		ggdata = {}
		ggadsdata = {"impression":0, "clicks":0, "spend":0.0, "sales":0, "revenue":0.0, "cancelorder":0, "cancelrev":0.0}
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
					"revenue" : 0.0,
					"cancelorder": 0,
					"cancelrev": 0.0
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
					"revenue" : 0.0,
					"cancelorder": 0,
					"cancelrev": 0.0
				}

			ggdata[campaign_id]["ad_sets"][ad_set_id]["ads"].append({
				"ad_id": ad_id,
				"ad_name": row[5],
				"impressions": row[6],
				"clicks": row[7],
				"spend": float(row[8]),
				"sales": int(row[9]),
				"revenue": float(row[10]),
				"cancelorder": int(row[11]),
				"cancelrev": float(row[12])
			})

			ggadsdata["impression"] = ggadsdata["impression"] + row[6]
			ggadsdata["clicks"] = ggadsdata["clicks"] + row[7]
			ggadsdata["spend"] = ggadsdata["spend"] + float(row[8])
			ggadsdata["sales"] = ggadsdata["sales"] + int(row[9])
			ggadsdata["revenue"] = ggadsdata["revenue"] + float(row[10])
			ggadsdata["cancelorder"] = ggadsdata["cancelorder"] + int(row[11])
			ggadsdata["cancelrev"] = ggadsdata["cancelrev"] + float(row[12])
			
			ggdata[campaign_id]["impression"] = ggdata[campaign_id]["impression"] + row[6]
			ggdata[campaign_id]["clicks"] = ggdata[campaign_id]["clicks"] + row[7]
			ggdata[campaign_id]["spend"] = ggdata[campaign_id]["spend"] + float(row[8])
			ggdata[campaign_id]["sales"] = ggdata[campaign_id]["sales"] + int(row[9])
			ggdata[campaign_id]["revenue"] = ggdata[campaign_id]["revenue"] + float(row[10])
			ggdata[campaign_id]["cancelorder"] = ggdata[campaign_id]["cancelorder"] + int(row[11])
			ggdata[campaign_id]["cancelrev"] = ggdata[campaign_id]["cancelrev"] + float(row[12])

			ggdata[campaign_id]["ad_sets"][ad_set_id]["impression"] = ggdata[campaign_id]["ad_sets"][ad_set_id]["impression"] + row[6]
			ggdata[campaign_id]["ad_sets"][ad_set_id]["clicks"] = ggdata[campaign_id]["ad_sets"][ad_set_id]["clicks"] + row[7]
			ggdata[campaign_id]["ad_sets"][ad_set_id]["spend"] = ggdata[campaign_id]["ad_sets"][ad_set_id]["spend"] + float(row[8])
			ggdata[campaign_id]["ad_sets"][ad_set_id]["sales"] = ggdata[campaign_id]["ad_sets"][ad_set_id]["sales"] + int(row[9])
			ggdata[campaign_id]["ad_sets"][ad_set_id]["revenue"] = ggdata[campaign_id]["ad_sets"][ad_set_id]["revenue"] + float(row[10])
			ggdata[campaign_id]["ad_sets"][ad_set_id]["cancelorder"] = ggdata[campaign_id]["ad_sets"][ad_set_id]["cancelorder"] + int(row[10])
			ggdata[campaign_id]["ad_sets"][ad_set_id]["cancelrev"] = ggdata[campaign_id]["ad_sets"][ad_set_id]["cancelrev"] + float(row[12])

		# Convert the nested structure to a list of dates with campaigns
		campaign_list = list(ggdata.values())
		for date_entry in campaign_list:
			date_entry["ad_sets"] = list(date_entry["ad_sets"].values())

		ggadsdata["campaign"] = campaign_list
		# Convert to JSON
		# json_data = json.dumps(campaign_list)n
		json_data = ggadsdata


		return jsonify(json_data)
	else:
		return jsonify({"msg":"No Data Found"}), 404



@report_bp.route('/graphsales', methods=['GET', 'OPTIONS'])
@cross_origin(origins='*', methods=['GET'], headers=['Content-Type'])
def get_reportgraphdata():

	headers = request.headers
	body = request.args
	startdate = body.get('startdate')
	enddate = body.get('enddate')
	userid = headers.get('workspaceId')
	
	user = UserRegister.query.filter_by(workspace=userid).first()

	sql_query = db.text("select * from report_graphsales(:workspace, :startdate, :enddate)")

	result = db.session.execute(sql_query, {'workspace': userid, 'productid':user.productid, 'startdate':startdate, 'enddate':enddate})
	data = result.fetchall()

	sale_data = {'revenue':0.0, 'sales':0, 'data':{}}
	for row in data:
		key = row[0].strftime("%Y-%m-%d")
		sale_data['data'][key] = [{"revenue":float(row[1]), "sales": int(row[2])}]
		sale_data['revenue'] = sale_data['revenue'] + float(row[1])
		sale_data['sales'] = sale_data['sales'] + int(row[2])

	return jsonify(sale_data), 200



@report_bp.route('/tablesaledata', methods=['GET', 'OPTIONS'])
@cross_origin(origins='*', methods=['GET'], headers=['Content-Type'])
def get_reporttablesaledata():

	headers = request.headers
	body = request.args
	startdate = body.get('startdate')
	enddate = body.get('enddate')
	userid = headers.get('workspaceId')
	adid = body.get('adid')
	channel = body.get('channel')
	attribute = body.get('attribute')
	user = UserRegister.query.filter_by(workspace=userid).first()

	output = []
	if user:
		sort = 'ASC' if attribute == 'first' else 'DESC'
		sql_query = db.text("select * from table_salesdata(:workspace, :productid, :startdate, :enddate, :channel, :adid, :sort)")

		result = db.session.execute(sql_query, {'workspace': userid, 'productid':user.productid, 'startdate':startdate, 'enddate':enddate, 'channel':channel, 'adid':adid, 'sort':sort})
		data = result.fetchall()

		for row in data:
			element = {}
			element['complete_name'] = row[0]
			element['email_phone'] = row[1]
			element['total'] = float(row[2])
			element['order_date'] = row[3].strftime("%Y-%m-%d %H:%M:%S")
			output.append(element)
		
	return jsonify(output), 200



@report_bp.route('/dashboardgraphsales', methods=['GET', 'OPTIONS'])
@cross_origin(origins='*', methods=['GET'], headers=['Content-Type'])
def get_dashboardgraphdata():

	headers = request.headers
	body = request.args
	startdate = body.get('startdate')
	enddate = body.get('enddate')
	userid = headers.get('workspaceId')
	user = UserRegister.query.filter_by(workspace=userid).first()

	sql_query = db.text("select * from dashboard_graphsales(:workspace, :startdate, :enddate)")

	result = db.session.execute(sql_query, {'workspace': userid, 'productid':user.productid, 'startdate':startdate, 'enddate':enddate})
	data = result.fetchall()

	sale_data = {'revenue':{"data":[], "total":0.0}, 'sales':{"data":[],"total":0.0}, 'spend':{"data":[],"total":0.0}, 'roi':{"data":[],"total":0.0}, 'aov':{"data":[],"total":0.0}, 'cpa':{"data":[],"total":0.0}}
	for row in data:
		date_str = row[0].strftime("%Y-%m-%d")
		revenue = round(float(row[1]),2)
		sales = int(row[2])
		spend = round(float(row[3]), 2)
		roi = round(float(row[4]), 2)
		aov = round(float(row[5]), 2)
		cpa = round(float(row[6]), 2)

		sale_data["revenue"]["data"].append({"value": revenue, "date": date_str})
		sale_data["sales"]["data"].append({"value": sales, "date": date_str})
		sale_data["spend"]["data"].append({"value": spend, "date": date_str})
		sale_data["roi"]["data"].append({"value": roi, "date": date_str})
		sale_data["aov"]["data"].append({"value": aov, "date": date_str})
		sale_data["cpa"]["data"].append({"value": cpa, "date": date_str})

		sale_data["revenue"]['total'] += revenue
		sale_data["sales"]['total'] += sales
		sale_data["spend"]['total'] += spend

	sale_data["roi"]['total'] = round(sale_data["revenue"]['total']/max(sale_data["spend"]['total'],1),2)
	sale_data["aov"]['total'] = round(sale_data["revenue"]['total']/max(sale_data["sales"]['total'],1), 2)
	sale_data["cpa"]['total'] = round(sale_data["spend"]['total']/max(sale_data["sales"]['total'],1), 2)
	sale_data["spend"]['total'] = round(sale_data["spend"]['total'], 2)

	return jsonify(sale_data), 200


def channel_matrix(userid, productid, startdate, enddate, fbflag, ggflag):
	sort = 'DESC'
	metric={}
	fbadsdata = {"impression":0, "clicks":0, "spend":0.0, "sales":0, "revenue":0.0, "aov":0.0, "cpa":0.0, "roi":0.0, "profit":0.0, "cpc":0.0}
	if fbflag:
		sql_query_fb = db.text("select * from table_facebookattribute(:workspace, :productid, :startdate, :enddate, :sort)")
		result = db.session.execute(sql_query_fb, {'workspace': userid, 'productid':productid, 'startdate':startdate, 'enddate':enddate, 'sort':sort})
		data = result.fetchall()

		for row in data:
			fbadsdata["impression"] = fbadsdata["impression"] + int(row[6])
			fbadsdata["clicks"] = fbadsdata["clicks"] + int(row[7])
			fbadsdata["spend"] = fbadsdata["spend"] + float(row[8])
			fbadsdata["sales"] = fbadsdata["sales"] + int(row[9])
			fbadsdata["revenue"] = fbadsdata["revenue"] + float(row[10])
		fbadsdata["revenue"] = round(fbadsdata["revenue"],0)
		fbadsdata["spend"] = round(fbadsdata["spend"],0)
		fbadsdata["aov"] = round(fbadsdata["revenue"]/max(fbadsdata["sales"],1),2)
		fbadsdata["cpa"] = round(fbadsdata["spend"]/max(fbadsdata["sales"],1),2)
		fbadsdata["roi"] = round(fbadsdata["revenue"]/max(fbadsdata["spend"],1),2)
		fbadsdata["profit"] = round(fbadsdata["revenue"] - fbadsdata["spend"],0)
		fbadsdata["cpc"] = round(fbadsdata["spend"]/max(fbadsdata["clicks"],1),2)
		fbadsdata["cpm"] = round(fbadsdata["spend"]*1000/max(fbadsdata["impression"],1),2)
	metric['meta'] = fbadsdata

	ggdsdata = {"impression":0, "clicks":0, "spend":0.0, "sales":0, "revenue":0.0, "aov":0.0, "cpa":0.0, "roi":0.0, "profit":0.0, "cpc":0.0}
	if ggflag:
		sql_query_fb = db.text("select * from table_googleattribute(:workspace, :productid, :startdate, :enddate, :sort)")
		result = db.session.execute(sql_query_fb, {'workspace': userid, 'productid':productid, 'startdate':startdate, 'enddate':enddate, 'sort':sort})
		data = result.fetchall()

		for row in data:
			ggdsdata["impression"] = ggdsdata["impression"] + int(row[6])
			ggdsdata["clicks"] = ggdsdata["clicks"] + int(row[7])
			ggdsdata["spend"] = ggdsdata["spend"] + float(row[8])
			ggdsdata["sales"] = ggdsdata["sales"] + int(row[9])
			ggdsdata["revenue"] = ggdsdata["revenue"] + float(row[10])
		ggdsdata["revenue"] = round(ggdsdata["revenue"],0)
		ggdsdata["spend"] = round(ggdsdata["spend"],0)
		ggdsdata["aov"] = round(ggdsdata["revenue"]/max(ggdsdata["sales"],1),2)
		ggdsdata["cpa"] = round(ggdsdata["spend"]/max(ggdsdata["sales"],1),2)
		ggdsdata["roi"] = round(ggdsdata["revenue"]/max(ggdsdata["spend"],1),2)
		ggdsdata["profit"] = round(ggdsdata["revenue"] - ggdsdata["spend"],0)
		ggdsdata["cpc"] = round(ggdsdata["spend"]/max(ggdsdata["clicks"],1),2)
		ggdsdata["cpm"] = round(ggdsdata["spend"]*1000/max(ggdsdata["impression"],1),2)
	metric['google'] = ggdsdata

	adspend = {"impression":0, "clicks":0, "spend":0.0, "sales":0, "revenue":0.0, "aov":0.0, "cpa":0.0, "roi":0.0, "profit":0.0, "cpc":0.0}
	adspend['impression'] = fbadsdata["impression"] + ggdsdata["impression"]
	adspend['clicks'] = fbadsdata["clicks"] + ggdsdata["clicks"]
	adspend['spend'] = fbadsdata["spend"] + ggdsdata["spend"]
	adspend['cpm'] = adspend['spend']*1000/max((fbadsdata["impression"] + ggdsdata["impression"]),1)
	adspend['sales'] = fbadsdata["sales"] + ggdsdata["sales"]
	adspend['revenue'] = fbadsdata["revenue"] + ggdsdata["revenue"]
	adspend['aov'] = adspend['revenue'] / max(adspend['sales'], 1)
	adspend['cpa'] = adspend['spend'] / max(adspend['sales'], 1)
	adspend['roi'] = adspend['revenue'] / max(adspend['spend'], 1)
	adspend['profit'] = fbadsdata["profit"] + ggdsdata["profit"]
	adspend['cpc'] = adspend['spend'] / max(adspend['clicks'], 1)
	metric['adspend'] = adspend
	

	return metric


@report_bp.route('/dashboardmetric', methods=['GET', 'OPTIONS'])
@cross_origin(origins='*', methods=['GET'], headers=['Content-Type'])
def get_dashboardmetric():
	headers = request.headers
	_body = request.args
	startdate = _body.get('startdate')
	enddate = _body.get('enddate')
	userid = headers.get('workspaceId')
	user = UserRegister.query.filter_by(workspace=userid).first()

	fbflag = False
	ggflag = False
	fb = ClientFacebookredentials.query.filter_by(workspace=userid).first()
	if fb:
		fbflag = True
	gg = ClientGoogleCredentials.query.filter_by(workspace=userid).first()
	if gg:
		ggflag = True

	result = channel_matrix(userid, user.productid, startdate, enddate, fbflag, ggflag)

	return jsonify(result),200



@report_bp.route('/dashboardtraffic', methods=['GET', 'OPTIONS'])
@cross_origin(origins='*', methods=['GET'], headers=['Content-Type'])
def get_dashboardtraffic():
	headers = request.headers
	_body = request.args
	startdate = datetime.strptime(_body.get('startdate'), "%Y-%m-%d")
	enddate = datetime.strptime(_body.get('enddate'), "%Y-%m-%d") + timedelta(days=1)
	userid = headers.get('workspaceId')
	user = UserRegister.query.filter_by(workspace=userid).first()

	data={}

	page_view = CustomerInfo.objects(
		**{"body__pageLoad": 1},
		productid=float(user.productid),
		creation_at__gte=startdate,
   		creation_at__lte=enddate
	).count()
	data['page_view'] = int(page_view*1.03)

	
	localsess_pipeline = [
    {'$match': {
        'productid': float(user.productid),
        'creation_at': {'$gte': startdate, '$lte': enddate}
    }},
    {'$group': {
        '_id': '$localsession'
    }},
    {'$count': 'distinct_localsession_count'}
	]
	usr = list(CustomerInfo.objects.aggregate(*localsess_pipeline))
	try:
		data['user'] = usr[0]['distinct_localsession_count']
	except:
		data['user'] = 0


	sess_pipeline = [
    {'$match': {
        'productid': float(user.productid),
        'creation_at': {'$gte': startdate, '$lte': enddate},
        'body.customerInfo': {}
    }},
    {'$group': {
        '_id': '$session'  # Group by 'localsession' to get distinct values
    }},
    {'$count': 'distinct_session_count'}  # Counts the number of distinct groups
	]
	unique_usr = list(CustomerInfo.objects.aggregate(*sess_pipeline))
	try:
		data['unique_user'] = unique_usr[0]['distinct_session_count']
	except:
		data['unique_user'] = 0

	if user.product_type == 'growth':
		bounce_pipeline = [
			{
				'$match': {
					'productid': float(user.productid),
					'creation_at': {'$gte': startdate, '$lte': enddate}
				}
			},
			{
				'$group': {
					'_id': '$localsession',
					'count': {'$sum': 1}  # Count occurrences of each localsession
				}
			},
			{
				'$match': {
					'count': 1  # Filter to keep only those groups where count is exactly 1
				}
			},
			{
				'$count': 'unique_localsession_count'
			}
		]

		session = data['user'] if data['user'] !=0 else 1
		try:
			bounce = list(CustomerInfo.objects.aggregate(*bounce_pipeline))
			data['bounce_rate'] = round(bounce[0]['unique_localsession_count']*100/session,2)
		except:
			data['bounce_rate'] = 0.0

		data['page_view_per_session'] = round(data['page_view']/session, 2)

	
	tablename = 'order_' + userid
	orderTable = order_table_dynamic(tablename)
	db.Model.metadata.reflect(db.engine)
	conversion = orderTable.query.filter(
        orderTable.order_date >= startdate,
        orderTable.order_date <= enddate
    ).count()
	if data['user'] == 0:
		data['cr'] = 0.0
	else:
		data['cr'] = round(conversion*100.0/data['user'],2)


	return jsonify(data), 200




