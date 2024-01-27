# connection.py
from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy

from flask_mongoengine import MongoEngine
from mongoengine import connect, disconnect

from flask_pymongo import PyMongo

from flask_jwt_extended import JWTManager


app = Flask(__name__)
app.url_map._rules_by_endpoint = {}
app.config.from_pyfile('config.py')

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

# disconnect()
db_mongo = connect(host=app.config['MONGO_URI'])
# db = MongoEngine(app)
# MongoDB connection
# mongo = PyMongo(app)


