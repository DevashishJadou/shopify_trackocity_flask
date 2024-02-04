# config.py
from datetime import timedelta

SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = True
SQLALCHEMY_DATABASE_URI = 'postgresql://dbeditor:aPk3ClBYXa@10.0.12.64:5432/template1'
MONGO_URI = 'mongodb://10.0.12.64:27017/test'
SECRET_KEY = 'your_secret_key'

JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
JWT_SECRET_KEY = 'a824306622db4766cd5a93c2'