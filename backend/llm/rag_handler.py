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
- float_id (VARCHAR)
- timestamp (TIMESTAMP)
- latitude (REAL)
- longitude (REAL)
- pressure (REAL) - Ocean depth in decibars.
- temperature (REAL) - In Celsius.
- salinity (REAL)

Table Name: argo_floats
Columns:
- float_id (VARCHAR, Unique)
- project_name (VARCHAR)
"""

def get_sql_from_question(question: str) -> dict:
    """
    Uses a RAG pipeline with Gemini to convert a natural language question 
    into a JSON object containing a SQL query and a visualization suggestion.
    """
    try:
        # This new prompt instructs the LLM to return a structured JSON response
        prompt = f"""
        You are an expert PostgreSQL assistant for ARGO ocean data. Your task is to convert a user's question into a JSON object.
        This JSON object must contain two keys: "sql_query" and "visualization_type".

        - "sql_query": A valid PostgreSQL query based on the user's question and the provided schema.
        - "visualization_type": Your suggestion for the best way to visualize the data. 
          Possible values are: "table", "line_chart", "map".

        - Choose "line_chart" for data showing a profile or trend, like temperature vs. pressure (depth). The y-axis should be pressure and inverted to show depth.
        - Choose "map" if the user asks for float locations or trajectories.
        - Choose "table" for everything else, like listing names or simple values.
        
        You must only output the raw JSON object and nothing else. Do not include markdown formatting like ```json.

        Database Schema:
        {DB_SCHEMA}

        User Question: "{question}"

        JSON Output:
        """

        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        # Clean up and parse the JSON response from the LLM
        response_text = response.text.strip()
        response_json = json.loads(response_text)
        
        print(f"DEBUG: LLM Response JSON -> {response_json}")
        return response_json

    except Exception as e:
        print(f"An error occurred in the RAG handler: {e}")
        return {
            "sql_query": "SELECT 'An error occurred. Please check the logs.';",
            "visualization_type": "table"
        }