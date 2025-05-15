from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough
from sqlalchemy import text
import sqlparse

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
        self.llm = ChatOpenAI(openai_api_key=openai_api_key, model="gpt-4o-mini", temperature=0.1, top_p=0.7, frequency_penalty=0.2, presence_penalty=0)
        
        # Updated system template to classify question type based on context
        self.classifier_template = """
        You are a query classifier that determines:
        1. Whether the question is a sequential follow-up to previous questions.
        2. If not sequential, whether the question requires database access.
        
        Considerations for sequential classification:
        - It logically follows from one of the previous questions..
        - It references a concept, term, or request from previous questions.
        - It asks for additional information, visualization, or formatting based on prior results.
        
        Considerations for database access:
        - It asks for historical, numerical, or trend-based performance data.
        - It requires an analysis of past metrics (e.g., CPA trends, ROAS shifts, best-performing campaigns).
        - The question asks for data-driven insights or recommendations.  This includes questions about optimization, scaling, or strategy that necessitate looking at past performance.

        Questions that don't need database access:
        1. Purely theoretical or conceptual questions that do not require specific data to answer.
        2. Greetings or casual conversation
        3. Requests for formatting, visualization, or restructuring of previously retrieved data

        
        Question: {question}
        Previous Questions: {prev_questions}
        
        Respond in the following JSON format:
        {{
            "is_sequential": boolean,
            "reason": "Brief explanation of classification",
            "needs_database": boolean,
            "response": "No answer if no database needed, otherwise null"
        }}

        """

    def classify_question(self, question, prev_questions=None):
        """Determine if the question is sequential or needs database access."""
        prev_questions_str = " | ".join(prev_questions) if prev_questions else "None"
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(self.classifier_template)
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        
        result = chain.invoke({"question": question, "prev_questions": prev_questions_str})
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {
                "is_sequential": False,
                "needs_database": True,
                "reason": "Classification failed, defaulting to database query",
                "response": None
            }



    def get_query_template(self):
        return """You are an advanced Postgres SQL Query Generator specialized in Performance Marketing Analytics, with expertise in:
            - PostgreSQL query optimization
            - Marketing metrics calculation
            - Campaign performance evaluation
            - Marketing data analysis

            Purpose of this Step
            The SQL query you generate will be used as input for a data interpretation assistant in Step 2. Ensure that:
            - The query retrieves all necessary performance metrics (CPA, ROAS, CTR, CPM, CR, AOV etc) for detailed analysis.
            - Data is structured to enable insights into performance trends, comparisons, and key observations.
            - If the user asks for a comparison (MoM, WoW) or segmentation, include the required breakdown with sufficient granularity.

                    
            Schema Information:
            {schema}
            
            Question: {question}
            
            
            Step 1: Understanding the Query
            Before generating the Postgres SQL query:
            1. Identify the user's intent:
            - Is it about account performance, ad performance, campaign trends, or conversion insights?
            - Does it require trend analysis, forecasting, or segmentation?
            
            2. Extract essential details:
            - Time period (last 3 days, last 7 days, WoW, or all available data).
            - Metrics mentioned or inferred (CPA, ROAS, CTR, CR, AOV, CPC, CPM, etc.).
            - Requested breakdowns (by campaign, ad set, ad type, creative type).
            - Comparison logic (current period vs. previous period, winning vs. losing ads).

            3. Determine table relationships:
            - For ad platform data, join `horizon.ads`.
            - For first-click attribution, join `horizon.ads_firstattribute`.
            - For conversion and ad spend focus, primarily use `horizon.ads_lastattribute`.



            Step 2: Constructing the Query
            1. Select primary tables based on query type:
            - Ad performance: Use `horizon.ads_lastattribute` (final conversions & spend).
            - First-touch attribution analysis: Use `horizon.ads_firstattribute`.

            2. Extract relevant metrics (based on direct request & inferred insights):
            - Primary metrics: ROAS, CPA, CTR, CPC, AOV, Impression, CR.
            - New customer insights: New orders (nOrders), new revenue (nROAS, nAOV, nCR).
            - Engagement indicators: Fresh visitor % (fresh_visitor / click), video vs. image ad type performance.
            - Granular breakdowns: Campaign name, ad set ID, ad ID, creative type (video/image).

            3. Enhance analysis with additional insights:
            - Account-level: Spend vs. revenue trends, impression & click volatility, channel mix.
            - Campaign-level: MoM/WoW comparisons, top/bottom performers by ROAS or CPA.
            - Adset/Ad-level: CTR vs. CR trends, ad fatigue indicators (e.g., declining CTR over time), creative metadata

            4. Optimize SQL query for efficiency:
            - Use workspace and time filters (default to last 7 days if unspecified).
            - Apply date truncation (`date_trunc('month', orderdate)`) for grouping.
            - Prevent division errors with `NULLIF(, 0)` and SUM null with `COALESCE(,0)`.
            - Use subqueries/CTEs for complex logic readability
            - Include raw data (e.g., clicks, impressions) alongside calculated metrics.
            - Double cross verigy syntax of query.
            - Give Perference to 'name' field over 'id' like adset_name or adsetid


            Step 3: Generating the Final SQL Query
            - The query should strictly return only SQL, without explanations.
            - Ensure joins, groupings, and aggregations align with analysis objectives.
            - Use consistent schema prefix (`horizon.`) for all tables.
            - Always include `workspace = '{workspace}'` in the `WHERE` clause     

            Example 1: Facebook Campaign Analysis for ROAS Improvement
            Question: Can you analyze the performance of the ad '080125-1M3-VID14-C-LEM-C1' over the last 7 days? Identify any anomalies, provide actionable recommendations, suggest budget strategies if relevant, and forecast potential performance trends based on recent data.
            SQL Query: WITH al_agg AS (
                        SELECT
                            al.adid,
                            al.dated,
                            SUM(COALESCE(al.revenue, 0)) AS revenue,
                            SUM(COALESCE(al.spend, 0)) AS spend,
                            SUM(COALESCE(al.orders, 0)) AS orders,
                            SUM(COALESCE(al.new_revenue, 0)) AS new_revenue,
                            SUM(COALESCE(al.new_order, 0)) AS new_order,
                            SUM(COALESCE(al.fresh_visitor, 0)) AS fresh_visitor,
                            SUM(COALESCE(al.engagement, 0)) AS engagement,
                            SUM(COALESCE(al.video_view_3s, 0)) AS video_view_3s,
                            SUM(COALESCE(al.video_p25_watched_actions, 0)) AS video_watched_actions_25percent,
                            SUM(COALESCE(al.video_p50_watched_actions, 0)) AS video_watched_actions_50percent,
                            SUM(COALESCE(al.video_p100_watched_actions, 0)) AS video_watched_actions_100percent
                        FROM horizon.ads_lastattribute al
                         WHERE al.ad_name = '080125-1M3-VID14-C-LEM-C1'
                        AND al.dated >= CURRENT_DATE - INTERVAL '7 days'
                        AND al.workspace = '854e249d718e42cba341aa0559931c12
                        GROUP BY 1, 2
                    )
                    SELECT
                        ads.dated AS date,
                        ads.ad_name AS ad_name,
                        COALESCE(ads.ad_type, 'NA') AS ad_type,
                        COALESCE(ads.ad_copy, 'NA') AS ad_copy,
                        SUM(COALESCE(al.revenue,0)) AS total_revenue,
                        SUM(COALESCE(ads.spend,0)) AS total_spend,
                        ROUND(SUM(COALESCE(al.revenue,0)) / NULLIF(SUM(ads.spend), 0), 2) AS roas,
                        ROUND(SUM(COALESCE(al.revenue,0)) / NULLIF(SUM(COALESCE(al.orders,0)), 0), 2) AS cpa,
                        ROUND(SUM(ads.spend) / NULLIF(SUM(ads.clicks), 0), 2) AS cpc,
                        ROUND(SUM(ads.clicks)*100 / NULLIF(SUM(ads.impression), 0), 2) AS ctr,
                        ROUND(SUM(COALESCE(al.new_revenue,0)) / NULLIF(SUM(ads.spend), 0), 2) AS nroas,
                        ROUND(SUM(COALESCE(al.orders,0))*100 / NULLIF(SUM(ads.clicks), 0), 2) AS cr,
                        SUM(COALESCE(al.orders,0)) AS total_orders,
                        SUM(COALESCE(al.new_order,0)) AS new_order,
                        SUM(COALESCE(al.fresh_visitor,0)) AS fresh_visitor,
                        SUM(COALESCE(al.engagement,0)) AS creative_engagement,
                        SUM(COALESCE(al.video_view_3s,0)) AS video_view_3s,
                        SUM(COALESCE(al.video_watched_actions_25percent,0)) AS video_watched_actions_25percent,
                        SUM(COALESCE(al.video_watched_actions_50percent,0)) AS video_watched_actions_50percent,
                        SUM(COALESCE(al.video_watched_actions_100percent,0)) AS video_watched_actions_100percent
                    from
                        horizon.ads ads 
                        left join al_agg  al on COALESCE(ads.adid, ads.campaignid) = al.adid and ads.dated = al.dated  
                    WHERE
                        ads.ad_name = '080125-1M3-VID14-C-LEM-C1'
                        AND ads.dated >= CURRENT_DATE - INTERVAL '7 days'
                        AND ads.workspace = '854e249d718e42cba341aa0559931c12'
                    GROUP BY
                        1,2,3,4
                    ORDER BY
                        ads.dated;

            Example 2: Month-over-Month Facebook Ads Performance Comparison
            Question: How is my account performing?
            SQL Query:  WITH al_agg AS (
                            SELECT
                                date_trunc('month', al.orderdate) AS month,
                                al.adid,
                                al.campaign_name,
                                SUM(COALESCE(al.revenue, 0)) AS revenue,
                                SUM(COALESCE(al.spend, 0)) AS spend,
                                SUM(COALESCE(al.orders, 0)) AS orders,
                                SUM(COALESCE(al.new_revenue, 0)) AS new_revenue,
                                SUM(COALESCE(al.new_order, 0)) AS new_order,
                                SUM(COALESCE(al.fresh_visitor, 0)) AS fresh_visitor
                            FROM horizon.ads_lastattribute al
                            WHERE
                                LOWER(al.channel) = 'facebook'
                                AND al.workspace = '854e249d718e42cba341aa0559931c12'
                                AND al.orderdate >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '60 days')
                            GROUP BY 1, 2, 3
                        ),

                        ads_agg AS (
                            SELECT
                                date_trunc('month', ads.dated) AS month,
                                COALESCE(ads.adid, ads.campaignid) AS adid,
                                SUM(ads.spend) AS spend,
                                SUM(ads.impression) AS impressions,
                                SUM(ads.clicks) AS clicks
                            FROM horizon.ads ads
                            GROUP BY 1, 2
                        )
                        SELECT
                            al.month,
                            al.campaign_name,
                            SUM(al.revenue) AS total_revenue,
                            SUM(a.spend) AS total_spend,
                            SUM(al.orders) AS total_orders,
                            ROUND(SUM(COALESCE(a.spend, 0)) * 1000.0 / NULLIF(SUM(a.impressions), 0), 2) AS cpm,
                            ROUND(SUM(COALESCE(a.clicks, 0)) * 100.0 / NULLIF(SUM(a.impressions), 0), 2) AS ctr,
                            ROUND(SUM(al.revenue) / NULLIF(SUM(a.spend), 0), 2) AS roas,
                            ROUND(SUM(al.new_revenue) / NULLIF(SUM(a.spend), 0), 2) AS nroas,
                            SUM(al.new_orders) AS new_total_order,
                            SUM(al.fresh_visitors) AS fresh_visitor
                        FROM ads_agg a
                        LEFT JOIN al_agg al ON al.adid = a.adid AND al.month = a.month
                        GROUP BY al.month, al.campaign_name
                        ORDER BY roas DESC;

            SQL Query:"""



    def get_schema_info(self):
        """Fetch and format schema information"""
        query = """
        SELECT 
            t.table_name,
            array_agg(DISTINCT c.column_name || ' (' || c.data_type || ')') as columns
        FROM information_schema.tables t
        JOIN information_schema.columns c ON t.table_name = c.table_name
        WHERE t.table_schema = 'horizon' AND t.table_name <> 'ads'
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

        def __init__(self):
            self.counter = 0 

        def validate_query(query):
            try:
                parsed = sqlparse.parse(query)
                if not parsed:
                    return False, "Invalid SQL syntax"
                # Add more checks (e.g., field validation against schema)
                return True, None
            except Exception as e:
                return False, str(e)
        
        def validate_and_clean(output):
            query = re.sub(r'```sql\s*|\s*```', '', output)
            is_valid, error = validate_query(query)  # Assume validate_query is defined
            if not is_valid and self.counter < 3:
                self.counter += 1
                self.create_query_chain(workspace)
            return query
        
        chain = (
            RunnablePassthrough.assign(
                schema=lambda _: self.get_schema_info(),
                workspace=lambda _: workspace
            )
            | prompt
            | self.llm
            | StrOutputParser()
            | validate_and_clean
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

    def handle_question(self, question, workspace, prev_question):
        """Handle both database and non-database questions"""
        classification = self.classify_question(question, prev_question)
        
        if classification["needs_database"]:
            chain = self.create_query_chain(workspace)
            query = chain.invoke({"question": question})
            results = self.execute_query(query)

            log = ChatBotLog(workspace=workspace, question = question, query=query, result=str(results))
            db.session.add(log)
            db.session.commit()

            data = [row_to_dict(row) for row in results]
            return jsonify_with_decimal({"data": data, "is_sequential": classification['is_sequential']})
        else:
            return jsonify({
                "type": "direct_response",
                "response": classification["response"],
                "reason": classification["reason"],
                "is_sequential": classification['is_sequential']
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
    prev_question = body.get('prevQuestions')
    
    try:
        return handler.handle_question(question, workspace, prev_question)
    except Exception as e:
        return jsonify({"error": "Error in processing Request"}), 500
        # try:
        #     return handler.handle_question(question, workspace, prev_question)
        # except Exception as e:
        #     try:
        #         return handler.handle_question(question, workspace, prev_question)
        #     except Exception as e:
        #         # return jsonify({"error": str(e)}), 500
        #         return jsonify({"error": "Error in processing Request"}), 500