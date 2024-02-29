# models/mongo_models.py

import mongoengine as me
from mongoengine import Document, StringField, FloatField, DateTimeField
from datetime import datetime

class Fingerprint(me.Document):
    session = me.StringField()
    visitorid = me.StringField()
    productid = me.FloatField()
    creation_at = me.DateTimeField(default=datetime.now)
    localsession = me.StringField()

class CustomerInfo(me.Document):
    session = me.StringField()
    productid = me.FloatField()
    creation_at = me.DateTimeField(default=datetime.now)
    localsession = me.StringField()
    body = me.DictField()



class Error(me.Document):
    session = me.StringField()
    productid = me.FloatField()
    error = me.StringField()

