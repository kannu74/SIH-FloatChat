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

    # This is a unified prompt that gives the model all instructions at once.
    prompt = f"""
    You are Orca AI, a friendly and expert AI assistant for ARGO ocean data.
    Your task is to analyze the user's latest question in the context of a conversation and respond in one of three ways:
    
    1.  **If the user asks a greeting or a simple conversational question** (like "hi", "who are you?", "thanks"):
        Respond with a friendly, conversational answer. The output MUST be a JSON object like this:
        {{"response_type": "text", "answer": "Hello! I am Orca AI. How can I help you with ARGO data?"}}

    2.  **If the user asks a general knowledge question** about oceanography or the ARGO program that CANNOT be answered by the database schema:
        Use your internal knowledge to answer. The output MUST be a JSON object like this:
        {{"response_type": "text", "answer": "An ARGO float is an autonomous profiling float that measures..."}}

    3.  **If the user asks a question that requires getting data from the database** (e.g., asking for a map, profile, count, or specific values):
        Generate a SQL query and a visualization type. The output MUST be a JSON object like this:
        {{"response_type": "database", "sql_query": "SELECT ...", "visualization_type": "map"}}

    --- RULES for Database Queries ---
    - For any visualization query ("map", "line_chart", "scatter_plot"), YOU MUST add a "LIMIT 1500" to the SQL query.
    - A 'map' query MUST select 'latitude', 'longitude', AND 'float_id'.
    - A 'line_chart' is ONLY for plots involving 'pressure' or 'depth'.
    - A 'scatter_plot' is ONLY for 'temperature vs salinity' or 'T-S diagram' requests.
    - Always respond with only the raw JSON object and nothing else.

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