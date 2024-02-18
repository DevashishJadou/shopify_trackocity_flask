# sql_models.py
# from connection import db
from ..connection import db
from datetime import datetime
from sqlalchemy import MetaData, Table, Column, Integer, String, DateTime, Text, Numeric, Date
from sqlalchemy.schema import UniqueConstraint

# db = SQLAlchemy()

class UserRegister(db.Model):
    __tablename__ = "user_register"
    id = db.Column(db.Integer, primary_key=True)
    complete_name = db.Column(db.String(255))
    email = db.Column(db.String(64))
    phone = db.Column(db.String(16))
    _password = db.Column(db.String(255))
    workspace = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class ClientGoogleCredentials(db.Model):
    __tablename__ = "client_google_credentials"
    id = db.Column(db.Integer, primary_key=True)
    workspace = db.Column(db.String(64))
    _token = db.Column(db.String(255))
    account_name = db.Column(db.String(32))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    

class RazorpayConfiguration(db.Model):
    __tablename__ = "payment_razorpay_config"
    id = db.Column(db.Integer, primary_key=True)
    workspace = db.Column(db.String(64))
    razorpay_api_secret = db.Column(db.String(128))
    razorpay_api_key = db.Column(db.String(128))
    razorpay_client_secret = db.Column(db.String(64))


class ClientFacebookredentials(db.Model):
    __tablename__ = "client_facebook_credentials"
    id = db.Column(db.Integer, primary_key=True)
    workspace = db.Column(db.String(64))
    _token = db.Column(db.String(255))
    email = db.Column(db.String(128))
    userid = db.Column(db.String(32))
    expireon = db.Column(db.DateTime)
    account = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)



# class WooCommerce(db.Model):
#     __tablename__ = "woo_commerce_order"
#     id = db.Column(db.Integer, primary_key=True)
#     workspace = db.Column(db.String(64))
#     order_date = db.Column(db.DateTime)
#     transcation_id = db.Column(db.String(128))
#     first_name = db.Column(db.String(128))
#     last_name = db.Column(db.String(128))
#     email = db.Column(db.String(128))
#     payment_method = db.Column(db.String(64))
#     total = db.Column(db.Numeric)
#     customer_ip = db.Column(db.String(32))
#     customer_user_agent = db.Column(db.Text)
#     created_at = db.Column(db.DateTime, default=datetime.now)
#     updated_at = db.Column(db.DateTime, default=datetime.now)


class WooCommerce(db.Model):
    __tablename__ = "channel_woocommerce_integration"
    id = db.Column(db.Integer, primary_key=True)
    workspace = db.Column(db.String(64))
    client_secret = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class Shopify(db.Model):
    __tablename__ = "channel_shopify_integration"
    id = db.Column(db.Integer, primary_key=True)
    workspace = db.Column(db.String(64))
    base_url = db.Column(db.String(256))
    access_key = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


def order_table_dynamic(tablename):
    class OrderTable(db.Model):
        __tablename__ = tablename
        __table_args__ = {'extend_existing':True}
        id = db.Column(db.Integer, primary_key=True)
        order_date = db.Column(db.DateTime)
        transcation_id = db.Column(db.String(128))
        first_name = db.Column(db.String(128))
        last_name = db.Column(db.String(128))
        email = db.Column(db.String(128))
        payment_method = db.Column(db.String(64))
        total = db.Column(db.Numeric)
        customer_ip = db.Column(db.String(32))
        customer_user_agent = db.Column(db.Text)

    return OrderTable
    


# class OrderTable(db.Model):
#     # __tablename__ = tablename
#     id = db.Column(db.Integer, primary_key=True)
#     order_date = db.Column(db.DateTime)
#     transcation_id = db.Column(db.String(128))
#     first_name = db.Column(db.String(128))
#     last_name = db.Column(db.String(128))
#     email = db.Column(db.String(128))
#     payment_method = db.Column(db.String(64))
#     customer_ip = db.Column(db.String(32))
#     customer_user_agent = db.Column(db.String(128))

# def order_table_dynamic(tablename):
#         class DynamicOrderTable(OrderTable):
#             __tablename__ = tablename
#             extend_existing = True

#         return DynamicOrderTable()


    
    


def ordertable(tablename):
    # Define a table with order name and columns
    metadata = MetaData()
    order_table = Table(
			tablename,
			metadata,
			Column('id', Integer, primary_key=True),
            Column('channel', String(32)),
			Column('order_date', DateTime),
			Column('transcation_id', String(128)),
			Column('first_name', String(128)),
			Column('last_name', String(128)),
			Column('email', String(128)),
			Column('payment_method', String(64)),
            Column('total', Numeric),
			Column('customer_ip', String(32)),
			Column('customer_user_agent', Text),
			Column('created_at', DateTime, default=datetime.now),
			Column('updated_at', DateTime, default=datetime.now, onupdate=datetime.now)
		)
    return order_table


def googleads_table(tablename):
    # Define a table with googleads name and columns
    metadata = MetaData()
    googleads_table = Table(
			tablename,
			metadata,
            Column('dated', Date),
            Column('account', String(32)),
            Column('account_name', String(64)),
            Column('campaignid', String(32)),
			Column('campaign_name', String(128)),
			Column('adgroupid', String(32)),
            Column('adgroup_name', String(128)),
            Column('adid', String(32)),
            Column('ad_name', String(128)),
            Column('impression', Integer),
            Column('clicks', Integer),
            Column('spend', Numeric),
			Column('created_at', DateTime, default=datetime.now),
			Column('updated_at', DateTime, default=datetime.now, onupdate=datetime.now)
		)
    return googleads_table


def facebookads_table(tablename):
    # Define a table with googleads name and columns
    metadata = MetaData()
    facebookads_table = Table(
			tablename,
			metadata,
            Column('dated', Date),
            Column('account', String(32)),
            Column('account_name', String(64)),
            Column('campaignid', String(32)),
			Column('campaign_name', String(128)),
			Column('adsetid', String(32)),
            Column('adset_name', String(128)),
            Column('adid', String(32)),
            Column('ad_name', String(128)),
            Column('impression', Integer),
            Column('clicks', Integer),
            Column('spend', Numeric),
			Column('created_at', DateTime, default=datetime.now),
			Column('updated_at', DateTime, default=datetime.now, onupdate=datetime.now),
            UniqueConstraint('dated', 'adid', name='unique_dated_adid')
		)
    return facebookads_table

