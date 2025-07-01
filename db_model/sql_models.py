# sql_models.py
# from connection import db
from ..connection import db
from datetime import datetime
import uuid, os
from sqlalchemy import MetaData, Table, Column, Integer, String, DateTime, Text, Numeric, Date, Boolean, ForeignKey
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.sql import func

# db = SQLAlchemy()

class UserRegister(db.Model):
    __tablename__ = "user_register"
    id = db.Column(db.Integer, primary_key=True)
    complete_name = db.Column(db.String(255))
    email = db.Column(db.String(64))
    phone = db.Column(db.String(16))
    _password = db.Column(db.String(255))
    workspace = db.Column(db.String(64), unique=True)
    productid = db.Column(db.String(16), unique=True)
    timezone = db.Column(db.String(128))
    timezone_value = db.Column(db.Numeric)
    company = db.Column(db.String(64))
    currency = db.Column(db.String(8))
    isverify = db.Column(db.Boolean, default=False)
    isactive = db.Column(db.Boolean, default=False)
    plan_till = db.Column(db.DateTime)
    product_type = db.Column(db.String(16))
    account_type = db.Column(db.String(16))
    subdomain = db.Column(db.String(16))
    agencyid = db.Column(db.Integer)
    isleadgen = db.Column(db.Boolean, default=False)
    tax_rate = db.Column(db.Numeric)
    tax_on = db.Column(db.Boolean, default=False)
    tag = db.Column(db.String(16))
    plan = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.now)
    last_activity = db.Column(db.DateTime, default=datetime.now)
    is_logout = db.Column(db.Boolean, default=True)

class UserSubdomain(db.Model):
    __tablename__ = "user_subdomain_list"
    id = db.Column(db.Integer, primary_key=True)
    subdomain = db.Column(db.String(16))
    status = db.Column(db.Boolean, default=False)


class AgencyRegister(db.Model):
    __tablename__ = "agency_register"
    id = db.Column(db.Integer, primary_key=True)
    complete_name = db.Column(db.String(255))
    email = db.Column(db.String(64))
    phone = db.Column(db.String(16))
    _password = db.Column(db.String(255))
    workspace = db.Column(db.String(64), unique=True)
    productid = db.Column(db.String(16), unique=True)
    timezone = db.Column(db.String(128))
    company = db.Column(db.String(128))
    currency = db.Column(db.String(8))
    isverify = db.Column(db.Boolean, default=False)
    isactive = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)



class ClientGoogleCredentials(db.Model):
    __tablename__ = "client_google_credentials"
    id = db.Column(db.Integer, primary_key=True)
    workspace = db.Column(db.String(64))
    _token = db.Column(db.String(255))
    account_name = db.Column(db.String(32))
    account = db.Column(db.String(32))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    manager_account = db.Column(db.String(32))
    

class RazorpayConfiguration(db.Model):
    __tablename__ = "payment_razorpay_config"
    id = db.Column(db.Integer, primary_key=True)
    workspace = db.Column(db.String(64))
    razorpay_api_secret = db.Column(db.String(128))
    razorpay_api_key = db.Column(db.String(128))
    razorpay_client_secret = db.Column(db.String(64))
    active = db.Column(db.Boolean, default=False)


class PlatformConfiguration(db.Model):
    __tablename__ = "platform_config"
    id = db.Column(db.Integer, primary_key=True)
    workspace = db.Column(db.String(64))
    platform = db.Column(db.String(64))
    active = db.Column(db.Boolean, default=False)


class InstaMojoConfiguration(db.Model):
    __tablename__ = "payment_instamojo_config"
    id = db.Column(db.Integer, primary_key=True)
    workspace = db.Column(db.String(64))
    active = db.Column(db.Boolean, default=False)

class ClientFacebookredentials(db.Model):
    __tablename__ = "client_facebook_credentials"
    id = db.Column(db.Integer, primary_key=True)
    workspace = db.Column(db.String(64))
    accesstoken = db.Column(db.Text)
    email = db.Column(db.String(128))
    userid = db.Column(db.String(32))
    expireon = db.Column(db.DateTime)
    account = db.Column(db.String(64))
    account_name = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class ClientLinkedinCredentials(db.Model):
    __tablename__ = "client_linkedin_credentials"
    id = db.Column(db.Integer, primary_key=True)
    workspace = db.Column(db.String(64))
    access_token = db.Column(db.Text)
    account = db.Column(db.String(32))
    account_name = db.Column(db.String(64))
    expire_in = db.Column(db.Date)
    active = db.Column(db.Boolean)
    refresh_token = db.Column(db.Text)
    refresh_token_expire_in = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

class ChatBotLog(db.Model):
    __tablename__ = "chatbot_query_log"
    id = db.Column(db.Integer, primary_key=True)
    workspace = db.Column(db.String(64))
    datetime = db.Column(db.DateTime, default=datetime.now)
    question = db.Column(db.Text)
    query = db.Column(db.Text)
    result = db.Column(db.Text)


class WooCommerce(db.Model):
    __tablename__ = "channel_woocommerce_integration"
    id = db.Column(db.Integer, primary_key=True)
    workspace = db.Column(db.String(64))
    client_secret = db.Column(db.String(128))
    active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class Shopify(db.Model):
    __tablename__ = "channel_shopify_integration"
    id = db.Column(db.Integer, primary_key=True)
    workspace = db.Column(db.String(64))
    base_url = db.Column(db.String(256))
    access_key = db.Column(db.String(128))
    active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

class Payment(db.Model):
    __tablename__ = "payment_request"
    id = db.Column(db.Integer, primary_key=True)
    completename = db.Column(db.String(32))
    email = db.Column(db.String(128))
    order_id = db.Column(db.String(32))
    currency = db.Column(db.String(8))
    total = db.Column(db.Numeric)
    link = db.Column(db.String(128))
    status = db.Column(db.String(16))
    transaction_id = db.Column(db.String(64))
    workspace = db.Column(db.String(64))
    expireon = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

class UTMSource(db.Model):
    __tablename__ = "utm_source"
    id = db.Column(db.Integer, primary_key=True)
    workspace = db.Column(db.String(64))
    productid = db.Column(db.String(16))
    utm_field = db.Column(db.String(64))
    value = db.Column(db.String(64))
    utm_sub_field = db.Column(db.String(64))
    displayname = db.Column(db.String(64))


class EmailChange(db.Model):
    __tablename__ = "change_email_vaildation"
    workspace = db.Column(db.String(32), primary_key=True)
    otp = db.Column(db.String(4))
    created_at = db.Column(db.DateTime, default=datetime.now)


class MongoMetric(db.Model):
    __tablename__ = "mongo_metric"
    id = db.Column(db.Integer, primary_key=True)
    dated = db.Column(db.Date)
    workspace = db.Column(db.String(32))
    productid = db.Column(db.String(16))
    metric = db.Column(db.String(16))
    value = db.Column(db.INTEGER)


class ProductTable(db.Model):
    __tablename__ = "product_table"
    id = db.Column(db.Integer, primary_key=True)
    workspaceid = db.Column(db.String(32))
    productid = db.Column(db.String(16))
    product_name = db.Column(db.String(128))
    cost_price = db.Column(db.NUMERIC)
    sale_price = db.Column(db.NUMERIC)


def order_table_dynamic(tablename):
    class OrderTable(db.Model):
        __tablename__ = tablename
        __table_args__ = {'extend_existing':True}
        id = db.Column(db.Integer, primary_key=True, autoincrement=True)
        order_date = db.Column(db.DateTime)
        transcation_id = db.Column(db.String(128), unique=True)
        first_name = db.Column(db.String(128))
        last_name = db.Column(db.String(128))
        email = db.Column(db.String(128))
        phone = db.Column(db.String(32))
        payment_method = db.Column(db.String(64))
        total = db.Column(db.Numeric)
        currency = db.Column(db.String(8))
        order_status = db.Column(db.String(32))
        event_type = db.Column(db.String(64))
        cart_id = db.Column(db.String(128))
        fbclid = db.Column(db.Text)
        customer_ip = db.Column(db.String(32))
        customer_user_agent = db.Column(db.Text)
        event_type = db.Column(db.String(32))
        thankyou_page = db.Column(db.Text)
        checkout_token = db.Column(db.String(64))
        first_stage_date = db.Column(db.DateTime)
        second_stage_date = db.Column(db.DateTime)
        converted_date = db.Column(db.DateTime)
        islead = db.Column(db.Boolean, default=False)
        created_at = db.Column(db.DateTime, default=datetime.now)
        updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
        email_encrypt = db.Column(BYTEA)
        phone_encrypt = db.Column(BYTEA)
        email_secure = db.Column(db.Text)
        phone_secure = db.Column(db.Text)
        notes = db.Column(db.Text)

        # @property
        # def decrypted_email(self,email):
        #     return db.session.query(func.pgp_sym_encrypt(email, os.environ.get('_ENCYPT_KEY'))).scalar()

        # @property
        # def decrypted_phone(self,phone):
        #     return db.session.query(func.pgp_sym_encrypt(phone, os.environ.get('_ENCYPT_KEY'))).scalar()
        

    return OrderTable
    



def ordertable(tablename):
    # Define a table with order name and columns
    metadata = MetaData(schema='public')
    order_table = Table(
			tablename,
			metadata,
			Column('id', Integer, primary_key=True, autoincrement=True),
            Column('channel', String(32)),
			Column('order_date', DateTime),
			Column('transcation_id', String(128), unique=True),
			Column('first_name', String(128)),
			Column('last_name', String(128)),
			Column('email', String(128)),
            Column('phone', String(32)),
            Column('cart_id', String(128)),
            Column('fbclid', Text),
			Column('payment_method', String(64)),
            Column('total', Numeric),
            Column('currency', String(8)),
            Column('order_status', String(32)),
			Column('customer_ip', String(64)),
			Column('customer_user_agent', Text),
            Column('thankyou_page', Text),
            Column('checkout_token', String(64)),
            Column('first_stage_date', DateTime),
            Column('second_stage_date', DateTime),
            Column('converted_date', DateTime),
            Column('islead', Boolean, default=False),
            Column('event_type', String(32)),
			Column('created_at', DateTime, default=datetime.now),
			Column('updated_at', DateTime, default=datetime.now, onupdate=datetime.now),
            Column('email_encrypt', BYTEA),
            Column('phone_encrypt', BYTEA),
            Column('email_secure', Text),
            Column('phone_secure', Text),
            Column('notes', Text)
		)
    return order_table



def orderlinetable(tablename):
    # Define a table with order name and columns
    metadata = MetaData(schema='public')
    orderline_table = Table(
			tablename,
			metadata,
			Column('order_id', Integer, primary_key=True),
			Column('shopify_productid', Integer),
			Column('sku', String(128), unique=True),
            Column('product_name', String(255)),
			Column('quantity', Integer),
			Column('price', Numeric),
			Column('variant_title', String(128)),
            Column('cost', Numeric)
		)
    return orderline_table


def googleads_table(tablename):
    # Define a table with googleads name and columns
    metadata = MetaData(schema='public')
    googleads_table = Table(
			tablename,
			metadata,
            Column('dated', Date),
            Column('account', String(32)),
            Column('account_name', String(64)),
            Column('campaignid', String(32)),
			Column('campaign_name', String(128)),
            Column('campaign_status', String(32)),
			Column('adsetid', String(32)),
            Column('adset_name', String(128)),
            Column('adset_status', String(32)),
            Column('adid', String(32)),
            Column('ad_name', String(128)),
            Column('ad_status', String(32)),
            Column('impression', Integer),
            Column('clicks', Integer),
            Column('spend', Numeric),
            Column('purchase', Integer),
            Column('purchase_value', Numeric),
            Column('purchase_roas', Numeric),
			Column('created_at', DateTime, default=datetime.now),
			Column('updated_at', DateTime, default=datetime.now, onupdate=datetime.now),
            UniqueConstraint('dated', 'adid', name=uuid.uuid4().hex)
		)
    return googleads_table


def facebookads_table(tablename):
    # Define a table with googleads name and columns
    metadata = MetaData(schema='public')
    facebookads_table = Table(
			tablename,
			metadata,
            Column('dated', Date),
            Column('account', String(32)),
            Column('account_name', String(64)),
            Column('campaignid', String(32)),
			Column('campaign_name', String(128)),
            Column('campaign_status', String(32)),
			Column('adsetid', String(32)),
            Column('adset_name', String(128)),
            Column('adset_status', String(32)),
            Column('adid', String(32)),
            Column('ad_name', String(128)),
            Column('ad_status', String(32)),
            Column('impression', Integer),
            Column('clicks', Integer),
            Column('spend', Numeric),
            Column('purchase_roas', Numeric),
            Column('purchase', Integer),
			Column('created_at', DateTime, default=datetime.now),
			Column('updated_at', DateTime, default=datetime.now, onupdate=datetime.now),
            UniqueConstraint('dated', 'adid', name=uuid.uuid4().hex)
		)
    return facebookads_table



def otherads_table(tablename):
    # Define a table with googleads name and columns
    metadata = MetaData(schema='public')
    otherads_table = Table(
			tablename,
			metadata,
            Column('channel', String(64)),
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
            Column('purchase_roas', Numeric),
            Column('purchase', Integer),
			Column('created_at', DateTime, default=datetime.now),
			Column('updated_at', DateTime, default=datetime.now, onupdate=datetime.now),
            UniqueConstraint('channel','dated', 'adid', name=uuid.uuid4().hex)
		)
    return otherads_table


def facebookcreative_table(tablename):
    metadata = MetaData(schema='public')
    facebookcreative_table = Table(
			tablename,
			metadata,
            Column('dated', Date),
            Column('account', String(32)),
            Column('account_name', String(64)),
            Column('adid', String(32)),
			Column('ad_name', String(128)),
			Column('adsetid', String(32)),
            Column('campaignid', String(32)),
            Column('frequency', Integer),
            Column('impression', Integer),
            Column('reach', Integer),
            Column('spend', Numeric),
            Column('clicks', Integer),
            Column('creative_id', String(32)),
            Column('creative_name', Text),
            Column('status', String(16)),
            Column('created_time', DateTime),
            Column('engagement', Integer),
            Column('video_view_3s', Integer),
            Column('video_p25_watched_actions', Integer),
            Column('video_p50_watched_actions', Integer),
            Column('video_p100_watched_actions', Integer),
            Column('video_30_sec_watched_actions', Integer),
            Column('video_thruplay_watched_actions', Integer),
            Column('ad_copy', Text),
            Column('ad_type', String(16)),
            Column('thumbnail_url', Text),
            Column('preview_shareable_link', Text),
            Column('video_length', Numeric),
            Column('preview', Text),
            Column('purchase', Integer),
            UniqueConstraint('dated', 'adid', name=uuid.uuid4().hex)
		)
    return facebookcreative_table


class CustomizeColumn(db.Model):
    __tablename__ = "customize_column"
    id = db.Column(db.Integer, primary_key=True)
    workspaceid = db.Column(db.String(32))
    report = db.Column(db.String(32))
    field = db.Column(db.String(64))
    seq = db.Column(db.INTEGER)
    custom_formula = db.Column(db.Text)
    is_custom_column = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(64))
    is_custom_used = db.Column(db.Boolean, default=False)
    custom_id = db.Column(db.String(32))
    view_name = db.Column(db.String(64))
    # latest_view = db.Column(db.Boolean, default=False)
