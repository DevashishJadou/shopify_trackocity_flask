from pymongo import MongoClient
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
# from langchain_anthropic import ChatAnthropic
from typing import Dict, List, Optional
import json, os
from datetime import datetime

from ..db_model.sql_models import *
from sqlalchemy import MetaData


from flask import Blueprint, jsonify, request
from flask_cors import cross_origin


chatbot_cd = Blueprint('chatbot', __name__)



class MongoDBAnalyst:
    def __init__(self, mongodb_uri: str, db_name: str, collection_name: str, openai_api_key: str):
        """Initialize MongoDB connection and LangChain components."""
        # MongoDB setup
        self.client = MongoClient(mongodb_uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        
        # LangChain setup with system message support
        self.llm = ChatOpenAI(api_key=openai_api_key, model="gpt-3.5-turbo")
        # For Claude:
        # self.llm = ChatAnthropic(
        #     anthropic_api_key=openai_api_key,
        #     model="claude-3-sonnet-20240229",
        #     temperature=0
        # )

        # Define system message template
        system_template = """You are a specialized MongoDB query generator for Trackocity's analytics platform. Your role is to generate precise MongoDB aggregation pipelines based on user questions and the provided schema.
        SCHEMA CONTEXT:
        {schema}

        KEY FIELD DEFINITIONS:
        1. Session Tracking:
        - "session": Browser-level unique identifier
        - "localsession": General session identifier
        - "body.setSession": Binary (1 = new user, 0 = returning)

        2. User Identification:
        - "body.visitorid": Device-level persistent identifier

        3. Time and Events:
        - "creation_at": Event timestamp
        - "body.pageLoad": Pageview indicator (1)

        4. URL and Navigation:
        - "body.currenturlparams.urlDetails.url": Current URL
        - "body.currenturlparams.urlparams": UTM tracking
        - "body.navigatordetails.deviceType": Device information
        - "body.navigatordetails.userAgentInfo": User agent details

        5. Activity Tracking:
        - "body.setCart": Cart action indicator (1 = added)

        DATE HANDLING REQUIREMENTS:
        1. Always use simple "YYYY-MM-DD" format in queries
        2. For $dateToString operations, use:
        {{"$dateToString": {{"format": "%Y-%m-%d", "date": "$creation_at"}}}}
        3. Never use ISODate() or full ISO timestamps
        4. For date grouping, use:
        - Daily: "%Y-%m-%d"
        - Monthly: "%Y-%m"
        - Yearly: "%Y"
        - Hourly: Use additional $hour operator in grouping

        QUERY REQUIREMENTS:
        1. Mandatory filters:
        - "body.pageLoad": 1
        - "productid": [specified value]
        2. Return: Valid JSON array only
        3. Sorting: Chronological by default
        4. Time-series: Group by appropriate time unit

        Your task is to:
        1. Analyze the user's question
        2. Apply mandatory filters
        3. Use proper date formatting
        4. Implement correct aggregation stages
        5. Ensure proper sorting
        6. Return only the MongoDB query array

        Example Date Handling:
        [
            {{
                "$match": {{
                    "creation_at": {{
                        "$gte": "2024-01-01",
                        "$lte": "2024-01-31"
                    }}
                }}
            }},
            {{
                "$group": {{
                    "_id": {{"$dateToString": {{"format": "%Y-%m-%d", "date": "$creation_at"}}}},
                    "count": {{"$sum": 1}}
                }}
            }}
        ]"""

        human_template = """Generate a MongoDB aggregation pipeline, no explaining text. Always return only the MongoDB query as a valid JSON array for this question: {question}"""

        # Create message templates
        self.system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
        self.human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

        # Combine into chat prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            self.system_message_prompt,
            self.human_message_prompt
        ])

        self.output_parser = StrOutputParser()
        
        # Create the chain with system context
        self.chain = (
            {"schema": RunnablePassthrough(), "question": RunnablePassthrough()}
            | self.prompt
            | self.llm
            | self.output_parser
        )

    def get_schema(self, productid: int) -> Optional[List[Dict]]:
        """Get schema from MongoDB based on productid."""
        try:
            query = {
                "productid": productid,
                "body.pageLoad": 1
            }
            
            # Get sample document
            sample_document = self.collection.find_one(query, sort=[("creation_at", -1)])
            
            if not sample_document:
                return None
            
            # Create schema information including nested fields
            def extract_schema(obj, prefix=""):
                schema = []
                for key, value in obj.items():
                    full_key = f"{prefix}.{key}" if prefix else key
                    if isinstance(value, dict):
                        schema.extend(extract_schema(value, full_key))
                    else:
                        schema.append({
                            "column_name": full_key,
                            "data_type": type(value).__name__
                        })
                return schema
            
            return extract_schema(sample_document)
            
        except Exception as e:
            print(f"Error getting schema: {str(e)}")
            return None

    
    def convert_dates_in_query(self, query):
        """
        Recursively convert any date strings in the query to datetime objects.
        Handles both single queries and aggregation pipelines.
        """
        if isinstance(query, list):
            # Handle aggregation pipeline
            return [self.convert_dates_in_query(stage) for stage in query]
            
        elif isinstance(query, dict):
            converted_query = {}
            for key, value in query.items():
                if isinstance(value, dict):
                    # Recursively handle nested dictionaries
                    converted_query[key] = self.convert_dates_in_query(value)
                elif isinstance(value, list):
                    # Handle lists of values
                    converted_query[key] = [self.convert_dates_in_query(item) if isinstance(item, dict) else item for item in value]
                elif isinstance(value, str) and key in ['$gte', '$lte', '$gt', '$lt']:
                    # Convert date string to datetime for comparison operators
                    try:
                        converted_query[key] = datetime.strptime(value, "%Y-%m-%d")
                    except ValueError:
                        converted_query[key] = value
                else:
                    converted_query[key] = value
            return converted_query
        else:
            return query

    
    def generate_and_run_query(self, question: str, productid: int) -> Dict:
        """Generate and execute MongoDB query based on user question."""
        try:
            # Get schema
            # schema = self.get_schema(productid)
            schema = [{'column_name': '_id', 'data_type': 'ObjectId'}, {'column_name': 'session', 'data_type': 'str'}, {'column_name': 'productid', 'data_type': 'float'}, {'column_name': 'creation_at', 'data_type': 'datetime'}, {'column_name': 'localsession', 'data_type': 'str'}, {'column_name': 'body.sessionid', 'data_type': 'str'}, {'column_name': 'body.visitorid', 'data_type': 'str'}, {'column_name': 'body.navigatordetails.userAgentInfo', 'data_type': 'str'}, {'column_name': 'body.navigatordetails.isOnline', 'data_type': 'bool'}, {'column_name': 'body.navigatordetails.isCookiesEnabled', 'data_type': 'bool'}, {'column_name': 'body.navigatordetails.language', 'data_type': 'str'}, {'column_name': 'body.navigatordetails.deviceType', 'data_type': 'str'}, {'column_name': 'body.navigatordetails.timezoneOffset', 'data_type': 'int'}, {'column_name': 'body.navigatordetails.ipaddress', 'data_type': 'str'}, {'column_name': 'body.fbcookie.fbcookieeid', 'data_type': 'NoneType'}, {'column_name': 'body.fbcookie.fbc', 'data_type': 'NoneType'}, {'column_name': 'body.fbcookie.fbp', 'data_type': 'str'}, {'column_name': 'body.cartid', 'data_type': 'NoneType'}, {'column_name': 'body.currenturlparams.urlDetails.url', 'data_type': 'str'}, {'column_name': 'body.currenturlparams.urlparams', 'data_type': 'str'}, {'column_name': 'body.currenturlparams.prevpagedetails', 'data_type': 'str'}, {'column_name': 'body.pageLoad', 'data_type': 'int'}, {'column_name': 'body.cart', 'data_type': 'NoneType'}, {'column_name': 'body.setCart', 'data_type': 'int'}, {'column_name': 'body.setSubmit', 'data_type': 'int'}, {'column_name': 'body.setSession', 'data_type': 'int'}, {'column_name': 'body.fingerprint', 'data_type': 'str'}]

            if not schema:
                return {"error": "No data found for the given query"}
            
            # Generate query using LangChain
            query_str = self.chain.invoke({
                "productid" : productid,
                "schema": json.dumps(schema, indent=2),
                "question": question
            })

            print(f'query:{query_str}')
            # Parse the generated query string into a MongoDB query object
            try:
                mongo_query = json.loads(query_str)
            except json.JSONDecodeError:
                return {"error": "Failed to parse generated query"}
            
            mongo_query = self.convert_dates_in_query(mongo_query)
            # Execute query
            if isinstance(mongo_query, dict):
                # result = list(self.collection.find(mongo_query))
                mongo_query = [mongo_query]
            # elif isinstance(mongo_query, list):  # For aggregation pipelines
            #     result = list(self.collection.aggregate(mongo_query))
            # else:
            #     return {"error": "Invalid query format"}
            # result = list(CustomerInfoHis.objects.aggregate(*mongo_query))
            result = list(self.collection.aggregate(mongo_query))
            
            return {
                "query": mongo_query,
                "result": result
            }
            
        except Exception as e:
            return {"error": f"Query execution failed: {str(e)}"}



@chatbot_cd.route('/website', methods=['POST', 'OPTIONS'])
@cross_origin(origins='*', methods=['POST', 'OPTIONS'], headers=['Content-Type'])
def chatwithwebsite():

    headers = request.headers
    userid = headers.get('workspaceId')
    user = UserRegister.query.filter_by(workspace = userid).first()
    body = json.loads(request.data)
    
    # Configuration
    mongodb_uri = os.environ.get('_MONGO_URI')
    db_name = "trackocity_history"
    collection_name = "customer_info"
    openai_api_key = os.environ.get('_OPENAI_KEY_MONGO') 
    # openai_api_key = "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"
    
    # Initialize the analyst
    analyst = MongoDBAnalyst(mongodb_uri, db_name, collection_name, openai_api_key)
    
    # Example usage
    productid = int(user.productid)
    question = body.get('question')
    
    # Get response
    response = analyst.generate_and_run_query(question, productid)
    
    # Print results
    if "error" in response:
        return jsonify(response['error'])
    else:
        return jsonify(response["result"])

