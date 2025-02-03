from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough
from sqlalchemy import text

from decimal import Decimal
from datetime import datetime, date
import json, os, re

from ..db_model.sql_models import *
from .mongo_bot import chatbot_cd

from flask import Blueprint, jsonify, request
from flask_cors import cross_origin


def custom_json_serializer(obj):
    if isinstance(obj, (datetime, date)):
        # Convert datetime to ISO format string
        return obj.isoformat()
    if isinstance(obj, Decimal):
        # Convert Decimal to float
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

def jsonify_with_decimal(data):
    """Convert data containing Decimal objects to JSON."""
    return json.dumps(data, default=custom_json_serializer)

def row_to_dict(row):
    """Convert SQLAlchemy Row object to dictionary."""
    if hasattr(row, '_asdict'):
        return row._asdict()
    elif hasattr(row, '__dict__'):
        return row.__dict__
    else:
        return dict(enumerate(row))

class SmartQueryHandler:
    def __init__(self, openai_api_key):
        self.openai_api_key = openai_api_key
        self.llm = ChatOpenAI(openai_api_key=openai_api_key, temperature=0.1, top_p=0.7, frequency_penalty=0.2,presence_penalty=0)
        
        # Classifier system template
        self.classifier_template = """You are a query classifier that determines whether a question requires database access or can be answered directly.

            For questions that need database access, they should:
            1. Ask about specific metrics, data, or analytics
            2. Reference business data, customer information, or performance metrics
            3. Require calculations or aggregations
            4. Need historical data analysis
            5. Ask about ad performance, customer journey, or revenue metrics

            Questions that don't need database access:
            1. General knowledge questions
            2. Greetings or casual conversation
            3. Questions about common facts
            4. Questions about your capabilities
            5. Non-business related queries

            Please classify the question and provide a structured response.

            Question: {question}

            Respond in the following JSON format:
            {{
                "needs_database": boolean,
                "reason": "Brief explanation of classification",
                "response": "Direct response if no database needed, otherwise null"
            }}
            """

    def classify_question(self, question):
        """Determine if the question needs database access"""
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(self.classifier_template)
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        
        result = chain.invoke({"question": question})
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {
                "needs_database": True,
                "reason": "Classification failed, defaulting to database query",
                "response": None
            }

    def get_query_template(self):
        return """You are a specialized SQL Query Bot designed to help marketing analysts evaluate performance and make data-driven decisions. Your primary role is to generate valid PostgreSQL queries that answer specific marketing-related questions while considering key performance metrics and business needs, based on the provided schema and requirements.
                    
            Schema Information:
            {schema}
            
            Question: {question}
            
            Internal Reasoning (Chain of Thought):
            1. First, think step by step about which tables, columns, and filters to use.
            2. Then, provide only the final SQL query as your answer, without revealing your internal reasoning.

            Available Tables and Key Metrics:  
            1. horizon.ads_lastattribute
               - Stores last-touch attribution data, conversions, and campaign performance metrics.     
            2. horizon.ads_firstattribute
               - Stores first-touch attribution data, revenue, and order metrics.
            3. horizon.customer_journey
                - orderid consider as foreign key from horizon.ads_lastattribute or horizon.ads_firstattribute
                - customer journey analysis includes the paths and touchpoints where users or customers arrive on the website from various sources
                - Use workspace and orderid combination to join with horizon.ads_lastattribute or horizon.ads_firstattribute
            
            
            Column Defination:
            1. purchase/order: Number of orders/sales
            2. purchase_value/total/revenue: Total/revenue value of orders/sales
                
            Query Requirements: 
            1. Workspace Filter: Always include `workspace = '{workspace}'` in the `WHERE` clause.  
            2. Date Range:  
                - Filter on `order_date`.  
                - If no date range is specified, default to the last 6 months.  
            3.Prefix: Use `horizon.` as the schema prefix for all tables.  
            4. Aggregations and Metrics:  
                - Use `SUM`, `AVG`, `ROUND(..., 2)`, and `NULL IF` to avoid division by zero or NULL values.  
                - Group by relevant dimensions (e.g., campaign_name, channel, month).  
            5. Performance:  
                - If needed, use subqueries for clarity.  
                - Ensure you only output the final SQL query—no explanations or step-by-step logic.

            
            Key Marketing Performance Metrics:
            When generating queries, focus on metrics that matter most to marketing analysts:
            1. ROAS (Return on Ad Spend)
            2. CTR (Click-Through Rate
            3. CR (Conversion Rate)
            4. CPA (Cost Per Acquisition)
            5. CPM (Cost Per Impression)
            6. CPC (Cost Per Click)
            7. Impressions
            8. Time to Conversion
            9. Revenue Attribution
            10. Adtype
            Structure your queries to help evaluate performance and guide decision-making (e.g., identifying top-performing channels, optimizing spend, tracking conversions over time).
            

            Example:
            1. question: Analysis sept 2024 campaign for facebook platform and give suggestion to Improve ROAS
               SQL Query: SELECT
                        date_trunc('month', al.orderdate) AS month,
                        al.campaign_name AS campaign_name,
                        ROUND(SUM(al.total),2) AS total_revenue,
                        ROUND(SUM(al.spend),2) AS total_spend,
                        SUM(al.orders) AS tota_order,
                        ROUND(AVG(al.purchase_roas), 2) AS roas
                        FROM
                        horizon.ads_lastattribute al
                        WHERE
                        al.channel = 'facebook'
                        AND al.workspace = '854e249d718e42cba341aa0559931c12'
                        AND al.orderdate >= '2024-09-01'
                        AND al.orderdate < '2024-10-01'
                        GROUP BY month, al.campaign_name
                        ORDER BY roas DESC;
            2. question: Compare this month with previous basis on  facebook ads level performance. Analysis which is better ads worked and why?
               SQL Query: SELECT
                                date_trunc('month', al.orderdate) AS month,
                                SUM(al.purchase) AS total_purchases,
                                ROUND(SUM(al.spend),2) AS total_spend,
                                ROUND(SUM(spend) / NULLIF(SUM(purchase), 1), 2) AS cpa,
                                ROUND(SUM(al.purchase_value) / NULLIF(SUM(al.spend), 1), 2) AS roas,
                                ROUND(SUM(al.spend)* 1000.0 / NULLIF(SUM(al.impression), 1),2) AS cpm,
                                ROUND(SUM(al.spend) / NULLIF(SUM(al.clicks), 1),2) AS cpc,
                                ROUND(SUM(al.clicks) / NULLIF(SUM(al.impression), 1),2) AS ctr
                            FROM
                                horizon.ads_lastattribute al
                            WHERE
                                al.channel = 'facebook'
                                AND al.workspace = '854e249d718e42cba341aa0559931c12'
                                AND (al.orderdate >= DATE_TRUNC('month', CURRENT_DATE))
                                OR (al.orderdate >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month') AND al.orderdate < DATE_TRUNC('month', CURRENT_DATE))
                            GROUP BY month
                            ORDER BY month;

            SQL Query:"""

    def get_schema_info(self):
        """Fetch and format schema information"""
        query = """
        SELECT 
            t.table_name,
            array_agg(DISTINCT c.column_name || ' (' || c.data_type || ')') as columns
        FROM information_schema.tables t
        JOIN information_schema.columns c ON t.table_name = c.table_name
        WHERE t.table_schema = 'horizon'
        GROUP BY t.table_name;
        """
        
        schema_query = text(query)
        result = db.session.execute(schema_query)
        schema_data = result.fetchall()
        
        schema_str = "Available Tables:\n"
        for table, columns in schema_data:
            schema_str += f"\n{table}:\n"
            for col in columns:
                schema_str += f"  - {col}\n"
        
        return schema_str

    def create_query_chain(self, workspace):
        """Create the chain for query generation"""
        prompt = ChatPromptTemplate.from_template(self.get_query_template())
        
        chain = (
            RunnablePassthrough.assign(
                schema=lambda _: self.get_schema_info(),
                workspace=lambda _: workspace
            )
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        return chain

    def execute_query(self, query):
        """Execute the generated query"""
        try:
            data_query = text(query)
            result = db.session.execute(data_query)
            return result.fetchall()
        finally:
            pass

    def handle_question(self, question, workspace):
        """Handle both database and non-database questions"""
        classification = self.classify_question(question)
        
        if classification["needs_database"]:
            try:
                chain = self.create_query_chain(workspace)
                query = chain.invoke({"question": question})
                query = re.sub(r'```sql\s*|\s*```', '', query)
                results = self.execute_query(query)

                log = ChatBotLog(workspace=workspace, question = question, query=query, result=str(results))
                db.session.add(log)
                db.session.commit()

                data = [row_to_dict(row) for row in results]
                return jsonify_with_decimal(data)
            except Exception as e:
                log = ChatBotLog(workspace=workspace, question = question, query=query, result=str(e.args))
                db.session.add(log)
                db.session.commit()
        else:
            return jsonify({
                "type": "direct_response",
                "response": classification["response"],
                "reason": classification["reason"]
            })

# Flask route implementation
@chatbot_cd.route('/adperformance', methods=['POST', 'OPTIONS'])
@cross_origin(origins='*', methods=['POST', 'OPTIONS'], headers=['Content-Type'])
def chatwithsql():
    headers = request.headers
    openai_api_key = os.environ.get('_OPENAI_KEY_SQL')
    
    # Initialize handler
    handler = SmartQueryHandler(openai_api_key)
    
    userid = headers.get('workspaceId')
    user = UserRegister.query.filter_by(workspace=userid).first()
    body = json.loads(request.data)
    
    workspace = userid
    question = body.get('question')
    
    try:
        return handler.handle_question(question, workspace)
    except Exception as e:
        # return jsonify({"error": str(e)}), 500
        try:
            return handler.handle_question(question, workspace)
        except Exception as e:
            try:
                return handler.handle_question(question, workspace)
            except Exception as e:
                # return jsonify({"error": str(e)}), 500
                return jsonify({"error": "Error in processing Request"}), 500