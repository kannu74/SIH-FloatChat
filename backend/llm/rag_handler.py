import os
import json
import chromadb
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure the Gemini API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Database schema for the prompt context
DB_SCHEMA = """
Table Name: argo_measurements
Columns:
- float_id (VARCHAR), timestamp (TIMESTAMP), latitude (REAL), longitude (REAL)
- pressure (REAL) - Ocean depth., temperature (REAL) - In Celsius., salinity (REAL)
Table Name: argo_floats
Columns:
- float_id (VARCHAR, Unique), project_name (VARCHAR)
"""

def get_sql_from_question(question: str) -> dict:
    """
    Uses a RAG pipeline with Gemini to convert a natural language question
    into a JSON object containing a SQL query and a visualization suggestion.
    """
    try:
        prompt = f"""
        You are an expert PostgreSQL assistant for ARGO ocean data. Your task is to convert a user's question into a JSON object.
        This JSON object must contain two keys: "sql_query" and "visualization_type".

        - "sql_query": A valid PostgreSQL query based on the user's question and the provided schema.
        - "visualization_type": Your suggestion for the best way to visualize the data.
          Possible values are: "table", "line_chart", "map", "scatter_plot".

        --- CRITICAL PERFORMANCE RULE ---
        For any visualization query ("map", "line_chart", "scatter_plot"), you MUST add a "LIMIT 1500" to the end of the SQL query to avoid crashing the user's browser. Do not return more than 1500 data points for a plot.
        ---
        
        --- VISUALIZATION RULES ---
        - Any plot involving 'pressure' or 'depth' is ALWAYS a 'line_chart'.
        - Choose "map" if the user asks for float 'locations' or to 'plot on a map'. The query MUST include 'latitude', 'longitude', AND 'float_id'.
        - Choose "scatter_plot" ONLY if the user explicitly asks to compare 'temperature vs salinity' or for a 'T-S diagram'. The query must select temperature, salinity, and pressure.
        - Choose "table" for everything else (e.g., simple COUNT or AVG queries).
        ---

        - For "profile" requests on the "most recent measurement", use a subquery:
          SELECT temperature, pressure FROM argo_measurements WHERE timestamp = (SELECT MAX(timestamp) FROM argo_measurements);

        You must only output the raw JSON object and nothing else.

        Database Schema:
        {DB_SCHEMA}

        User Question: "{question}"

        JSON Output:
        """

        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        response_text = response.text.strip().replace("```json", "").replace("```", "")
        response_json = json.loads(response_text)
        
        print(f"DEBUG: LLM Response JSON -> {response_json}")
        return response_json

    except Exception as e:
        print(f"An error occurred in the RAG handler: {e}")
        return {
            "sql_query": "SELECT 'An error occurred. Please check the logs.';",
            "visualization_type": "table"
        }