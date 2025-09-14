import os
import pandas as pd
import numpy as np
import logging  # <-- Import the logging module
from flask import Flask, request, jsonify
from sqlalchemy import create_engine, text
from backend.llm.rag_handler import get_sql_from_question

# --- Configure logging ---
# This sets up a basic logger that prints debug-level messages with a timestamp.
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
# -------------------------

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
    if not engine:
        logging.error("API call failed because database connection is not available.")
        return jsonify({"error": "Database connection not available."}), 500

    data = request.get_json()
    if not data or 'question' not in data:
        logging.warning("Invalid request received: 'question' field is missing.")
        return jsonify({"error": "Invalid request. 'question' is required."}), 400

    question = data['question']
    
    llm_response = get_sql_from_question(question)
    sql_query = llm_response.get('sql_query')
    viz_type = llm_response.get('visualization_type', 'table')

    try:
        logging.debug(f"Executing SQL query: {sql_query}")
        with engine.connect() as connection:
            df = pd.read_sql(text(sql_query), connection)
        
        # Replace NaN with None (which becomes null in JSON)
        df = df.replace({np.nan: None})

        result = df.to_dict(orient='records')
        logging.info(f"Query successful. Found {len(result)} records.")
        
        return jsonify({
            "question": question,
            "sql_query": sql_query,
            "visualization": viz_type,
            "data": result
        })
    except Exception as e:
        # Using logging.error provides a more detailed traceback
        logging.error(f"AN ERROR OCCURRED while executing the SQL query: {sql_query}", exc_info=True)
        
        return jsonify({
            "error": "Failed to execute the generated SQL query.",
            "sql_query": sql_query,
            "details": str(e)
        }), 500

