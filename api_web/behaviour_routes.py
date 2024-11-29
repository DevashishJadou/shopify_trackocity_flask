from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from datetime import datetime

from sqlalchemy import text
from decimal import Decimal
from ..db_model.sql_models import UserRegister
from ..connection import db

# Define the Blueprint
behaviour_bp = Blueprint('behaviour', __name__)

def fetch_sales_velocity(workspace, productid, startdate, enddate, channel=None, adid=None):
    """
    Fetches data for sales velocity from the behaviour_sale_velocity function in the database.
    """

    # Adjust channel and adid parameters as needed
    if channel in ('Facebook', 'Google'):
        channel = channel.lower()
    elif channel and channel.lower() == 'all':
        channel = None
    
    if adid and adid.lower() == 'all':
        adid = None

    # SQL Query with parameters for the stored function
    sql_query = text("SELECT * FROM behaviour_sale_velocity(:workspace, :productid, :startdate, :enddate, :channel, :adid)")
    result = db.session.execute(sql_query, {
        'workspace': workspace, 
        'productid': productid,
        'startdate': startdate, 
        'enddate': enddate, 
        'channel': channel, 
        'adid': adid
    })
    columns = result.keys()
    data = [dict(zip(columns, row)) for row in result.fetchall()]
    return data


def process_sales_velocity_data(df, include_dayzero=False):
    # Extract the relevant values from the data dictionary
    sales_data = df[0]
    
    # Mapping of days to the relevant fields in the data
    day_mapping = [
        ("1 Day", "day1", "total_day1"),
        ("2-7 Days", "day2_7", "total_day2_7"),
        ("8-14 Days", "day8_14", "total_day8_14"),
        ("15-30 Days", "day15_30", "total_day15_30"),
        ("31-60 Days", "day31_60", "total_day31_60"),
        ("61-90 Days", "day61_90", "total_day61_90"),
        ("91-180 Days", "day91_180", "total_day91_180"),
        ("181-360 Days", "day181_360", "total_day181_360"),
        ("More than 360 Days", "day360", "total_day360")
    ]

    if include_dayzero:
        day_mapping = [("0 Day", "day0", "total_day0")] + day_mapping
    
    # Calculate overall totals
    total_contacts = sum(sales_data[day] for _, day, _ in day_mapping)
    total_sales_value = sum(sales_data[total_day] for _, _, total_day in day_mapping if sales_data[total_day] is not None)
    
    # Start building the result
    result = {
        "sales_conversion": total_contacts,
        'traffic': max(sales_data["traffic"],1),
        "value": float(total_sales_value),
        "table_data": []
    }
    
    # Variables for cumulative sales percentage calculation
    cumulative_sales = 0
    cumulative_contact = 0

    # Process each time period
    for label, contact_key, value_key in day_mapping:
        contacts = sales_data[contact_key]
        sales_value = sales_data[value_key] if sales_data[value_key] is not None else Decimal(0)
        
        # Calculate metrics
        sales_conversion_rate = contacts / total_contacts if total_contacts > 0 else 0
        average_sales_value = float(sales_value / contacts) if contacts > 0 else 0
        percentage_contact = round((contacts / sales_data["traffic"]) * 100.0 if sales_data["traffic"] > 0 else 0,2)
        percentage_sales = round((sales_value  / total_sales_value * 100) if total_sales_value > 0 else 0,2)
        cumulative_sales += percentage_sales
        cumulative_contact += percentage_contact

        # Append to the table-data
        result["table_data"].append({
            "days_to_first_sale": label,
            "sales_conversion_rate": round(sales_conversion_rate, 2),
            "average_sales_value": round(average_sales_value, 2),
            "percentage_contact": round(percentage_contact, 2),
            "percentage_sales": round(percentage_sales, 2),
            "cumulative_sales": round(cumulative_sales, 2),
            "cumulative_contact": round(cumulative_contact, 2)
        })

    return result



@behaviour_bp.route('/sales_velocity', methods=['GET'])
@cross_origin(origins='*', methods=['GET'], headers=['Content-Type'])
def sales_velocity():
    """
    Endpoint to get sales velocity data as a JSON response.
    """
    headers = request.headers
    body = request.args

    # Retrieve request parameters
    startdate = body.get('startdate')
    enddate = body.get('enddate')
    userid = headers.get('workspaceId')
    adid = body.get('campaign')
    channel = body.get('channel')
    include_dayzero = body.get('include_dayzero')
    include_dayzero = include_dayzero.lower() == 'true'

    # Get user info to obtain product ID
    user = UserRegister.query.filter_by(workspace=userid).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Fetch data from the function
    df = fetch_sales_velocity(
        workspace=userid, 
        productid=user.productid, 
        startdate=startdate, 
        enddate=enddate, 
        channel=channel, 
        adid=adid
    )

    # Process the DataFrame
    final_data = process_sales_velocity_data(df, include_dayzero)

    return jsonify(final_data)




@behaviour_bp.route('/sales_cohort', methods=['GET'])
@cross_origin(origins='*', methods=['GET'], headers=['Content-Type'])
def scustomer_cohort():
    headers = request.headers
    body = request.args

    # Retrieve request parameters
    startdate = body.get('startdate')
    enddate = body.get('enddate')
    userid = headers.get('workspaceId')
    interval = body.get('interval')
    adid = body.get('campaign')
    channel = body.get('channel')
    today = datetime.today()

    user = UserRegister.query.filter_by(workspace=userid).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    if interval.lower() == 'weekly':
        interval_format = 'YYYY-WW'
    else:
        interval_format = 'YYYY-MM'
    
    if channel in ('Facebook', 'Google'):
        channel = channel.lower()
    elif channel and channel.lower() == 'all':
        channel = None
    
    if adid and adid.lower() == 'all':
        adid = None

    sql_query = text("SELECT * FROM behaviour_cohort(:workspace, :productid, :startdate, :enddate, :group_format, :channel, :adid)")
    result = db.session.execute(sql_query, {
        'workspace': userid, 
        'productid': user.productid,
        'startdate': startdate, 
        'enddate': enddate, 
        'channel': channel, 
        'adid': adid,
        'group_format': interval_format
    })
    columns = result.keys()

    def process_row(row, interval):
        # Parse the month and year from "_period"
        if interval.lower() == 'weekly':
            _period = row["_period"]
            formatted_period = f"{_period[2:4]}-{_period[5:7]}"
            row_week_date = datetime.strptime(formatted_period, "%y-%W")
            current_week = today.isocalendar()[1]  # Current ISO week number
            week_diff = (today.year - row_week_date.year) * 52 + (current_week - int(_period[5:7]))
            processed_row = {
                "_period": row["_period"],
                "new_customer": row["new_customer"],
                "nrev": row["nrev"],
                "naov": row["naov"],
                "nltv": row["nltv"],
                "multiorder": row["multiorder"],
                "firstpurchase": row["firstpurchase"],
                "day7": row["day7"] if week_diff >= 1 else None,
                "day14": row["day14"] if week_diff >= 2 else None,
                "days30": row["days30"] if week_diff >= 4 else None,
                "day60": row["day60"] if week_diff >= 8 else None,
                "day90": row["day90"] if week_diff >= 12 else None,
                "day180": row["day180"] if week_diff >= 26 else None,
                "day365": row["day365"] if week_diff >= 52 else None,
                "day365plus": row["day365plus"] if week_diff >= 52 else None,
            }
        else:
            row_date = datetime.strptime(row["_period"], "%Y-%m")
            month_diff = (today.year - row_date.year) * 12 + today.month - row_date.month
            processed_row = {
                "_period": row["_period"],
                "new_customer": row["new_customer"],
                "nrev": row["nrev"],
                "naov": row["naov"],
                "nltv": row["nltv"],
                "multiorder": row["multiorder"],
                "firstpurchase": row["firstpurchase"],
                "day7": row["day7"] if month_diff >= 1 else None,
                "day14": row["day14"] if month_diff >= 1 else None,
                "days30": row["days30"] if month_diff >= 1 else None,
                "day60": row["day60"] if month_diff >= 2 else None,
                "day90": row["day90"] if month_diff >= 3 else None,
                "day180": row["day180"] if month_diff >= 6 else None,
                "day365": row["day365"] if month_diff >= 12 else None,
                "day365plus": row["day365plus"] if month_diff >= 12 else None,
            }

        return processed_row
    
    data = [dict(zip(columns, row)) for row in result.fetchall()]
    result = [process_row(row, interval) for row in data]
    return result



@behaviour_bp.route('/campaigndetail', methods=['GET'])
@cross_origin(origins='*', methods=['GET'], headers=['Content-Type'])
def get_campaigndetails():

    headers = request.headers
    body = request.args

    startdate = body.get('startdate')
    enddate = body.get('enddate')
    userid = headers.get('workspaceId')
    channel = body.get('channel')

    if channel in ('Facebook', 'Google'):
        channel = channel.lower()
    tablename = f"{channel}ads_{userid}"
    sql_query = text(f"SELECT distinct on(campaignid) campaignid, campaign_name FROM {tablename} where dated >= :startdate and dated <= :enddate order by campaignid, dated desc")
    result = db.session.execute(sql_query, {
        'startdate': startdate, 
        'enddate': enddate
    })

    campaigns = [{"campaignid": row.campaignid, "campaign_name": row.campaign_name} for row in result]

    return campaigns