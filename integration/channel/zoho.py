from flask import request, jsonify
import json, os
import requests
from datetime import datetime, timedelta
from flask_cors import cross_origin
from .woocommerce import channel_bp

from ...db_model.sql_models import UserRegister, PlatformConfiguration, order_table_dynamic, ordertable, ordertable_detail
from ...connection import db
from sqlalchemy import MetaData
from sqlalchemy import text


metadata = MetaData()

ACCOUNTS_URL = 'https://accounts.zoho.in'
API_URL = 'https://www.zohoapis.in'


def generate_zoho_refresh_token(client_id, client_secret, grant_code):
    """Generate refresh token when user first connects Zoho CRM"""
    
    token_url = f"{ACCOUNTS_URL}/oauth/v2/token"
    
    try:
        response = requests.post(
            token_url,
            params={
                'code': grant_code,
                'client_id': client_id,
                'client_secret': client_secret,
                'grant_type': 'authorization_code'
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get('refresh_token')
        else:
            print(f"Failed to get token. Status: {response.status_code}, Response: {response.text}")
            return None
    except Exception as e:
        print(f"Error getting token: {str(e)}")
        return None


@channel_bp.route('/zohointegration', methods=['POST'])
@cross_origin()
def zohointegration():
    data = json.loads(request.get_data().decode("utf-8"))
    client_id = data.get('client_id')
    client_secret = data.get('client_secret')
    grant_code = data.get('grant_code')
    modules = data.get('modules')  
    workspace = request.headers.get('workspaceId')
    
    if not all([client_id, client_secret, grant_code, workspace]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if not modules:
        return jsonify({'error': 'Please select at least one module'}), 400
    
    # Generate refresh token
    refresh_token = generate_zoho_refresh_token(client_id, client_secret, grant_code)
    if not refresh_token:
        return jsonify({'error': 'Something went wrong. Please verify your credentials and try again.'}), 400
    
    # Check if config exists
    existing = db.session.execute(
        text("SELECT id FROM platform_config WHERE workspace = :workspace AND platform = 'zoho_crm'"),{'workspace': workspace}).fetchone()
    
    if existing:
        db.session.execute(
            text("""
                UPDATE platform_config 
                SET client_id = :client_id,
                    client_secret = :client_secret,
                    refresh_token = :refresh_token,
                    modules = :modules,
                    active = TRUE
                WHERE workspace = :workspace AND platform = 'zoho_crm'
            """),
            {
                'workspace': workspace,
                'client_id': client_id,
                'client_secret': client_secret,
                'refresh_token': refresh_token,
                'modules': modules  
            }
        )
        db.session.commit()
        return jsonify({'message': 'Information Updated Successfully'}), 200
    
    else:
        # Insert new config
        db.session.execute(
            text("""
                INSERT INTO platform_config 
                (workspace, platform, client_id, client_secret, refresh_token, modules, active)
                VALUES (:workspace, 'zoho_crm', :client_id, :client_secret, :refresh_token, :modules, TRUE)
            """),
            {
                'workspace': workspace,
                'client_id': client_id,
                'client_secret': client_secret,
                'refresh_token': refresh_token,
                'modules': modules  
            }
        )
        db.session.commit() 
        
        try:
            tablename = 'order_' + workspace
            ordertabledetailtablename = 'order_detailed_' + workspace
            
            if not metadata.tables.get(tablename):
                zoho_table = ordertable(tablename)
                ordertable_detail_table = ordertable_detail(ordertabledetailtablename)
                
                try:
                    zoho_table.create(bind=db.engine)
                except Exception as e:
                    print(f'Error order table creation: {e.args}')
                
                try:
                    ordertable_detail_table.create(bind=db.engine)
                except Exception as e:
                    print(f'Error order_detailed table creation: {e.args}')
        
        except Exception as e:
            print(f'Zoho integration error: {e}')
            return jsonify({'error': 'Something went Wrong'}), 500
    
    return jsonify({'message': 'success'}), 200