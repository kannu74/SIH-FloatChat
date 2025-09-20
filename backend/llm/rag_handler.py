import os
import json
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Configure the Gemini API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

DB_SCHEMA = """
Table Name: argo_measurements (stores individual sensor readings)
Columns:
- float_id (VARCHAR), timestamp (TIMESTAMP), latitude (REAL), longitude (REAL)
- pressure (REAL) - Ocean depth., temperature (REAL) - In Celsius., salinity (REAL)
Table Name: argo_floats (stores metadata for each float)
Columns:
- float_id (VARCHAR, Unique), project_name (VARCHAR)
"""

def handle_question(question: str, chat_history: list) -> dict:
    """
    Handles all user questions with a single, powerful LLM call.
    The model decides whether to query the database, answer from knowledge, or give a greeting.
    """
    formatted_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history])

    # This prompt is updated with instructions for the new chart types
    prompt = f"""
    You are Orca AI, a friendly and expert AI assistant for ARGO ocean data.
    Your task is to analyze the user's latest question and respond with a JSON object.
    
    1.  **If the user asks a greeting or simple conversational question**:
        The JSON output must be: {{"response_type": "text", "answer": "Hello! I am Orca AI. How can I help?"}}

    2.  **If the user asks a general knowledge question**:
        The JSON output must be: {{"response_type": "text", "answer": "An ARGO float is..."}}

    3.  **If the user asks for data from the database**:
        The JSON output must be: {{"response_type": "database", "sql_query": "SELECT ...", "visualization_type": "..."}}

    --- RULES for Database Queries ---
    - Possible visualization types are: "table", "map", "line_chart", "scatter_plot", "bar_chart", "histogram", "time_series".
    - A 'map' query MUST select 'latitude', 'longitude', AND 'float_id'. LIMIT to 1500 points.
    - A 'line_chart' is ONLY for plots involving 'pressure' or 'depth'. LIMIT to 1500 points.
    - A 'scatter_plot' is ONLY for 'temperature vs salinity' requests and MUST select temperature, salinity, AND pressure. LIMIT to 1500 points.
    - A 'bar_chart' is for comparing counts across categories (e.g., 'count of floats per project').
    - A 'histogram' is for showing the 'distribution' of a single variable. LIMIT to 5000 points.
    - A 'time_series' is for tracking a variable 'over time' for a specific float_id. The SQL query MUST select 'timestamp' and the requested variable.
    - Always respond with only the raw JSON object.

    --- CONVERSATION HISTORY ---
    {formatted_history}
    ---
    
    DATABASE SCHEMA:
    {DB_SCHEMA}
    ---

    LATEST USER QUESTION: "{question}"

    JSON RESPONSE:
    """
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        }
        response = model.generate_content(prompt, safety_settings=safety_settings)

        response_text = response.text.strip().replace("```json", "").replace("```", "")
        if not response_text:
            raise ValueError("Model returned an empty response.")
            
        print(f"DEBUG: Raw LLM Response -> {response_text}")
        response_json = json.loads(response_text)
        return response_json

    except Exception as e:
        print(f"An error occurred in the RAG handler: {e}")
        return {
            "response_type": "text",
            "answer": "I'm sorry, I encountered an issue processing your request. Please try rephrasing."
        }

