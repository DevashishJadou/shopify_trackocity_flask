# connection.py
from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail

from mongoengine import connect

from flask_jwt_extended import JWTManager

import os



app = Flask(__name__)
app.url_map._rules_by_endpoint = {}
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('_SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = os.environ.get('_SQLALCHEMY_ECHO')
app.config['SQLALCHEMY_POOL_SIZE'] = 10
app.config['SQLALCHEMY_MAX_OVERFLOW'] = 20
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 30
app.config['SQLALCHEMY_POOL_RECYCLE'] = 1800
app.config['SQLALCHEMY_POOL_PRE_PING'] = True
app.config['JWT_SECRET_KEY'] = os.environ.get('_JWT_SECRET_KEY')
app.config['SECRET_KEY'] = os.environ.get('_SECRET_KEY_FLASK')

app.config['MAIL_SERVER'] = 'smtp.gmail.com' 
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('_MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('_MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('_MAIL_USERNAME')

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


#initialize
db.init_app(app)
jwt.init_app(app)
mail = Mail(app)


db_mongo = connect(host=os.environ.get('_MONGO_URI'))
# db = MongoEngine(app)
# MongoDB connection
# mongo = PyMongo(app)


