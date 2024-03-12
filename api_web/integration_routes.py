# integration pg

from ..db_model.sql_models import UserRegister
from ..connection import db

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin


intgration_cd = Blueprint('integration', __name__)

@intgration_cd.route('/code', methods=['GET', 'OPTIONS'])
@cross_origin(origins='*', methods=['GET', 'POST', 'OPTIONS'], headers=['Content-Type'])
def code_productid():
    headers = request.headers
    workspace = headers.get('workspaceId')

    user = UserRegister.query.filter_by(workspace=workspace).first()

    if user:
        return jsonify({"productid":user.productid}), 200
    else:
        return jsonify({"message":"Workspace don't found"}), 400