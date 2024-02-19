# connection.py
from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy

from mongoengine import connect

from flask_jwt_extended import JWTManager

import os
# from botocore.exceptions import ClientError

app = Flask(__name__)
app.url_map._rules_by_endpoint = {}
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('_SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = os.getenv('_SECRET_KEY')
# app.config.from_pyfile('config.py')

# PostgreSQL connection
db = SQLAlchemy()
jwt = JWTManager()


def get_db():
    if 'db' not in g:
        init_app(app)
        g.db = db.engine.connect()
    return g.db

def close_db(e=None):
    db = g.pop('db', None)

def create_app():
    return app

def init_app(app):
    db.init_app(app)
    if db is not None:
        db.close()

# def get_secret():

#     secret_name = "flask_ecs"
#     region_name = "ap-south-1"

#     # Create a Secrets Manager client
#     session = boto3.session.Session()
#     client = session.client(
#         service_name='secretsmanager',
#         region_name=region_name
#     )

#     try:
#         get_secret_value_response = client.get_secret_value(
#             SecretId=secret_name
#         )
#     except ClientError as e:
#         raise e

#     return get_secret_value_response['SecretString']


#initialize
db.init_app(app)
jwt.init_app(app)

# disconnect()
db_mongo = connect(host=os.environ.get('_MONGO_URI'))
# db = MongoEngine(app)
# MongoDB connection
# mongo = PyMongo(app)


