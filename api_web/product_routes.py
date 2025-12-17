# product_routes

from ..db_model.sql_models import UserRegister
from ..db_model.mongo_models import CustomerInfo
from ..connection import db

from flask import Blueprint, request, jsonify
from sqlalchemy import text
from sqlalchemy.sql import func
from .schema import FB
from flask_cors import cross_origin
import json, os, re

from datetime import datetime, timedelta
from collections import defaultdict

product_bp = Blueprint('product', __name__)
ENCRYPTION_KEY = os.environ.get('_ENCYPT_KEY')


@product_bp.route('/products', methods=['GET', 'OPTIONS'])
@cross_origin(origins='*', methods=['GET'], headers=['Content-Type'])
def get_products():
    headers = request.headers
    body = request.args
    startdate = body.get('startdate')
    enddate = body.get('enddate')
    traffic = body.get('traffic')
    userid = headers.get('workspaceId')

    
    user = UserRegister.query.filter_by(workspace=userid).first()

    try:
        sql_query = text("SELECT * FROM get_products_data(:workspace, :productid,  :startdate, :enddate,:channel)")
        op = db.session.execute(sql_query, { 'workspace': userid, 'productid':user.productid, 'startdate':startdate, 'enddate':enddate,'channel':traffic})
        data = op.fetchall()
    except Exception as e:
        db.session.rollback()
        raise e
    finally:
        db.session.close()


    columns = ['product_name','image_url','impressions', 'clicks', 'add_to_cart','purchases','spend', 'revenue', 'units', 'roas','cpc', 'cr_percent', 'c2c_percent']
    result = [dict(zip(columns, row)) for row in data]

    return result


@product_bp.route('/catalogue_products', methods=['GET', 'OPTIONS'])
@cross_origin(origins='*', methods=['GET'], headers=['Content-Type'])
def get_catalogue_products():
    headers = request.headers
    body = request.args
    startdate = body.get('startdate')
    enddate = body.get('enddate')
    traffic = body.get('traffic')
    userid = headers.get('workspaceId')

    
    user = UserRegister.query.filter_by(workspace=userid).first()

    try:
        sql_query = text("SELECT * FROM get_catalogue_products_data(:workspace, :productid,  :startdate, :enddate,:channel)")
        op = db.session.execute(sql_query, { 'workspace': userid, 'productid':user.productid, 'startdate':startdate, 'enddate':enddate,'channel':traffic})
        data = op.fetchall()
    except Exception as e:
        db.session.rollback()
        raise e
    finally:
        db.session.close()


    columns = ['product_name','image_url','impressions', 'clicks', 'add_to_cart','purchases','spend', 'revenue', 'units', 'roas','cpc', 'cr_percent', 'c2c_percent']
    result = [dict(zip(columns, row)) for row in data]

    return result