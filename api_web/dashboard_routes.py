from ..db_model.sql_models import UserRegister, ClientFacebookredentials, ClientGoogleCredentials, MongoMetric, UTMSource
from ..db_model.mongo_models import CustomerInfo
from ..connection import db

from flask import Blueprint, request, jsonify
from sqlalchemy import text
from sqlalchemy.sql import func
from flask_cors import cross_origin
import json, os, re

from datetime import datetime, timedelta
from collections import defaultdict


dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/demographic/heatmap', methods=['GET', 'OPTIONS'])
@cross_origin(origins='*', methods=['GET'], headers=['Content-Type'])
def dashboard_heatmap():

	headers = request.headers
	body = request.args
	startdate = body.get('startdate')
	enddate = body.get('enddate')
	userid = headers.get('workspaceId')

	user = UserRegister.query.filter_by(workspace=userid).first()
	productid = user.productid

	sql_query = db.text("select * from demographic_graph (:workspace, :productid, :startdate, :enddate)")

	result = db.session.execute(sql_query, {'workspace': userid, 'productid':productid, 'startdate':startdate, 'enddate':enddate})
	data = result.fetchall()

	columns = ["adsource", "country", "region", "spend", "impresion", "traffic", "clicks", "orders", "cr", "revenue", "aov", "cpa"]

	results = [dict(zip(columns, row)) for row in data]
	return jsonify(results),200
