# reporting_routes

# from ..db_model.sql_models import UserRegister
# from ..connection import db
from db_model.sql_models import UserRegister
from connection import db

from flask import Blueprint, request, jsonify

# from .schema import FB
from api_web.schema import FB
from flask_cors import cross_origin

report_bp = Blueprint('repot', __name__)


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
