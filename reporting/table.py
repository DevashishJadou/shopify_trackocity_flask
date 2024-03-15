from ..db_model.sql_models import UserRegister
from ..connection import db, app

from flask import Blueprint, request, redirect, jsonify, make_response

report_bp = Blueprint('reporting', __name__)


@report_bp.route('/reporting/table')
def get_data():

    headers = request.headers
    userid = headers.get('workspaceId')
    user = UserRegister.query.filter_by(workspace=userid).first()

    sql_query = db.text("select * from my_view_function(:workspace, :productid)")


    result = db.session.execute(sql_query, {'client_id': userid, 'productid':user.productid})
    data = result.fetchall()

    # Transform the result into the desired JSON format
    data_json = {}
    for row in data:
        import pdb
        pdb.set_trace()
        id = row[0]
        if id not in data_json:
            data_json[id] = {
                'order_date': row[1],
                'transcation_id': row[2],
                'email': row[3],
                'created_at': row[4],
                'total': row[5],
                'sessions': []
            }
        session = {
            'sessionid': row[6],
            'firstname': row[7],
            'lastname': row[8],
            'form_event_time': row[9],
            'localsession': row[10],
            'adsource': row[11],
            'adid': row[12],
            'event_time': row[13]
        }
        data_json[id]['sessions'].append(session)

    return jsonify(data_json)

if __name__ == '__main__':
    app.run(debug=True)
