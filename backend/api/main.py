import os
import pandas as pd
import numpy as np
import logging  # Using Python's standard logging module
from flask import Flask, request, jsonify
from sqlalchemy import create_engine, text
from backend.llm.rag_handler import handle_question

# Configure logging for structured output
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__, template_folder='../../templates', static_folder='../../static')

# --- Database Connection ---
try:
    db_url = (
        f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:"
        f"{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:"
        f"{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}?client_encoding=utf8"
    )
    engine = create_engine(db_url)
    logging.info("Successfully connected to PostgreSQL for API.")
except Exception as e:
    logging.error(f"Failed to connect to PostgreSQL for API: {e}", exc_info=True)
    engine = None

@app.route('/api/chat', methods=['POST'])
def chat_handler():
    data = request.get_json()
    if not data or 'question' not in data:
        logging.warning("Invalid request received: 'question' field is missing.")
        return jsonify({"error": "Invalid request."}), 400

    question = data.get('question')
    chat_history = data.get('chat_history', [])

    # Get the unified response from the new AI handler
    ai_response = handle_question(question, chat_history)
    response_type = ai_response.get('response_type')

    # If the AI decided it's a database query, execute it
    if response_type == 'database':
        sql_query = ai_response.get('sql_query')
        viz_type = ai_response.get('visualization_type', 'table')
        try:
            logging.debug(f"Executing SQL query: {sql_query}")
            with engine.connect() as connection:
                df = pd.read_sql(text(sql_query), connection)
            df = df.replace({np.nan: None})
            result = df.to_dict(orient='records')
            logging.info(f"Query successful. Found {len(result)} records.")
            return jsonify({ "data": result, "sql_query": sql_query, "visualization": viz_type })
        except Exception as e:
            logging.error(f"Error executing SQL query: {sql_query}", exc_info=True)
            return jsonify({ "error": "Failed to execute SQL query.", "details": str(e) }), 500
    
    # If it's a text response, just forward the answer
    elif response_type == 'text':
        return jsonify({ "data": ai_response.get('answer'), "visualization": "text" })
    
    # Fallback for any unexpected response types
    else:
        logging.warning(f"Received unexpected response type from AI: {response_type}")
        return jsonify({ "data": "Sorry, I received an unexpected response format.", "visualization": "text" })