# reporting_routes

from ..db_model.sql_models import UserRegister, ClientFacebookredentials, ClientGoogleCredentials, MongoMetric, UTMSource
from ..db_model.mongo_models import CustomerInfo
from ..connection import db

from flask import Blueprint, request, jsonify
from sqlalchemy import text
from .schema import FB
from flask_cors import cross_origin
import json

from datetime import datetime, timedelta
from collections import defaultdict

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


@report_bp.route('/source', methods=['GET', 'OPTIONS'])
@cross_origin(origins='*', methods=['GET'], headers=['Content-Type'])
def get_all_source():
    headers = request.headers
    userid = headers.get('workspaceId')
      
    src = UTMSource.query.filter_by(workspace=userid).all()
    unique_src = {record.displayname for record in src}
    src_list = list(unique_src)

    return jsonify(src_list), 200
      

# Utility function to update metrics
def update_metrics(metrics, row, indexes, traffic):

    if traffic not in ('Facebook', 'Google'):
        metrics["Clicks"] += (int(row[indexes["nvisitor"]]) + int(row[indexes["New Visits"]]))
    else:
        metrics["Clicks"] += row[indexes["Clicks"]]  

    metrics["Impression"] += row[indexes["Impression"]]
    metrics["Spend"] += round(float(row[indexes["Spend"]]),1)
    metrics["Sales"] += int(row[indexes["Sales"]])
    metrics["Revenue"] += round(float(row[indexes["Revenue"]]),1)
    metrics["Profit"] += round((float(row[indexes["Revenue"]]) - float(row[indexes["Spend"]])),1)
    metrics["CancelOrder"] += int(row[indexes["CancelOrder"]])
    metrics["CancelRev"] += float(row[indexes["CancelRev"]])
    metrics["nSales"] += int(row[indexes["nSales"]])
    metrics["nRevenue"] += float(row[indexes["nRevenue"]])
    metrics["New Visits"] += min(int(row[indexes["New Visits"]]), row[indexes["Clicks"]])
    metrics["nvisitor"] += int(row[indexes["nvisitor"]])
    metrics["visitor"] += (int(row[indexes["nvisitor"]]) + int(row[indexes["New Visits"]]))
    metrics["ReportedRev"] += round(float(row[indexes["ReportedRev"]]),2)
    metrics["Cost"] += round(float(row[indexes["Cost"]]),2)

    # Calculate new metrics
    metrics["CPM"] = round(metrics["Spend"] *1000 / max(metrics["Impression"],1), 1)
    metrics["ROAS"] = round(metrics["Revenue"] / max(metrics["Spend"], 1),2)
    metrics["AOV"] = round(metrics["Revenue"] / max(metrics["Sales"], 1),1)
    metrics["CPA"] = 'n/a' if metrics["Sales"] == 0 else round(metrics["Spend"] / metrics["Sales"],1)
    metrics["CPC"] = 'n/a' if metrics["Clicks"] == 0 else round(metrics["Spend"] / metrics["Clicks"],2)
    metrics["CTR %"] = 'n/a' if metrics["Impression"] == 0 else round(metrics["Clicks"]*100 / metrics["Impression"],2)
    metrics["CR %"] = 'n/a' if metrics["Clicks"] == 0 else round(metrics["Sales"]*100 / metrics["Clicks"],2)
	
    metrics["nSpend"] = float(metrics["Clicks"]) * min(metrics["Clicks"], metrics["visitor"]) / max(1, metrics["Clicks"], metrics["visitor"])
    metrics["nROAS"] = 'n/a' if metrics["Spend"] == 0 else round(metrics["nRevenue"] / metrics["Spend"],2)
    metrics["nAOV"] = 'n/a' if metrics["nSales"] == 0 else round(metrics["nRevenue"] / metrics["nSales"],1)
    metrics["nCPA"] = 'n/a' if metrics["nSales"] == 0 else round(metrics["Spend"] / metrics["nSales"],1)
    metrics["nCPC"] = 'n/a' if metrics["visitor"] == 0 else round(metrics["Spend"] / metrics["visitor"],2)
    metrics["nCR %"] = 'n/a' if metrics["visitor"] == 0 else round(metrics["nSales"]*100 / metrics["visitor"],2)
    metrics["New Visits %"] = 'n/a' if metrics["Clicks"] == 0 else round(metrics["New Visits"]*100 / metrics["Clicks"] ,2)
    metrics["eCPNV"] = 'n/a' if metrics["New Visits"] == 0 else round(metrics["Spend"] / metrics["New Visits"] ,1)

    metrics["Gross Margin %"] = 'n/a' if (row[indexes["Revenue"]]) == 0 else round((row[indexes["Revenue"]] - (row[indexes["Spend"]]+row[indexes["Cost"]]))*100 / row[indexes["Revenue"]] ,1)
    metrics["Gross Profit"] = round((row[indexes["Revenue"]] - (row[indexes["Spend"]]+row[indexes["Cost"]])),1)


# Utility function to initialize campaign and ad set
def initialize_campaign_and_ad_set(data, campaign_id, row, ad_set_id):
    if campaign_id not in data:
        data[campaign_id] = {
            "campaign_id": campaign_id,
            "campaign_name": row[1],
            "ad_sets": {},
            "Impression": 0, "Clicks": 0, "Spend": 0.0,
            "Sales": 0, "Revenue": 0.0, "Profit":0.0, "CPM":0, "ROAS": 0.0, "AOV": 0.0,
			"CPC": 0.0, "CPA":0.0, "CTR %":0.0, "CR %":0.0, "CancelOrder": 0,
            "CancelRev": 0.0, "nSales": 0, "nRevenue": 0.0, 
            "New Visits": 0, "nvisitor": 0, "visitor": 0, "nSpend": 0.0,
            "nROAS": 0.0, "nAOV": 0.0, "nCPA": 0.0, "nCPC": 0.0, "nCR %": 0.0, "New Visits %": 0.0,
            "eCPNV": 0.0, "ReportedRev":0.0, "Cost":0.0, "Gross Margin %":0.0, "Gross Profit":0.0
        }
    if ad_set_id not in data[campaign_id]["ad_sets"]:
        data[campaign_id]["ad_sets"][ad_set_id] = {
            "ad_set_id": ad_set_id,
            "ad_set_name": row[3],
            "ads": [],
            "Impression": 0, "Clicks": 0, "Spend": 0.0, "Profit": 0.0,
            "Sales": 0, "Revenue": 0.0, "CPM":0, "ROAS": 0.0, "AOV": 0.0,
			"CPC": 0.0, "CPA":0.0, "CTR %":0.0, "CR %":0.0, "CancelOrder": 0,
            "CancelRev": 0.0, "nSales": 0, "nRevenue": 0.0, 
            "New Visits": 0, "nvisitor": 0, "visitor": 0, "nSpend": 0.0,
            "nROAS": 0.0, "nAOV": 0.0, "nCPA": 0.0, "nCPC": 0.0, "nCR %": 0.0, "New Visits %": 0.0,
            "eCPNV": 0.0, "ReportedRev":0.0, "Cost":0.0, "Gross Margin %":0.0, "Gross Profit":0.0
        }

# Utility function to process ads
def process_ads(data, fbadsdata, row, indexes, traffic):
    campaign_id, ad_set_id, ad_id = row[0], row[2], row[4]
    if traffic not in ('Facebook', 'Google'):
        row[indexes["Clicks"]] += (int(row[indexes["nvisitor"]]) + int(row[indexes["New Visits"]]))

    
    # Initialize campaign and ad set
    initialize_campaign_and_ad_set(data, campaign_id, row, ad_set_id)
   
    # Add ad details
    data[campaign_id]["ad_sets"][ad_set_id]["ads"].append({
        "ad_id": ad_id,
        "ad_name": row[indexes["ad_name"]],
        "Impression": row[indexes["Impression"]],
        "Clicks": row[indexes["Clicks"]],
        "Spend": round(float(row[indexes["Spend"]]),1),
        "Sales": int(row[indexes["Sales"]]),
        "Revenue": round(float(row[indexes["Revenue"]]),0),
		"Profit" : round(float(row[indexes["Revenue"]]) - float(row[indexes["Spend"]]),0),
		"CPM": 'n/a' if row[indexes["Impression"]] == 0 else round(float(row[indexes["Spend"]]*1000 / row[indexes["Impression"]]),1),
		"ROAS": 'n/a' if row[indexes["Spend"]] == 0 else round(float(row[indexes["Revenue"]]) / float(row[indexes["Spend"]]),2),
        "AOV": 'n/a' if row[indexes["Sales"]] == 0 else round(float(row[indexes["Revenue"]]) / int(row[indexes["Sales"]]),1),
        "CPA": 'n/a' if row[indexes["Sales"]] == 0 else round(float(row[indexes["Spend"]]) / int(row[indexes["Sales"]]),1),
        "CPC": 'n/a' if row[indexes["Clicks"]] == 0 else round(float(row[indexes["Spend"]]) / int(row[indexes["Clicks"]]),2),
		"CTR %": 'n/a' if row[indexes["Impression"]] == 0 else round(float(row[indexes["Clicks"]])*100 / int(row[indexes["Impression"]]),2),
        "CR %": 'n/a' if row[indexes["Clicks"]] == 0 else round(int(row[indexes["Sales"]])*100 / int(row[indexes["Clicks"]]),2),
        "CancelOrder": int(row[indexes["CancelOrder"]]),
        "CancelRev": float(row[indexes["CancelRev"]]),
        "ReportedRev": float(row[indexes["ReportedRev"]]),
        "Cost": float(row[indexes["Cost"]]),
        "nSales": int(row[indexes["nSales"]]),
        "nRevenue": float(row[indexes["nRevenue"]]),
        "nvisitor": int(row[indexes["nvisitor"]]),
        "visitor": int(row[indexes["New Visits"]]) + int(row[indexes["nvisitor"]]),
        "nROAS": 'n/a' if row[indexes["Spend"]] == 0 else round(float(row[indexes["nRevenue"]]) / float(row[indexes["Spend"]]),2),
        "nAOV": 'n/a' if row[indexes["nSales"]] == 0 else round(float(row[indexes["nRevenue"]]) / int(row[indexes["nSales"]]),1),
        "nCPA": 'n/a' if row[indexes["nSales"]] == 0 else round(float(row[indexes["Spend"]]) /int(row[indexes["nSales"]]),1),
        "nCPC": 'n/a' if row[indexes["New Visits"]] == 0 else round(float(row[indexes["Spend"]]) / int(row[indexes["New Visits"]]) + int(row[indexes["nvisitor"]]),2),
        "nCR %": 'n/a' if row[indexes["New Visits"]] == 0 else round(int(row[indexes["nSales"]])*100 / int(row[indexes["New Visits"]]) + int(row[indexes["nvisitor"]]),2),
		"New Visits %": 'n/a' if row[indexes["Clicks"]] == 0 else round(min(row[indexes["New Visits"]], row[indexes["Clicks"]])*100 / row[indexes["Clicks"]] ,2),
        "New Visits": min(row[indexes["New Visits"]], row[indexes["Clicks"]]),
        "eCPNV": 'n/a' if row[indexes["New Visits"]] == 0 else round(row[indexes["Spend"]] / row[indexes["New Visits"]] ,1),
        "Gross Margin %": 'n/a' if (row[indexes["Revenue"]]) == 0 else round((row[indexes["Revenue"]] - (row[indexes["Spend"]]+row[indexes["Cost"]]))*100 / row[indexes["Revenue"]] ,1),
        "Gross Profit": round((row[indexes["Revenue"]] - (row[indexes["Spend"]]+row[indexes["Cost"]])),1)
    })
    
    # Update metrics for campaign, ad set, and overall
    update_metrics(fbadsdata, row, indexes, traffic)
    update_metrics(data[campaign_id], row, indexes, traffic)
    update_metrics(data[campaign_id]["ad_sets"][ad_set_id], row, indexes, traffic)
	

@report_bp.route('/table', methods=['GET', 'OPTIONS'])
@cross_origin(origins='*', methods=['GET'], headers=['Content-Type'])
def get_reporttabledatafacebook():
    headers = request.headers
    body = request.args
    startdate = body.get('startdate')
    enddate = body.get('enddate')
    attribute = body.get('attribute')
    traffic = body.get('traffic')
    userid = headers.get('workspaceId')
    user = UserRegister.query.filter_by(workspace=userid).first()


    if user:
        sort = 'ASC' if attribute == 'first' else 'DESC'
        if traffic == 'Facebook':
            sql_query = text("SELECT * FROM table_facebookattribute(:workspace, :productid, :startdate, :enddate, :sort)")
            result = db.session.execute(sql_query, {
	            'workspace': userid, 'productid': user.productid,
	            'startdate': startdate, 'enddate': enddate, 'sort': sort
	        })
            data = result.fetchall()
        elif traffic == 'Google':
            sql_query = text("SELECT * FROM table_googleattribute(:workspace, :productid, :startdate, :enddate, :sort)")
            result = db.session.execute(sql_query, {
	            'workspace': userid, 'productid': user.productid,
	            'startdate': startdate, 'enddate': enddate, 'sort': sort
	        })
            data = result.fetchall()
        else:
            sql_query = text("SELECT * FROM table_otherattribute(:workspace, :productid, :startdate, :enddate, :sort, :src)")
            result = db.session.execute(sql_query, {
	            'workspace': userid, 'productid': user.productid,
	            'startdate': startdate, 'enddate': enddate, 'sort': sort, 'src':traffic
	        })
            data = result.fetchall()

        record = {}
        adsdata = {
            "Impression": 0, "Clicks": 0, "Spend": 0.0, "Profit":0.0,
            "Sales": 0, "Revenue": 0.0, "ROAS": 0.0, "AOV": 0.0,
			"CPC": 0.0, "CPA":0.0, "CTR %":0.0, "CR %":0.0, "CancelOrder": 0,
            "CancelRev": 0.0, "nSales": 0, "nRevenue": 0.0, 
            "New Visits": 0, "nvisitor":0, "visitor":0,
            "nROAS": 0.0, "nAOV": 0.0, "nCPA": 0.0, "nCPC": 0.0, "nCR %": 0.0, "New Visits %":0.0,
            "ReportedSale":0, "ReportedRev":0.0, "Cost":0.0, "Gross Margin %":0.0, "Gross Profit":0.0
        }

        # Process each row of data
        for row in data:
            process_ads(record, adsdata, row, {
                "ad_name": 5, "Impression": 6, "Clicks": 7, "Spend": 8,
                "Sales": 9, "Revenue": 10, "CancelOrder": 11, 
                "CancelRev": 12, "nSales": 13, "nRevenue": 14, 
                "New Visits": 15, "nvisitor":16, "visitor":17,
                "ReportedSale":18, "ReportedRev":19, "Cost":20
            }, traffic)

        # Convert ad_sets to list in campaigns
        campaign_list = list(record.values())
        for campaign in campaign_list:
            campaign["ad_sets"] = list(campaign["ad_sets"].values())

        adsdata["campaign"] = campaign_list

        return jsonify(adsdata)
    else:
        return jsonify({"msg": "No Data Found"}), 404



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
		sale_data['data'][key] = [{"revenue":round(row[1],0), "sales": int(row[2])}]
		sale_data['revenue'] = round(sale_data['revenue'] + float(row[1]),0)
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
		if channel in ('Facebook', 'Google'):
			channel = channel.lower()
		sort = 'ASC' if attribute == 'First' else 'DESC'
		sql_query = db.text("select * from table_salesdata(:workspace, :productid, :startdate, :enddate, :channel, :adid, :sort)")

		result = db.session.execute(sql_query, {'workspace': userid, 'productid':user.productid, 'startdate':startdate, 'enddate':enddate, 'channel':channel, 'adid':adid, 'sort':sort})
		data = result.fetchall()

		for row in data:
			element = {}
			element['complete_name'] = row[0]
			element['email_phone'] = row[1]
			element['total'] = float(row[2])
			element['order_date'] = row[3].strftime("%Y-%m-%d %H:%M:%S")
			element['trackid'] = row[4]
			output.append(element)
		
	return jsonify(output), 200



@report_bp.route('/tablesalejourney', methods=['GET', 'OPTIONS'])
@cross_origin(origins='*', methods=['GET'], headers=['Content-Type'])
def get_reporttablesalejourney():

	headers = request.headers
	body = request.args
	userid = headers.get('workspaceId')
	trackid = body.get('trackid')
	user = UserRegister.query.filter_by(workspace=userid).first()

	output = []
	if user:
		sql_query = db.text("select * from table_salejourney(:workspace, :productid, :trackid)")

		result = db.session.execute(sql_query, {'workspace': userid, 'productid':user.productid, 'trackid':trackid})
		data = result.fetchall()

		for row in data:
			element = {}
			element['event_time'] = row[0].strftime("%Y-%m-%d %H:%M:%S")
			element['adsource'] = row[1]
			element['adname'] = row[2]
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

	sql_query = db.text("select * from dashboard_graphsales(:workspace, :startdate, :enddate)")

	result = db.session.execute(sql_query, {'workspace': userid, 'startdate':startdate, 'enddate':enddate})
	data = result.fetchall()

	sale_data = {'revenue':{"data":[], "total":0.0, "compare":0.0}, 'sales':{"data":[],"total":0.0, "compare":0.0}, 'spend':{"data":[],"total":0.0, "compare":0.0}, 'roi':{"data":[],"total":0.0, "compare":0.0}, 'aov':{"data":[],"total":0.0, "compare":0.0}, 'cpa':{"data":[],"total":0.0, "compare":0.0}}
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


	sql_prevquery = db.text("select * from dashboard_graphprev_sales(:workspace, :startdate, :enddate)")
	try:
		startdate = datetime.strptime(startdate, '%b %d %Y')
		enddate = datetime.strptime(enddate, '%b %d %Y')
	except:
		startdate = datetime.strptime(startdate, '%b %d, %Y')
		enddate = datetime.strptime(enddate, '%b %d, %Y')
	difference = enddate - startdate
	enddate = (startdate - timedelta(days=1)).strftime('%Y-%m-%d')
	startdate = (startdate - difference - timedelta(days=1)).strftime('%Y-%m-%d')
	
	result = db.session.execute(sql_prevquery, {'workspace': userid, 'startdate':startdate, 'enddate':enddate})
	data = result.fetchall()
	for row in data:
		sale_data["revenue"]["compare"] = (100.0*(sale_data["revenue"]['total'] - round(float(row[0]),2)) / round(float(row[0]),2)) if row[0] != 0 else 0
		sale_data["sales"]["compare"] = (100.0*(sale_data["sales"]['total'] - round(float(row[1]),2)) / round(float(row[1]),2)) if row[1] != 0 else 0
		sale_data["spend"]["compare"] = (100.0*(sale_data["spend"]['total'] - round(float(row[2]),2)) / round(float(row[2]),2)) if row[2] != 0 else 0
		sale_data["roi"]["compare"] = (100.0*(sale_data["roi"]['total'] - round(float(row[3]),2)) / round(float(row[3]),2)) if row[3] != 0 else 0
		sale_data["aov"]["compare"] = (100.0*(sale_data["aov"]['total'] - round(float(row[4]),2)) / round(float(row[4]),2)) if row[4] != 0 else 0
		sale_data["cpa"]["compare"] = (100.0*(sale_data["cpa"]['total'] - round(float(row[5]),2)) / round(float(row[5]),2)) if row[5] != 0 else 0

	return jsonify(sale_data), 200


def sum_dicts(list1, list2):
	combined_dict = defaultdict(int)
	for entry in list1 + list2:
		combined_dict[entry['date']] += entry['value']

	result = [{"date": date, "value": value} for date, value in combined_dict.items()]

	return result


def channel_matrix(userid, productid, startdate, enddate, fbflag, ggflag):

	try:
		startdate_ = datetime.strptime(startdate, '%b %d %Y')
		enddate_ = datetime.strptime(enddate, '%b %d %Y')
	except:
		startdate_ = datetime.strptime(startdate, '%b %d, %Y')
		enddate_ = datetime.strptime(enddate, '%b %d, %Y')
	difference = enddate_ - startdate_
	enddate_prev = (startdate_ - timedelta(days=1)).strftime('%Y-%m-%d')
	startdate_prev = (startdate_ - difference - timedelta(days=1)).strftime('%Y-%m-%d')

	sort = 'DESC'
	metric={}
	adspend = {'revenue':{"data":[], "total":0.0, "compare":0.0}, 'sales':{"data":[],"total":0.0, "compare":0.0}, 'spend':{"data":[],"total":0.0, "compare":0.0}, 'roi':{"data":[],"total":0.0, "compare":0.0}, 'aov':{"data":[],"total":0.0, "compare":0.0}, 'cpa':{"data":[],"total":0.0, "compare":0.0}, 'profit':{"data":[],"total":0.0, "compare":0.0}, 'cr':{"data":[],"total":0.0, "compare":0.0}, 'click':{"data":[],"total":0.0, "compare":0.0}}
	fbadsdata = {'accountpresent':fbflag,'revenue':{"data":[], "total":0.0, "compare":0.0}, 'sales':{"data":[],"total":0.0, "compare":0.0}, 'spend':{"data":[],"total":0.0, "compare":0.0}, 'roi':{"data":[],"total":0.0, "compare":0.0}, 'aov':{"data":[],"total":0.0, "compare":0.0}, 'cpa':{"data":[],"total":0.0, "compare":0.0}, 'profit':{"data":[],"total":0.0, "compare":0.0}, 'cr':{"data":[],"total":0.0, "compare":0.0},'click':{"data":[],"total":0.0, "compare":0.0}}
	fbrevenue =0; fbsales=0; fbspend=0; fbroi=0; fbaov=0; fbcpa=0; fbcr=0; fbprofit=0; fbclick=0;
	if fbflag:
		sql_query_fb = db.text("select * from dashboard_facebookattribute(:workspace, :productid, :startdate, :enddate, :sort)")
		result = db.session.execute(sql_query_fb, {'workspace': userid, 'productid':productid, 'startdate':startdate, 'enddate':enddate, 'sort':sort})
		data = result.fetchall()

		for row in data:
			date_str = row[0].strftime("%Y-%m-%d")
			revenue = round(float(row[5]),2)
			sales = int(row[4])
			spend = round(float(row[3]), 2)
			roi = round(float(row[6]), 2)
			aov = round(float(row[7]), 2)
			cpa = round(float(row[8]), 2)
			cr = round(float(row[9]), 2)
			profit = round(float(row[10]), 2)
			click = round(float(row[2]), 2)

			fbadsdata["revenue"]["data"].append({"value": round(revenue), "date": date_str})
		
			fbadsdata["sales"]["data"].append({"value": sales, "date": date_str})
			fbadsdata["spend"]["data"].append({"value": round(spend), "date": date_str})
			fbadsdata["roi"]["data"].append({"value": roi, "date": date_str})
			fbadsdata["aov"]["data"].append({"value": aov, "date": date_str})
			fbadsdata["cpa"]["data"].append({"value": cpa, "date": date_str})
			fbadsdata["cr"]["data"].append({"value": cr, "date": date_str})
			fbadsdata["profit"]["data"].append({"value": round(profit), "date": date_str})
			fbadsdata["click"]["data"].append({"value": click, "date": date_str})

			fbadsdata["revenue"]['total'] += revenue
			fbadsdata["sales"]['total'] += sales
			fbadsdata["spend"]['total'] += spend
			fbadsdata["profit"]['total'] += profit
			fbadsdata["click"]['total'] += click

			adspend["revenue"]['total'] += revenue
			adspend["sales"]['total'] += sales
			adspend["spend"]['total'] += spend
			adspend["profit"]['total'] += profit
			adspend["click"]['total'] += click

		fbadsdata["aov"]['total'] = round(fbadsdata["revenue"]['total']/max(fbadsdata["sales"]['total'],1),2)
		fbadsdata["cpa"]['total'] = round(fbadsdata["spend"]['total']/max(fbadsdata["sales"]['total'],1),2)
		fbadsdata["roi"]['total'] = round(fbadsdata["revenue"]['total']/max(fbadsdata["spend"]['total'],1),2)
		fbadsdata["cr"]['total'] = round(fbadsdata["sales"]['total']/max(fbadsdata["click"]['total'],1),2)

		sqlquery_fbprev = db.text("select * from dashboard_facebookprev_attribute(:workspace, :productid, :startdate, :enddate, :sort)")
		result = db.session.execute(sqlquery_fbprev, {'workspace': userid, 'productid':productid, 'startdate':startdate_prev, 'enddate':enddate_prev, 'sort':sort})
		body = result.fetchall()

		for row in body:
			fbrevenue = round(float(row[4]))
			fbsales = int(row[3])
			fbspend = round(float(row[2]))
			fbroi = round(float(row[5]), 2)
			fbaov = round(float(row[6]), 2)
			fbcpa = round(float(row[7]), 2)
			fbcr = round(float(row[8]), 2)
			fbprofit = round(float(row[9]))
			fbclick = round(float(row[1]), 2)

			fbadsdata["revenue"]["compare"] = (100.0*(fbadsdata["revenue"]['total'] - fbrevenue) / fbrevenue) if fbrevenue != 0 else 0
			fbadsdata["sales"]["compare"] = (100.0*(fbadsdata["sales"]['total'] - fbsales) / fbsales) if fbsales != 0 else 0
			fbadsdata["spend"]["compare"] = (100.0*(fbadsdata["spend"]['total'] - fbspend) / fbspend) if fbspend != 0 else 0
			fbadsdata["roi"]["compare"] = (100.0*(fbadsdata["roi"]['total'] - fbroi) / fbroi) if fbroi != 0 else 0
			fbadsdata["aov"]["compare"] = (100.0*(fbadsdata["aov"]['total'] - fbaov) / fbaov) if fbaov != 0 else 0
			fbadsdata["cpa"]["compare"] = (100.0*(fbadsdata["cpa"]['total'] - fbcpa) / fbcpa) if fbcpa != 0 else 0
			fbadsdata["cr"]["compare"] = (100.0*(fbadsdata["cr"]['total'] - fbcr) / fbcr) if fbcr != 0 else 0
			fbadsdata["profit"]["compare"] = (100.0*(fbadsdata["profit"]['total'] - fbprofit) / abs(fbprofit)) if fbprofit != 0 else 0
			fbadsdata["click"]["compare"] = (100.0*(fbadsdata["click"]['total'] - fbclick) / fbclick) if fbclick != 0 else 0
	
	metric['meta'] = fbadsdata

	ggdsdata = {'accountpresent':ggflag,'revenue':{"data":[], "total":0.0, "compare":0.0}, 'sales':{"data":[],"total":0.0, "compare":0.0}, 'spend':{"data":[],"total":0.0, "compare":0.0}, 'roi':{"data":[],"total":0.0, "compare":0.0}, 'aov':{"data":[],"total":0.0, "compare":0.0}, 'cpa':{"data":[],"total":0.0, "compare":0.0}, 'profit':{"data":[],"total":0.0, "compare":0.0}, 'cr':{"data":[],"total":0.0, "compare":0.0},'click':{"data":[],"total":0.0, "compare":0.0}}
	ggrevenue =0; ggsales=0; ggspend=0; ggroi=0; ggaov=0; ggcpa=0; ggcr=0; ggprofit=0; ggclick=0;
	if ggflag:
		sql_query_fb = db.text("select * from dashboard_googleattribute(:workspace, :productid, :startdate, :enddate, :sort)")
		result = db.session.execute(sql_query_fb, {'workspace': userid, 'productid':productid, 'startdate':startdate, 'enddate':enddate, 'sort':sort})
		data = result.fetchall()

		for row in data:

			date_str = row[0].strftime("%Y-%m-%d")
			revenue = round(float(row[5]),2)
			sales = int(row[4])
			spend = round(float(row[3]), 2)
			roi = round(float(row[6]), 2)
			aov = round(float(row[7]), 2)
			cpa = round(float(row[8]), 2)
			cr = round(float(row[9]), 2)
			profit = round(float(row[10]), 2)
			click = round(float(row[2]), 2)

			ggdsdata["revenue"]["data"].append({"value": round(revenue), "date": date_str})
			ggdsdata["sales"]["data"].append({"value": sales, "date": date_str})
			ggdsdata["spend"]["data"].append({"value": round(spend), "date": date_str})
			ggdsdata["roi"]["data"].append({"value": roi, "date": date_str})
			ggdsdata["aov"]["data"].append({"value": aov, "date": date_str})
			ggdsdata["cpa"]["data"].append({"value": cpa, "date": date_str})
			ggdsdata["cr"]["data"].append({"value": cr, "date": date_str})
			ggdsdata["profit"]["data"].append({"value": round(profit), "date": date_str})
			ggdsdata["click"]["data"].append({"value": click, "date": date_str})

			ggdsdata["revenue"]['total'] += revenue
			ggdsdata["sales"]['total'] += sales
			ggdsdata["spend"]['total'] += spend
			ggdsdata["profit"]['total'] += profit
			ggdsdata["click"]['total'] += click


			adspend["revenue"]['total'] += revenue
			adspend["sales"]['total'] += sales
			adspend["spend"]['total'] += spend
			adspend["profit"]['total'] += profit
			adspend["click"]['total'] += click

		ggdsdata["aov"]['total'] = round(ggdsdata["revenue"]['total']/max(ggdsdata["sales"]['total'],1),2)
		ggdsdata["cpa"]['total'] = round(ggdsdata["spend"]['total']/max(ggdsdata["sales"]['total'],1),2)
		ggdsdata["roi"]['total'] = round(ggdsdata["revenue"]['total']/max(ggdsdata["spend"]['total'],1),2)
		ggdsdata["cr"]['total'] = round(ggdsdata["sales"]['total']/max(ggdsdata["click"]['total'],1),2)

		sqlquery_ggprev = db.text("select * from dashboard_googleprev_attribute(:workspace, :productid, :startdate, :enddate, :sort)")
		result = db.session.execute(sqlquery_ggprev, {'workspace': userid, 'productid':productid, 'startdate':startdate_prev, 'enddate':enddate_prev, 'sort':sort})
		body = result.fetchall()
		
		for row in body:
			ggrevenue = round(float(row[4]),2)
			ggsales = int(row[3])
			ggspend = round(float(row[2]), 2)
			ggroi = round(float(row[5]), 2)
			ggaov = round(float(row[6]), 2)
			ggcpa = round(float(row[7]), 2)
			ggcr = round(float(row[8]), 2)
			ggprofit = round(float(row[9]), 2)
			ggclick = round(float(row[1]), 2)

			ggdsdata["revenue"]["compare"] = (100.0*(ggdsdata["revenue"]['total'] - ggrevenue) / max(ggrevenue,1))  if ggrevenue != 0 else 0
			ggdsdata["sales"]["compare"] = (100.0*(ggdsdata["sales"]['total'] - ggsales) / max(ggsales,1)) if ggsales != 0 else 0
			ggdsdata["spend"]["compare"] = (100.0*(ggdsdata["spend"]['total'] - ggspend) / max(ggspend,1)) if ggspend != 0 else 0
			ggdsdata["roi"]["compare"] = (100.0*(ggdsdata["roi"]['total'] - ggroi) / max(ggroi,0.01)) if ggroi != 0 else 0
			ggdsdata["aov"]["compare"] = (100.0*(ggdsdata["aov"]['total'] - ggaov) / max(ggaov,1)) if ggaov != 0 else 0
			ggdsdata["cpa"]["compare"] = (100.0*(ggdsdata["cpa"]['total'] - ggcpa) / max(ggcpa,1)) if ggcpa != 0 else 0
			ggdsdata["cr"]["compare"] = (100.0*(ggdsdata["cr"]['total'] - ggcr) / max(ggcr, 0.01)) if ggcr != 0 else 0
			ggdsdata["profit"]["compare"] = (100.0*(ggdsdata["profit"]['total'] - ggprofit) / max(abs(ggprofit),1)) if ggprofit != 0 else 0
			ggdsdata["click"]["compare"] = (100.0*(ggdsdata["click"]['total'] - ggclick) / max(ggclick,1)) if ggclick != 0 else 0

	metric['google'] = ggdsdata

	for key in adspend:
		adspend[key]['data'] = sum_dicts(fbadsdata[key]['data'], ggdsdata[key]['data'])
	adspend['aov']['total'] = adspend['revenue']['total'] / max(adspend['sales']['total'], 1)
	adspend['cpa']['total'] = adspend['spend']['total'] / max(adspend['sales']['total'], 1)
	adspend['roi']['total'] = adspend['revenue']['total'] / max(adspend['spend']['total'], 1)
	adspend["cr"]['total'] = round(adspend["sales"]['total']/max(adspend["click"]['total'],1),2)

	adspendprev_roi = (fbrevenue + ggrevenue) / max((fbspend + ggspend) ,1)
	adspendprev_aov = (fbrevenue + ggrevenue) / max((fbsales + ggsales),1)
	adspendprev_cpa = (fbspend + ggspend) / max((fbsales + ggsales),1)
	adspendprev_cr = (fbsales + ggsales) / max((fbclick + ggclick) ,1)

	adspend["spend"]["compare"] = (100.0*(adspend["spend"]["total"] - (fbspend + ggspend)) / max((fbspend + ggspend),1)) if (fbspend + ggspend) != 0 else 0
	adspend["sales"]["compare"] = (100.0*(adspend["sales"]["total"] - (fbsales + ggsales)) / max((fbsales + ggsales),1)) if (fbsales + ggsales) != 0 else 0
	adspend["revenue"]["compare"] = (100.0*(adspend["revenue"]["total"] - (fbrevenue + ggrevenue)) / max((fbrevenue + ggrevenue),1)) if (fbrevenue + ggrevenue) != 0 else 0
	adspend["roi"]["compare"] = (100.0*(adspend["roi"]['total'] - adspendprev_roi) / max(adspendprev_roi,0.01)) if adspendprev_roi != 0 else 0
	adspend["aov"]["compare"] = (100.0*(adspend["aov"]['total'] - adspendprev_aov) / max(adspendprev_aov,1)) if adspendprev_aov != 0 else 0
	adspend["cpa"]["compare"] = (100.0*(adspend["cpa"]['total'] - adspendprev_cpa) / max(adspendprev_cpa,1)) if adspendprev_cpa != 0 else 0
	adspend["cr"]["compare"] = (100.0*(adspend["cr"]['total'] - adspendprev_cr) / max(adspendprev_cr, 0.01)) if adspendprev_cr != 0 else 0
	adspend["click"]["compare"] = (100.0*(adspend["click"]['total'] - (fbclick + ggclick)) / max((fbclick + ggclick), 1)) if (fbclick + ggclick) != 0 else 0
	adspend["profit"]["compare"] = (100.0*(adspend["profit"]['total'] - (fbprofit + ggprofit)) / max(abs(fbprofit + ggprofit), 1)) if (fbprofit + ggprofit) != 0 else 0
	
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



def dashbaord_mongo_query(metric, productid, startdate, enddate):
	
    if metric == 'pageview':
        pipeline = [
        {
            '$match': {
                'body.pageLoad': 1,
                'productid': int(productid),
                'creation_at': {'$gte': startdate, '$lte': enddate}
            }
        },
        {
            '$group': {
                '_id': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$creation_at'}},
                'pageview': {'$sum': 1}
            }
        },
        {
            '$sort': {'_id': 1}
        }
        ]
        return list(CustomerInfo.objects.aggregate(*pipeline))
    
    if metric in ('localsession', 'session'):
        pipeline = [
            {
                '$match': {
                    'productid': int(productid),
                    'creation_at': {'$gte': startdate, '$lte': enddate},
                    'body.customerInfo': {}
                }
            },
            {
                '$group': {
                    '_id': {
                        'date': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$creation_at'}},
                        metric: '$'+metric
                    }
                }
            },
            {
                '$group': {
                    '_id': '$_id.date',
                    metric: {'$sum': 1}
                }
            },
            {
                '$sort': {'_id': 1}
            }
        ]
        return list(CustomerInfo.objects.aggregate(*pipeline))
    
    if metric == 'nuser':
        pipeline = [
        {
            '$match': {
                'productid': int(productid),
                'creation_at': {'$gte': startdate, '$lte': enddate},
                'body.setSession': 1
            }
        },
        {
            '$group': {
                '_id': {
                    'date': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$creation_at'}}
                },
                'distinctSessions': {'$addToSet': '$session'}
            }
        },
        {
            '$project': {
                'date': '$_id.date',
                'nuser': {'$size': '$distinctSessions'}
            }
        },
        {
            '$sort': {'date': 1}
        }
    ]
        return list(CustomerInfo.objects.aggregate(*pipeline))



@report_bp.route('/dashboardtraffic', methods=['GET', 'OPTIONS'])
@cross_origin(origins='*', methods=['GET'], headers=['Content-Type'])
def get_dashboardtraffic():
    headers = request.headers
    _body = request.args
    # startdate = datetime.strptime(_body.get('startdate'), "%Y-%m-%d")
    # enddate = datetime.strptime(_body.get('enddate'), "%Y-%m-%d") + timedelta(days=1)
    try:
        startdate = datetime.strptime(_body.get('startdate'), '%b %d %Y')
        enddate = datetime.strptime(_body.get('enddate'), '%b %d %Y') + timedelta(days=1)
    except:
        startdate = datetime.strptime(_body.get('startdate'), '%b %d, %Y')
        enddate = datetime.strptime(_body.get('enddate'), '%b %d, %Y') + timedelta(days=1)
    difference = enddate - startdate
    enddate_prev = (startdate - timedelta(days=1)).strftime('%Y-%m-%d')
    startdate_prev = (startdate - difference - timedelta(days=1)).strftime('%Y-%m-%d')
    userid = headers.get('workspaceId')
    user = UserRegister.query.filter_by(workspace=userid).first()

    trafficdata = {'pageview':{"data":[], "total":0.0, "compare":0.0}, 'session':{"data":[], "total":0.0, "compare":0.0}, 'localsession':{"data":[], "total":0.0, "compare":0.0}, 'nuser':{"data":[], "total":0.0, "compare":0.0}}
    
    for metric in ['pageview','session','localsession','nuser']:
        result = dashbaord_mongo_query(metric, user.productid, startdate, enddate)
        if metric == 'pageview':
            metric_result = MongoMetric.query.filter(MongoMetric.dated>=_body.get('startdate'), MongoMetric.dated<=_body.get('enddate'), MongoMetric.workspace==userid, MongoMetric.metric=='page_view').all()
        else:
            metric_result = MongoMetric.query.filter(MongoMetric.dated>=_body.get('startdate'), MongoMetric.dated<=_body.get('enddate'), MongoMetric.workspace==userid, MongoMetric.metric==metric).all()

        total = 0
        total_cmp = 0
        combined_dict = defaultdict(int)

        for entry in metric_result:
            dated = entry.dated
            # Add to combined_dict using the date as key, and accumulate the values
            combined_dict[dated.strftime('%Y-%m-%d')] += entry.value
            total += entry.value
        
        for ele in result:
            dd = ele['_id']['date'] if metric == 'nuser' else ele['_id']
            combined_dict[dd] += ele[metric]
            total += ele[metric]

        # Update total in trafficdata
        trafficdata[metric]['total'] = total

        # Now update trafficdata[metric]['data'] with the combined_dict logic
        for date, value in combined_dict.items():
            date_found = False

            # Check if the date already exists in the metric data
            for entry in trafficdata[metric]['data']:
                if entry['date'] == date:
                    # If the date is found, add the value to the existing value
                    entry['value'] += value
                    date_found = True
                    break

            # If the date is not found, append a new dictionary with the date and value
            if not date_found:
                trafficdata[metric]['data'].append({'date': date, 'value': value})
            trafficdata[metric]['data'].sort(key=lambda x: x['date'])

        metric_cmp = MongoMetric.query.filter(MongoMetric.dated>=startdate_prev, MongoMetric.dated<=enddate_prev, MongoMetric.workspace==userid, MongoMetric.metric==metric).all()
        for entry in metric_cmp:
            total_cmp += entry.value
        trafficdata[metric]['compare'] = (100.0*(total - total_cmp) / max(total_cmp,1)) if (total_cmp) != 0 else 0

     
    # localsess_pipeline = [
    # {'$match': {
    #     'productid': int(user.productid),
    #     'creation_at': {'$gte': startdate, '$lte': enddate}
    # }},
    # {'$group': {
    #     '_id': '$localsession'
    # }},
    # {'$count': 'distinct_localsession_count'}
    # ]
    # localsess_pipeline = [
    # {'$match': {
    #     'productid': int(user.productid),
    #     'creation_at': {'$gte': startdate, '$lte': enddate}
    # }},
    # {'$project': {
    #     'localsession': 1,
    #     'date': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$creation_at'}}
    # }},
    # {'$group': {
    #     '_id': '$date',
    #     'distinct_localsessions': {'$addToSet': '$localsession'}
    # }},
    # {'$project': {
    #     '_id': 1,
    #     'distinct_localsession_count': {'$size': '$distinct_localsessions'}
    # }}
    # ]
    # usr = list(CustomerInfo.objects.aggregate(*localsess_pipeline))
    # try:
    # 	data['user'] = usr[0]['distinct_localsession_count']
    # except:
    # 	data['user'] = 0


    # sess_pipeline = [
    # {'$match': {
    #     'productid': int(user.productid),
    #     'creation_at': {'$gte': startdate, '$lte': enddate},
    # 	'body.customerInfo': {}
    # }},
    # {'$group': {
    #     '_id': '$session'  # Group by 'localsession' to get distinct values
    # }},
    # {'$count': 'distinct_session_count'}  # Counts the number of distinct groups
    # ]
    # unique_usr = list(CustomerInfo.objects.aggregate(*sess_pipeline))
    # try:
    # 	data['unique_user'] = unique_usr[0]['distinct_session_count']
    # except:
    # 	data['unique_user'] = 0


    # if user.product_type == 'growth':
    # 	bounce_pipeline = [
    # 		{
    # 			'$match': {
    # 				'productid': float(user.productid),
    # 				'creation_at': {'$gte': startdate, '$lte': enddate}
    # 			}
    # 		},
    # 		{
    # 			'$group': {
    # 				'_id': '$localsession',
    # 				'count': {'$sum': 1}  # Count occurrences of each localsession
    # 			}
    # 		},
    # 		{
    # 			'$match': {
    # 				'count': 1  # Filter to keep only those groups where count is exactly 1
    # 			}
    # 		},
    # 		{
    # 			'$count': 'unique_localsession_count'
    # 		}
    # 	]

    # 	session = data['user'] if data['user'] !=0 else 1
    # 	try:
    # 		bounce = list(CustomerInfo.objects.aggregate(*bounce_pipeline))
    # 		data['bounce_rate'] = round(bounce[0]['unique_localsession_count']*100/session,2)
    # 	except:
    # 		data['bounce_rate'] = 0.0

    # 	data['page_view_per_session'] = round(data['page_view']/session, 2)

    
    # tablename = 'order_' + userid
    # orderTable = order_table_dynamic(tablename)
    # db.Model.metadata.reflect(db.engine)
    # conversion = orderTable.query.filter(
    #     orderTable.order_date >= startdate,
    #     orderTable.order_date <= enddate
    # ).count()
    # if data['user'] == 0:
    # 	data['cr'] = 0.0
    # else:
    # 	data['cr'] = round(conversion*100.0/data['user'],2)


    return jsonify(trafficdata), 200