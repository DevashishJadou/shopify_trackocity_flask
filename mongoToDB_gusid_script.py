import pymongo
import psycopg2
from mongoengine import Document, connect, StringField, IntField

from datetime import datetime, timedelta

# MongoDB Connection
mongo_client = pymongo.MongoClient("mongodb://43.205.70.36:27017/")
mongo_db = mongo_client["test"]
mongo_collection = mongo_db["customer_infoext"]

# PostgreSQL Connection
postgres_connection_string = "dbname=template1 user=dbeditor password=aPk3ClBYXa host=43.205.70.36"
postgres_conn = psycopg2.connect(postgres_connection_string)
postgres_cursor = postgres_conn.cursor()

# Calculate the timestamp for one hour ago
one_hour_ago = datetime.utcnow().replace(microsecond=0) - timedelta(hours=108)


# Define the datetime object for "2024-01-20T09:32:00Z"
# iso_date = datetime(2024, 1, 20, 9, 32, 0)

# Create the query with "$gte" operator
query = {
    "creation_at": {
        "$gte": one_hour_ago
    }
}
result = mongo_collection.find(query)

# Query MongoDB for documents created in the last hour
# recent_mongo_docs = mongo_collection.find({"created_at": {"$gt": one_hour_ago_iso}})
# recent_mongo_docs = mongo_collection.find({"productid":{"$eq":1235689}})


# Iterate over MongoDB documents and store in PostgreSQL
for mongo_doc in result:
    print(mongo_doc)
    creation_at = mongo_doc['creation_at'].strftime("%Y-%m-%d %H:%M:%S")
    customerInfo = mongo_doc['body']['customerInfo']
    email = customerInfo.get('email')
    if email:
        firstname = customerInfo.get('first_name')
        lastname = customerInfo.get('surname')
        phone = customerInfo.get('phone')
        # Insert the data into PostgreSQL
        postgres_cursor.execute(
            "INSERT INTO visitor_form (sessionid, productid, email, firstname, lastname, phone, event_time) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (mongo_doc['session'], str(int(mongo_doc['productid'])), email, firstname, lastname, phone, creation_at),
        )
postgres_conn.commit()

# Close connections
mongo_client.close()
postgres_conn.close()
